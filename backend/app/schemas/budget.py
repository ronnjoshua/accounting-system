from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.budget import BudgetPeriodType, BudgetStatus


class BudgetLineCreate(BaseModel):
    account_id: int
    period: int
    budgeted_amount: Decimal
    notes: Optional[str] = None


class BudgetLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    budget_id: int
    account_id: int
    period: int
    period_start: date
    period_end: date
    budgeted_amount: Decimal
    actual_amount: Decimal
    variance: Decimal
    variance_percent: Decimal
    notes: Optional[str] = None


class BudgetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fiscal_year: int
    period_type: BudgetPeriodType = BudgetPeriodType.MONTHLY
    notes: Optional[str] = None


class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    fiscal_year: int
    period_type: BudgetPeriodType
    start_date: date
    end_date: date
    status: BudgetStatus
    total_revenue: Decimal
    total_expense: Decimal
    net_income: Decimal
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    lines: List[BudgetLineResponse] = []
    created_at: datetime
    updated_at: datetime


class BudgetLineActual(BaseModel):
    account_id: int
    account_code: str
    account_name: str
    period: int
    period_start: date
    period_end: date
    budgeted_amount: Decimal
    actual_amount: Decimal
    variance: Decimal
    variance_percent: Decimal


class BudgetVsActualReport(BaseModel):
    budget_id: int
    budget_name: str
    fiscal_year: int
    period_type: BudgetPeriodType
    lines: List[BudgetLineActual]
    total_budgeted: Decimal
    total_actual: Decimal
    total_variance: Decimal
    total_variance_percent: Decimal
