from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel
from app.models.banking import ReconciliationStatus


class BankReconciliationCreate(BaseModel):
    account_id: int
    statement_date: date
    statement_balance: Decimal
    notes: Optional[str] = None


class BankReconciliationItemCreate(BaseModel):
    journal_entry_line_id: Optional[int] = None
    transaction_date: date
    description: str
    amount: Decimal
    is_cleared: bool = False


class BankReconciliationItemResponse(BaseModel):
    id: int
    reconciliation_id: int
    journal_entry_line_id: Optional[int] = None
    transaction_date: date
    description: str
    amount: Decimal
    is_cleared: bool
    cleared_date: Optional[date] = None

    class Config:
        orm_mode = True


class BankReconciliationResponse(BaseModel):
    id: int
    account_id: int
    statement_date: date
    statement_balance: Decimal
    gl_balance: Decimal
    reconciled_balance: Decimal
    difference: Decimal
    status: ReconciliationStatus
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    completed_by_id: Optional[int] = None
    items: List[BankReconciliationItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class BankTransactionResponse(BaseModel):
    id: int
    account_id: int
    transaction_id: str
    transaction_date: date
    post_date: Optional[date] = None
    description: str
    amount: Decimal
    is_matched: bool
    matched_journal_entry_id: Optional[int] = None
    matched_at: Optional[datetime] = None
    category: Optional[str] = None
    memo: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


class ReconciliationSummary(BaseModel):
    reconciliation_id: int
    account_id: int
    statement_date: date
    statement_balance: Decimal
    gl_balance: Decimal
    reconciled_balance: Decimal
    difference: Decimal
    status: ReconciliationStatus
    total_items: int
    cleared_items: int
    uncleared_items: int
