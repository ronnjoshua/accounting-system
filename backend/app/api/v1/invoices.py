from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.ar import Invoice, InvoiceLine, InvoiceStatus
from app.models.accounting import Account
from app.schemas.ar import InvoiceCreate, InvoiceUpdate, InvoiceResponse

router = APIRouter()


def get_default_revenue_account(db: Session) -> int:
    """Get a default revenue account for invoice lines"""
    # Try to find a Sales Revenue account
    result = db.execute(
        select(Account).where(Account.code.like("4%")).where(Account.is_active == True).limit(1)
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


def get_next_invoice_number(db: Session) -> str:
    result = db.execute(select(func.count(Invoice.id)))
    count = result.scalar() or 0
    return f"INV-{count + 1:06d}"


def calculate_line_total(line_data) -> Decimal:
    subtotal = line_data.quantity * line_data.unit_price
    discount = subtotal * (line_data.discount_percent / 100)
    after_discount = subtotal - discount
    tax = after_discount * (line_data.tax_percent / 100)
    return after_discount + tax


@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    status: Optional[InvoiceStatus] = None,
    customer_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(Invoice)

    if status:
        query = query.where(Invoice.status == status)
    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)
    if start_date:
        query = query.where(Invoice.invoice_date >= start_date)
    if end_date:
        query = query.where(Invoice.invoice_date <= end_date)

    query = query.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("", response_model=InvoiceResponse)
def create_invoice(
    data: InvoiceCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    invoice_number = get_next_invoice_number(db)

    subtotal = Decimal("0")
    tax_amount = Decimal("0")
    discount_amount = Decimal("0")

    invoice = Invoice(
        invoice_number=invoice_number,
        customer_id=data.customer_id,
        invoice_date=data.invoice_date,
        due_date=data.due_date,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        reference=data.reference,
        notes=data.notes,
        terms=data.terms,
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
                default_account_id = get_default_revenue_account(db)
            account_id = default_account_id

        line = InvoiceLine(
            product_id=line_data.product_id,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            discount_percent=line_data.discount_percent,
            tax_percent=line_data.tax_percent,
            line_total=line_total,
            account_id=account_id
        )
        invoice.lines.append(line)

        subtotal += line_subtotal
        discount_amount += line_discount
        tax_amount += line_tax

    invoice.subtotal = subtotal
    invoice.discount_amount = discount_amount
    invoice.tax_amount = tax_amount
    invoice.total = subtotal - discount_amount + tax_amount
    invoice.balance_due = invoice.total

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status not in [InvoiceStatus.draft]:
        raise HTTPException(
            status_code=400,
            detail="Only draft invoices can be modified"
        )

    if data.lines is not None:
        for line in invoice.lines:
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

            line = InvoiceLine(
                invoice_id=invoice.id,
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

        invoice.subtotal = subtotal
        invoice.discount_amount = discount_amount
        invoice.tax_amount = tax_amount
        invoice.total = subtotal - discount_amount + tax_amount
        invoice.balance_due = invoice.total - invoice.amount_paid

    update_data = data.dict(exclude_unset=True, exclude={"lines"})
    for field, value in update_data.items():
        setattr(invoice, field, value)

    invoice.updated_by_id = current_user.id
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
def send_invoice(
    invoice_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status != InvoiceStatus.draft:
        raise HTTPException(status_code=400, detail="Only draft invoices can be sent")

    invoice.status = InvoiceStatus.sent
    invoice.updated_by_id = current_user.id
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/void", response_model=InvoiceResponse)
def void_invoice(
    invoice_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.amount_paid > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot void invoice with payments applied"
        )

    invoice.status = InvoiceStatus.void
    invoice.updated_by_id = current_user.id
    db.commit()
    db.refresh(invoice)
    return invoice
