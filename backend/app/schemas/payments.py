from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


# ============== Customer Payments ==============

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
    journal_entry_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ============== Vendor Payments ==============

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
    journal_entry_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ============== Credit Notes ==============

class CreditNoteCreate(BaseModel):
    customer_id: int
    invoice_id: Optional[int] = None
    credit_date: date
    amount: Decimal
    reason: str
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("1")


class CreditNoteResponse(BaseModel):
    id: int
    credit_note_number: str
    customer_id: int
    invoice_id: Optional[int] = None
    credit_date: date
    amount: Decimal
    reason: str
    currency_code: str
    exchange_rate: Decimal
    journal_entry_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ============== Debit Notes ==============

class DebitNoteCreate(BaseModel):
    vendor_id: int
    bill_id: Optional[int] = None
    debit_date: date
    amount: Decimal
    reason: str
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("1")


class DebitNoteResponse(BaseModel):
    id: int
    debit_note_number: str
    vendor_id: int
    bill_id: Optional[int] = None
    debit_date: date
    amount: Decimal
    reason: str
    currency_code: str
    exchange_rate: Decimal
    journal_entry_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
