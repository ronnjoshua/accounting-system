from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models.ap import BillStatus


class VendorBase(BaseModel):
    code: str
    name: str
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    currency_code: str = "USD"
    payment_terms_days: int = 30
    payable_account_id: Optional[int] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_routing_number: Optional[str] = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    currency_code: Optional[str] = None
    payment_terms_days: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_routing_number: Optional[str] = None


class VendorResponse(VendorBase):
    id: int
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class BillLineCreate(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    tax_percent: Decimal = Decimal("0")
    account_id: Optional[int] = None  # Will use default expense account if not provided


class BillLineResponse(BaseModel):
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
        orm_mode = True


class BillCreate(BaseModel):
    vendor_id: int
    vendor_bill_number: Optional[str] = None
    bill_date: date
    due_date: date
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("1")
    reference: Optional[str] = None
    notes: Optional[str] = None
    purchase_order_id: Optional[int] = None
    lines: List[BillLineCreate]


class BillUpdate(BaseModel):
    vendor_bill_number: Optional[str] = None
    bill_date: Optional[date] = None
    due_date: Optional[date] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    lines: Optional[List[BillLineCreate]] = None


class BillResponse(BaseModel):
    id: int
    bill_number: str
    vendor_bill_number: Optional[str] = None
    vendor_id: int
    bill_date: date
    due_date: date
    status: BillStatus
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
    purchase_order_id: Optional[int] = None
    lines: List[BillLineResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class VendorPaymentCreate(BaseModel):
    vendor_id: int
    payment_date: date
    amount: Decimal
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("1")
    payment_method: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    bank_account_id: int
    bill_id: Optional[int] = None


class VendorPaymentResponse(BaseModel):
    id: int
    payment_number: str
    vendor_id: int
    payment_date: date
    amount: Decimal
    currency_code: str
    exchange_rate: Decimal
    payment_method: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    bank_account_id: int
    bill_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True
