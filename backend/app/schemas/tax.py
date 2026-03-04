from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.tax import TaxType


class TaxRateCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    tax_type: TaxType
    rate: Decimal
    tax_collected_account_id: Optional[int] = None
    tax_paid_account_id: Optional[int] = None
    country: Optional[str] = None
    state: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_compound: bool = False


class TaxRateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rate: Optional[Decimal] = None
    tax_collected_account_id: Optional[int] = None
    tax_paid_account_id: Optional[int] = None
    country: Optional[str] = None
    state: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None
    is_compound: Optional[bool] = None


class TaxRateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: Optional[str] = None
    tax_type: TaxType
    rate: Decimal
    tax_collected_account_id: Optional[int] = None
    tax_paid_account_id: Optional[int] = None
    country: Optional[str] = None
    state: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: bool
    is_compound: bool
    created_at: datetime
    updated_at: datetime


class TaxExemptionCreate(BaseModel):
    entity_type: str
    entity_id: int
    certificate_number: str
    exemption_reason: str
    tax_rate_id: Optional[int] = None
    effective_from: date
    effective_to: Optional[date] = None
    notes: Optional[str] = None


class TaxExemptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int
    certificate_number: str
    exemption_reason: str
    tax_rate_id: Optional[int] = None
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TaxPeriodCreate(BaseModel):
    name: str
    tax_type: TaxType
    period_start: date
    period_end: date
    due_date: date
    notes: Optional[str] = None


class TaxPeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tax_type: TaxType
    period_start: date
    period_end: date
    due_date: date
    tax_collected: Decimal
    tax_paid: Decimal
    net_tax_due: Decimal
    is_filed: bool
    filed_at: Optional[datetime] = None
    filed_by_id: Optional[int] = None
    payment_reference: Optional[str] = None
    payment_date: Optional[date] = None
    payment_amount: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TaxSummaryReport(BaseModel):
    start_date: date
    end_date: date
    tax_collected: Decimal
    tax_paid: Decimal
    net_tax_liability: Decimal
    taxable_sales_count: int
    taxable_purchases_count: int
