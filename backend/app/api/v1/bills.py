from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.ap import Bill, BillLine, BillStatus
from app.models.accounting import Account
from app.schemas.ap import BillCreate, BillUpdate, BillResponse

router = APIRouter()


def get_next_bill_number(db: Session) -> str:
    result = db.execute(select(func.count(Bill.id)))
    count = result.scalar() or 0
    return f"BILL-{count + 1:06d}"


def get_default_expense_account(db: Session) -> int:
    """Get a default expense account for bill lines"""
    # Try to find an expense account (typically starts with 5 or 6)
    result = db.execute(
        select(Account).where(Account.code.like("5%")).where(Account.is_active == True).limit(1)
    )
    account = result.scalar_one_or_none()
    if account:
        return account.id
    # Try 6xxx accounts
    result = db.execute(
        select(Account).where(Account.code.like("6%")).where(Account.is_active == True).limit(1)
    )
    account = result.scalar_one_or_none()
    if account:
        return account.id
    # Fallback to any active account
    result = db.execute(select(Account).where(Account.is_active == True).limit(1))
    account = result.scalar_one_or_none()
    if account:
        return account.id
    raise HTTPException(status_code=400, detail="No accounts found. Please create accounts first.")


@router.get("", response_model=List[BillResponse])
def list_bills(
    status: Optional[BillStatus] = None,
    vendor_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(Bill)

    if status:
        query = query.where(Bill.status == status)
    if vendor_id:
        query = query.where(Bill.vendor_id == vendor_id)
    if start_date:
        query = query.where(Bill.bill_date >= start_date)
    if end_date:
        query = query.where(Bill.bill_date <= end_date)

    query = query.order_by(Bill.bill_date.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("", response_model=BillResponse)
def create_bill(
    data: BillCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    bill_number = get_next_bill_number(db)

    subtotal = Decimal("0")
    tax_amount = Decimal("0")
    discount_amount = Decimal("0")

    bill = Bill(
        bill_number=bill_number,
        vendor_bill_number=data.vendor_bill_number,
        vendor_id=data.vendor_id,
        bill_date=data.bill_date,
        due_date=data.due_date,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        reference=data.reference,
        notes=data.notes,
        purchase_order_id=data.purchase_order_id,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    # Get default account if needed
    default_account_id = None

    for line_data in data.lines:
        line_subtotal = line_data.quantity * line_data.unit_price
        line_discount = line_subtotal * (line_data.discount_percent / 100)
        line_after_discount = line_subtotal - line_discount
        line_tax = line_after_discount * (line_data.tax_percent / 100)
        line_total = line_after_discount + line_tax

        # Use provided account_id or get default
        account_id = line_data.account_id
        if account_id is None:
            if default_account_id is None:
                default_account_id = get_default_expense_account(db)
            account_id = default_account_id

        line = BillLine(
            product_id=line_data.product_id,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            discount_percent=line_data.discount_percent,
            tax_percent=line_data.tax_percent,
            line_total=line_total,
            account_id=account_id
        )
        bill.lines.append(line)

        subtotal += line_subtotal
        discount_amount += line_discount
        tax_amount += line_tax

    bill.subtotal = subtotal
    bill.discount_amount = discount_amount
    bill.tax_amount = tax_amount
    bill.total = subtotal - discount_amount + tax_amount
    bill.balance_due = bill.total

    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@router.get("/{bill_id}", response_model=BillResponse)
def get_bill(
    bill_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Bill).where(Bill.id == bill_id))
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


@router.patch("/{bill_id}", response_model=BillResponse)
def update_bill(
    bill_id: int,
    data: BillUpdate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Bill).where(Bill.id == bill_id))
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    if bill.status not in [BillStatus.draft]:
        raise HTTPException(
            status_code=400,
            detail="Only draft bills can be modified"
        )

    if data.lines is not None:
        for line in bill.lines:
            db.delete(line)

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        discount_amount = Decimal("0")

        for line_data in data.lines:
            line_subtotal = line_data.quantity * line_data.unit_price
            line_discount = line_subtotal * (line_data.discount_percent / 100)
            line_after_discount = line_subtotal - line_discount
            line_tax = line_after_discount * (line_data.tax_percent / 100)
            line_total = line_after_discount + line_tax

            line = BillLine(
                bill_id=bill.id,
                product_id=line_data.product_id,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                discount_percent=line_data.discount_percent,
                tax_percent=line_data.tax_percent,
                line_total=line_total,
                account_id=line_data.account_id
            )
            db.add(line)

            subtotal += line_subtotal
            discount_amount += line_discount
            tax_amount += line_tax

        bill.subtotal = subtotal
        bill.discount_amount = discount_amount
        bill.tax_amount = tax_amount
        bill.total = subtotal - discount_amount + tax_amount
        bill.balance_due = bill.total - bill.amount_paid

    update_data = data.dict(exclude_unset=True, exclude={"lines"})
    for field, value in update_data.items():
        setattr(bill, field, value)

    bill.updated_by_id = current_user.id
    db.commit()
    db.refresh(bill)
    return bill


@router.post("/{bill_id}/receive", response_model=BillResponse)
def receive_bill(
    bill_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Bill).where(Bill.id == bill_id))
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    if bill.status != BillStatus.draft:
        raise HTTPException(status_code=400, detail="Only draft bills can be received")

    bill.status = BillStatus.received
    bill.updated_by_id = current_user.id
    db.commit()
    db.refresh(bill)
    return bill


@router.post("/{bill_id}/void", response_model=BillResponse)
def void_bill(
    bill_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Bill).where(Bill.id == bill_id))
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    if bill.amount_paid > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot void bill with payments applied"
        )

    bill.status = BillStatus.void
    bill.updated_by_id = current_user.id
    db.commit()
    db.refresh(bill)
    return bill
