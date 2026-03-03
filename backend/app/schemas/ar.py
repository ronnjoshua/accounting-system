from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models.ar import InvoiceStatus


class CustomerBase(BaseModel):
    code: str
    name: str
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    billing_address_line1: Optional[str] = None
    billing_address_line2: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None
    shipping_address_line1: Optional[str] = None
    shipping_address_line2: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None
    tax_id: Optional[str] = None
    currency_code: str = "USD"
    credit_limit: Optional[Decimal] = None
    payment_terms_days: int = 30
    receivable_account_id: Optional[int] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    billing_address_line1: Optional[str] = None
    billing_address_line2: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None
    shipping_address_line1: Optional[str] = None
    shipping_address_line2: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None
    tax_id: Optional[str] = None
    currency_code: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms_days: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceLineCreate(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    tax_percent: Decimal = Decimal("0")
    account_id: int


class InvoiceLineResponse(BaseModel):
    id: int
    product_id: Optional[int] = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_percent: Decimal
    tax_percent: Decimal
    line_total: Decimal
    account_id: int

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    customer_id: int
    invoice_date: date
    due_date: date
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("1")
    reference: Optional[str] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    lines: List[InvoiceLineCreate]


class InvoiceUpdate(BaseModel):
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    lines: Optional[List[InvoiceLineCreate]] = None


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    invoice_date: date
    due_date: date
    status: InvoiceStatus
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    currency_code: str
    exchange_rate: Decimal
    reference: Optional[str] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    lines: List[InvoiceLineResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerPaymentCreate(BaseModel):
    customer_id: int
    payment_date: date
    amount: Decimal
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("1")
    payment_method: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    bank_account_id: int
    invoice_id: Optional[int] = None


class CustomerPaymentResponse(BaseModel):
    id: int
    payment_number: str
    customer_id: int
    payment_date: date
    amount: Decimal
    currency_code: str
    exchange_rate: Decimal
    payment_method: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    bank_account_id: int
    invoice_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
