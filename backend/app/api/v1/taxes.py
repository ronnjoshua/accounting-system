from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.ar import Invoice, InvoiceStatus
from app.models.ap import Bill, BillStatus
from app.models.tax import TaxRate, TaxExemption, TaxPeriod, TaxType
from app.schemas.tax import (
    TaxRateCreate, TaxRateUpdate, TaxRateResponse,
    TaxExemptionCreate, TaxExemptionResponse,
    TaxPeriodCreate, TaxPeriodResponse,
    TaxSummaryReport
)

router = APIRouter()


# ============== Tax Rates ==============

@router.get("/rates", response_model=List[TaxRateResponse])
def list_tax_rates(
    tax_type: Optional[TaxType] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(TaxRate)

    if tax_type:
        query = query.where(TaxRate.tax_type == tax_type)
    if is_active is not None:
        query = query.where(TaxRate.is_active == is_active)

    query = query.order_by(TaxRate.code).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("/rates", response_model=TaxRateResponse)
def create_tax_rate(
    data: TaxRateCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    # Check for duplicate code
    existing = db.execute(select(TaxRate).where(TaxRate.code == data.code)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Tax rate with this code already exists")

    tax_rate = TaxRate(
        code=data.code,
        name=data.name,
        description=data.description,
        tax_type=data.tax_type,
        rate=data.rate,
        tax_collected_account_id=data.tax_collected_account_id,
        tax_paid_account_id=data.tax_paid_account_id,
        country=data.country,
        state=data.state,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
        is_compound=data.is_compound,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(tax_rate)
    db.commit()
    db.refresh(tax_rate)
    return tax_rate


@router.get("/rates/{rate_id}", response_model=TaxRateResponse)
def get_tax_rate(
    rate_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(TaxRate).where(TaxRate.id == rate_id))
    tax_rate = result.scalar_one_or_none()
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    return tax_rate


@router.patch("/rates/{rate_id}", response_model=TaxRateResponse)
def update_tax_rate(
    rate_id: int,
    data: TaxRateUpdate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    tax_rate = db.execute(select(TaxRate).where(TaxRate.id == rate_id)).scalar_one_or_none()
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tax_rate, field, value)

    tax_rate.updated_by_id = current_user.id
    db.commit()
    db.refresh(tax_rate)
    return tax_rate


# ============== Tax Exemptions ==============

@router.get("/exemptions", response_model=List[TaxExemptionResponse])
def list_tax_exemptions(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(TaxExemption)

    if entity_type:
        query = query.where(TaxExemption.entity_type == entity_type)
    if entity_id:
        query = query.where(TaxExemption.entity_id == entity_id)
    if is_active is not None:
        query = query.where(TaxExemption.is_active == is_active)

    query = query.order_by(TaxExemption.effective_from.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("/exemptions", response_model=TaxExemptionResponse)
def create_tax_exemption(
    data: TaxExemptionCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    exemption = TaxExemption(
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        certificate_number=data.certificate_number,
        exemption_reason=data.exemption_reason,
        tax_rate_id=data.tax_rate_id,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
        notes=data.notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(exemption)
    db.commit()
    db.refresh(exemption)
    return exemption


# ============== Tax Periods ==============

@router.get("/periods", response_model=List[TaxPeriodResponse])
def list_tax_periods(
    tax_type: Optional[TaxType] = None,
    is_filed: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(TaxPeriod)

    if tax_type:
        query = query.where(TaxPeriod.tax_type == tax_type)
    if is_filed is not None:
        query = query.where(TaxPeriod.is_filed == is_filed)

    query = query.order_by(TaxPeriod.period_end.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("/periods", response_model=TaxPeriodResponse)
def create_tax_period(
    data: TaxPeriodCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    period = TaxPeriod(
        name=data.name,
        tax_type=data.tax_type,
        period_start=data.period_start,
        period_end=data.period_end,
        due_date=data.due_date,
        notes=data.notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(period)
    db.commit()
    db.refresh(period)
    return period


@router.post("/periods/{period_id}/calculate", response_model=TaxPeriodResponse)
def calculate_tax_period(
    period_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    """Calculate tax collected and paid for a period"""
    period = db.execute(select(TaxPeriod).where(TaxPeriod.id == period_id)).scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Tax period not found")

    # Calculate tax collected from invoices
    result = db.execute(
        select(func.sum(Invoice.tax_amount))
        .where(and_(
            Invoice.invoice_date >= period.period_start,
            Invoice.invoice_date <= period.period_end,
            Invoice.status.notin_([InvoiceStatus.DRAFT, InvoiceStatus.VOID])
        ))
    )
    period.tax_collected = result.scalar() or Decimal("0")

    # Calculate tax paid from bills
    result = db.execute(
        select(func.sum(Bill.tax_amount))
        .where(and_(
            Bill.bill_date >= period.period_start,
            Bill.bill_date <= period.period_end,
            Bill.status.notin_([BillStatus.DRAFT, BillStatus.VOID])
        ))
    )
    period.tax_paid = result.scalar() or Decimal("0")

    period.net_tax_due = period.tax_collected - period.tax_paid

    db.commit()
    db.refresh(period)
    return period


@router.post("/periods/{period_id}/file", response_model=TaxPeriodResponse)
def file_tax_period(
    period_id: int,
    payment_reference: Optional[str] = None,
    payment_date: Optional[date] = None,
    payment_amount: Optional[Decimal] = None,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    """Mark a tax period as filed"""
    period = db.execute(select(TaxPeriod).where(TaxPeriod.id == period_id)).scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Tax period not found")

    if period.is_filed:
        raise HTTPException(status_code=400, detail="Tax period is already filed")

    period.is_filed = True
    period.filed_at = datetime.utcnow()
    period.filed_by_id = current_user.id

    if payment_reference:
        period.payment_reference = payment_reference
    if payment_date:
        period.payment_date = payment_date
    if payment_amount:
        period.payment_amount = payment_amount

    db.commit()
    db.refresh(period)
    return period


# ============== Tax Reports ==============

@router.get("/summary", response_model=TaxSummaryReport)
def get_tax_summary(
    start_date: date,
    end_date: date,
    tax_type: Optional[TaxType] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get tax summary for a date range"""
    # Tax collected from invoices
    invoice_query = select(func.sum(Invoice.tax_amount)).where(and_(
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date,
        Invoice.status.notin_([InvoiceStatus.DRAFT, InvoiceStatus.VOID])
    ))
    tax_collected = db.execute(invoice_query).scalar() or Decimal("0")

    # Tax paid on bills
    bill_query = select(func.sum(Bill.tax_amount)).where(and_(
        Bill.bill_date >= start_date,
        Bill.bill_date <= end_date,
        Bill.status.notin_([BillStatus.DRAFT, BillStatus.VOID])
    ))
    tax_paid = db.execute(bill_query).scalar() or Decimal("0")

    # Count of taxable transactions
    invoice_count = db.execute(
        select(func.count(Invoice.id)).where(and_(
            Invoice.invoice_date >= start_date,
            Invoice.invoice_date <= end_date,
            Invoice.tax_amount > 0,
            Invoice.status.notin_([InvoiceStatus.DRAFT, InvoiceStatus.VOID])
        ))
    ).scalar() or 0

    bill_count = db.execute(
        select(func.count(Bill.id)).where(and_(
            Bill.bill_date >= start_date,
            Bill.bill_date <= end_date,
            Bill.tax_amount > 0,
            Bill.status.notin_([BillStatus.DRAFT, BillStatus.VOID])
        ))
    ).scalar() or 0

    return {
        "start_date": start_date,
        "end_date": end_date,
        "tax_collected": tax_collected,
        "tax_paid": tax_paid,
        "net_tax_liability": tax_collected - tax_paid,
        "taxable_sales_count": invoice_count,
        "taxable_purchases_count": bill_count
    }
