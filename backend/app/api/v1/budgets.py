from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.accounting import Account, AccountType, JournalEntry, JournalEntryLine, JournalEntryStatus
from app.models.budget import Budget, BudgetLine, BudgetPeriodType, BudgetStatus
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetResponse,
    BudgetLineCreate, BudgetLineResponse,
    BudgetVsActualReport
)

router = APIRouter()


def calculate_period_dates(fiscal_year: int, period_type: BudgetPeriodType, period: int):
    """Calculate start and end dates for a budget period"""
    if period_type == BudgetPeriodType.MONTHLY:
        start = date(fiscal_year, period, 1)
        end = start + relativedelta(months=1, days=-1)
    elif period_type == BudgetPeriodType.QUARTERLY:
        start_month = (period - 1) * 3 + 1
        start = date(fiscal_year, start_month, 1)
        end = start + relativedelta(months=3, days=-1)
    else:  # YEARLY
        start = date(fiscal_year, 1, 1)
        end = date(fiscal_year, 12, 31)
    return start, end


def get_actual_amount(db: Session, account_id: int, start_date: date, end_date: date) -> Decimal:
    """Get actual amount from journal entries for an account in a period"""
    result = db.execute(
        select(
            func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(and_(
            JournalEntryLine.account_id == account_id,
            JournalEntry.status == JournalEntryStatus.POSTED.value,
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date
        ))
    )
    return result.scalar() or Decimal("0")


@router.get("", response_model=List[BudgetResponse])
def list_budgets(
    fiscal_year: Optional[int] = None,
    status: Optional[BudgetStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(Budget)

    if fiscal_year:
        query = query.where(Budget.fiscal_year == fiscal_year)
    if status:
        query = query.where(Budget.status == status)

    query = query.order_by(Budget.fiscal_year.desc(), Budget.name).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("", response_model=BudgetResponse)
def create_budget(
    data: BudgetCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    # Calculate start and end dates based on fiscal year
    start_date = date(data.fiscal_year, 1, 1)
    end_date = date(data.fiscal_year, 12, 31)

    budget = Budget(
        name=data.name,
        description=data.description,
        fiscal_year=data.fiscal_year,
        period_type=data.period_type,
        start_date=start_date,
        end_date=end_date,
        notes=data.notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Budget).where(Budget.id == budget_id))
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.patch("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    budget = db.execute(select(Budget).where(Budget.id == budget_id)).scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    if budget.status not in [BudgetStatus.DRAFT]:
        raise HTTPException(status_code=400, detail="Only draft budgets can be modified")

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)

    budget.updated_by_id = current_user.id
    db.commit()
    db.refresh(budget)
    return budget


@router.post("/{budget_id}/lines", response_model=BudgetLineResponse)
def add_budget_line(
    budget_id: int,
    data: BudgetLineCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    budget = db.execute(select(Budget).where(Budget.id == budget_id)).scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    if budget.status not in [BudgetStatus.DRAFT, BudgetStatus.APPROVED]:
        raise HTTPException(status_code=400, detail="Cannot modify this budget")

    # Validate account
    account = db.execute(select(Account).where(Account.id == data.account_id)).scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Calculate period dates
    period_start, period_end = calculate_period_dates(budget.fiscal_year, budget.period_type, data.period)

    # Check for duplicate
    existing = db.execute(
        select(BudgetLine).where(and_(
            BudgetLine.budget_id == budget_id,
            BudgetLine.account_id == data.account_id,
            BudgetLine.period == data.period
        ))
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Budget line already exists for this account and period")

    line = BudgetLine(
        budget_id=budget_id,
        account_id=data.account_id,
        period=data.period,
        period_start=period_start,
        period_end=period_end,
        budgeted_amount=data.budgeted_amount,
        notes=data.notes
    )

    db.add(line)

    # Update budget totals
    account_type = db.execute(
        select(AccountType).where(AccountType.id == account.account_type_id)
    ).scalar_one()

    if account_type.name.lower() == "revenue":
        budget.total_revenue += data.budgeted_amount
    elif account_type.name.lower() == "expense":
        budget.total_expense += data.budgeted_amount

    budget.net_income = budget.total_revenue - budget.total_expense

    db.commit()
    db.refresh(line)
    return line


@router.patch("/{budget_id}/lines/{line_id}", response_model=BudgetLineResponse)
def update_budget_line(
    budget_id: int,
    line_id: int,
    data: BudgetLineCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    line = db.execute(
        select(BudgetLine).where(and_(
            BudgetLine.id == line_id,
            BudgetLine.budget_id == budget_id
        ))
    ).scalar_one_or_none()

    if not line:
        raise HTTPException(status_code=404, detail="Budget line not found")

    budget = db.execute(select(Budget).where(Budget.id == budget_id)).scalar_one()

    if budget.status not in [BudgetStatus.DRAFT, BudgetStatus.APPROVED]:
        raise HTTPException(status_code=400, detail="Cannot modify this budget")

    old_amount = line.budgeted_amount
    line.budgeted_amount = data.budgeted_amount
    line.notes = data.notes

    # Update budget totals
    account = db.execute(select(Account).where(Account.id == line.account_id)).scalar_one()
    account_type = db.execute(
        select(AccountType).where(AccountType.id == account.account_type_id)
    ).scalar_one()

    diff = data.budgeted_amount - old_amount
    if account_type.name.lower() == "revenue":
        budget.total_revenue += diff
    elif account_type.name.lower() == "expense":
        budget.total_expense += diff

    budget.net_income = budget.total_revenue - budget.total_expense

    db.commit()
    db.refresh(line)
    return line


@router.post("/{budget_id}/approve", response_model=BudgetResponse)
def approve_budget(
    budget_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    budget = db.execute(select(Budget).where(Budget.id == budget_id)).scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    if budget.status != BudgetStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft budgets can be approved")

    budget.status = BudgetStatus.APPROVED
    budget.approved_by_id = current_user.id
    budget.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(budget)
    return budget


@router.post("/{budget_id}/activate", response_model=BudgetResponse)
def activate_budget(
    budget_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    budget = db.execute(select(Budget).where(Budget.id == budget_id)).scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    if budget.status != BudgetStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only approved budgets can be activated")

    budget.status = BudgetStatus.ACTIVE

    db.commit()
    db.refresh(budget)
    return budget


@router.get("/{budget_id}/vs-actual", response_model=BudgetVsActualReport)
def get_budget_vs_actual(
    budget_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get budget vs actual comparison report"""
    budget = db.execute(select(Budget).where(Budget.id == budget_id)).scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    lines = db.execute(
        select(BudgetLine).where(BudgetLine.budget_id == budget_id)
    ).scalars().all()

    report_lines = []
    total_budgeted = Decimal("0")
    total_actual = Decimal("0")

    for line in lines:
        # Get actual amount for this account and period
        actual = get_actual_amount(db, line.account_id, line.period_start, line.period_end)

        # Get account info
        account = db.execute(select(Account).where(Account.id == line.account_id)).scalar_one()

        variance = actual - line.budgeted_amount
        variance_pct = (variance / line.budgeted_amount * 100) if line.budgeted_amount != 0 else Decimal("0")

        report_lines.append({
            "account_id": line.account_id,
            "account_code": account.code,
            "account_name": account.name,
            "period": line.period,
            "period_start": line.period_start,
            "period_end": line.period_end,
            "budgeted_amount": line.budgeted_amount,
            "actual_amount": actual,
            "variance": variance,
            "variance_percent": variance_pct
        })

        total_budgeted += line.budgeted_amount
        total_actual += actual

    return {
        "budget_id": budget.id,
        "budget_name": budget.name,
        "fiscal_year": budget.fiscal_year,
        "period_type": budget.period_type,
        "lines": report_lines,
        "total_budgeted": total_budgeted,
        "total_actual": total_actual,
        "total_variance": total_actual - total_budgeted,
        "total_variance_percent": ((total_actual - total_budgeted) / total_budgeted * 100) if total_budgeted != 0 else Decimal("0")
    }
