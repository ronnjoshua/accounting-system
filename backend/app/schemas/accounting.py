from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.accounting import AccountTypeEnum, JournalEntryStatus


class AccountTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: AccountTypeEnum
    description: Optional[str] = None
    normal_balance: str


class AccountBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    account_type_id: int
    parent_id: Optional[int] = None
    currency_code: str = "USD"


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    currency_code: Optional[str] = None


class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_system: bool
    current_balance: Decimal
    account_type: AccountTypeResponse
    created_at: datetime
    updated_at: datetime


class CurrencyCreate(BaseModel):
    code: str
    name: str
    symbol: str
    decimal_places: int = 2


class CurrencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    symbol: str
    decimal_places: int
    is_active: bool


class ExchangeRateCreate(BaseModel):
    from_currency_code: str
    to_currency_code: str
    rate: Decimal
    effective_date: date


class ExchangeRateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_currency_code: str
    to_currency_code: str
    rate: Decimal
    effective_date: date


class JournalEntryLineCreate(BaseModel):
    account_id: int
    description: Optional[str] = None
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("1")


class JournalEntryLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    description: Optional[str] = None
    debit: Decimal
    credit: Decimal
    currency_code: str
    exchange_rate: Decimal
    base_debit: Decimal
    base_credit: Decimal


class JournalEntryCreate(BaseModel):
    entry_date: date
    description: str
    reference: Optional[str] = None
    is_adjusting: bool = False
    lines: List[JournalEntryLineCreate]


class JournalEntryUpdate(BaseModel):
    entry_date: Optional[date] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    is_adjusting: Optional[bool] = None
    lines: Optional[List[JournalEntryLineCreate]] = None


class JournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_number: str
    entry_date: date
    description: str
    reference: Optional[str] = None
    status: JournalEntryStatus
    is_adjusting: bool
    is_closing: bool
    is_recurring: bool
    posted_at: Optional[datetime] = None
    lines: List[JournalEntryLineResponse] = []
    created_at: datetime
    updated_at: datetime
