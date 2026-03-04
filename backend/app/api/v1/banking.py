from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.accounting import Account, JournalEntry, JournalEntryLine
from app.models.banking import (
    BankReconciliation, BankReconciliationItem, BankTransaction,
    ReconciliationStatus
)
from app.schemas.banking import (
    BankReconciliationCreate, BankReconciliationResponse,
    BankReconciliationItemCreate, BankReconciliationItemResponse,
    BankTransactionResponse, ReconciliationSummary
)

router = APIRouter()


@router.get("/reconciliations", response_model=List[BankReconciliationResponse])
def list_reconciliations(
    account_id: Optional[int] = None,
    status: Optional[ReconciliationStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(BankReconciliation)

    if account_id:
        query = query.where(BankReconciliation.account_id == account_id)
    if status:
        query = query.where(BankReconciliation.status == status)

    query = query.order_by(BankReconciliation.statement_date.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("/reconciliations", response_model=BankReconciliationResponse)
def create_reconciliation(
    data: BankReconciliationCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    # Validate account exists and is a bank/cash account
    account = db.execute(select(Account).where(Account.id == data.account_id)).scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Get current GL balance for this account
    gl_balance = account.current_balance

    reconciliation = BankReconciliation(
        account_id=data.account_id,
        statement_date=data.statement_date,
        statement_balance=data.statement_balance,
        gl_balance=gl_balance,
        reconciled_balance=Decimal("0"),
        difference=data.statement_balance - gl_balance,
        notes=data.notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(reconciliation)
    db.commit()
    db.refresh(reconciliation)
    return reconciliation


@router.get("/reconciliations/{reconciliation_id}", response_model=BankReconciliationResponse)
def get_reconciliation(
    reconciliation_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(
        select(BankReconciliation).where(BankReconciliation.id == reconciliation_id)
    )
    reconciliation = result.scalar_one_or_none()
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    return reconciliation


@router.get("/reconciliations/{reconciliation_id}/uncleared")
def get_uncleared_transactions(
    reconciliation_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get uncleared transactions for a bank account"""
    reconciliation = db.execute(
        select(BankReconciliation).where(BankReconciliation.id == reconciliation_id)
    ).scalar_one_or_none()

    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")

    # Get all journal entry lines for this account that are not yet cleared
    cleared_line_ids = db.execute(
        select(BankReconciliationItem.journal_entry_line_id)
        .where(BankReconciliationItem.is_cleared == True)
    ).scalars().all()

    query = (
        select(JournalEntryLine)
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(JournalEntryLine.account_id == reconciliation.account_id)
        .where(JournalEntry.entry_date <= reconciliation.statement_date)
    )

    if cleared_line_ids:
        query = query.where(JournalEntryLine.id.notin_(cleared_line_ids))

    result = db.execute(query)
    lines = result.scalars().all()

    uncleared = []
    for line in lines:
        je = db.execute(
            select(JournalEntry).where(JournalEntry.id == line.journal_entry_id)
        ).scalar_one()

        amount = line.debit - line.credit if line.debit > 0 else -(line.credit - line.debit)

        uncleared.append({
            "journal_entry_line_id": line.id,
            "journal_entry_id": je.id,
            "entry_number": je.entry_number,
            "entry_date": je.entry_date.isoformat(),
            "description": line.description or je.description,
            "amount": float(amount),
            "debit": float(line.debit),
            "credit": float(line.credit)
        })

    return uncleared


@router.post("/reconciliations/{reconciliation_id}/items", response_model=BankReconciliationItemResponse)
def add_reconciliation_item(
    reconciliation_id: int,
    data: BankReconciliationItemCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    reconciliation = db.execute(
        select(BankReconciliation).where(BankReconciliation.id == reconciliation_id)
    ).scalar_one_or_none()

    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")

    if reconciliation.status != ReconciliationStatus.in_progress:
        raise HTTPException(status_code=400, detail="Cannot modify completed reconciliation")

    item = BankReconciliationItem(
        reconciliation_id=reconciliation_id,
        journal_entry_line_id=data.journal_entry_line_id,
        transaction_date=data.transaction_date,
        description=data.description,
        amount=data.amount,
        is_cleared=data.is_cleared,
        cleared_date=date.today() if data.is_cleared else None
    )

    db.add(item)

    # Update reconciled balance
    if data.is_cleared:
        reconciliation.reconciled_balance += data.amount

    reconciliation.difference = reconciliation.statement_balance - reconciliation.gl_balance - reconciliation.reconciled_balance

    db.commit()
    db.refresh(item)
    return item


@router.patch("/reconciliations/{reconciliation_id}/items/{item_id}/clear")
def toggle_clear_item(
    reconciliation_id: int,
    item_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    """Toggle cleared status of a reconciliation item"""
    item = db.execute(
        select(BankReconciliationItem).where(and_(
            BankReconciliationItem.id == item_id,
            BankReconciliationItem.reconciliation_id == reconciliation_id
        ))
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    reconciliation = db.execute(
        select(BankReconciliation).where(BankReconciliation.id == reconciliation_id)
    ).scalar_one()

    if reconciliation.status != ReconciliationStatus.in_progress:
        raise HTTPException(status_code=400, detail="Cannot modify completed reconciliation")

    # Toggle cleared status
    if item.is_cleared:
        item.is_cleared = False
        item.cleared_date = None
        reconciliation.reconciled_balance -= item.amount
    else:
        item.is_cleared = True
        item.cleared_date = date.today()
        reconciliation.reconciled_balance += item.amount

    reconciliation.difference = reconciliation.statement_balance - reconciliation.gl_balance

    db.commit()

    return {"is_cleared": item.is_cleared, "reconciled_balance": float(reconciliation.reconciled_balance)}


@router.post("/reconciliations/{reconciliation_id}/complete", response_model=BankReconciliationResponse)
def complete_reconciliation(
    reconciliation_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    reconciliation = db.execute(
        select(BankReconciliation).where(BankReconciliation.id == reconciliation_id)
    ).scalar_one_or_none()

    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")

    if reconciliation.status != ReconciliationStatus.in_progress:
        raise HTTPException(status_code=400, detail="Reconciliation is not in progress")

    # Check if balanced (difference should be zero or within tolerance)
    if abs(reconciliation.difference) > Decimal("0.01"):
        raise HTTPException(
            status_code=400,
            detail=f"Reconciliation is not balanced. Difference: {reconciliation.difference}"
        )

    reconciliation.status = ReconciliationStatus.completed
    reconciliation.completed_at = datetime.utcnow()
    reconciliation.completed_by_id = current_user.id

    db.commit()
    db.refresh(reconciliation)
    return reconciliation


@router.get("/reconciliations/{reconciliation_id}/summary", response_model=ReconciliationSummary)
def get_reconciliation_summary(
    reconciliation_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    reconciliation = db.execute(
        select(BankReconciliation).where(BankReconciliation.id == reconciliation_id)
    ).scalar_one_or_none()

    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")

    # Count items
    total_items = db.execute(
        select(func.count(BankReconciliationItem.id))
        .where(BankReconciliationItem.reconciliation_id == reconciliation_id)
    ).scalar() or 0

    cleared_items = db.execute(
        select(func.count(BankReconciliationItem.id))
        .where(and_(
            BankReconciliationItem.reconciliation_id == reconciliation_id,
            BankReconciliationItem.is_cleared == True
        ))
    ).scalar() or 0

    return {
        "reconciliation_id": reconciliation.id,
        "account_id": reconciliation.account_id,
        "statement_date": reconciliation.statement_date,
        "statement_balance": reconciliation.statement_balance,
        "gl_balance": reconciliation.gl_balance,
        "reconciled_balance": reconciliation.reconciled_balance,
        "difference": reconciliation.difference,
        "status": reconciliation.status,
        "total_items": total_items,
        "cleared_items": cleared_items,
        "uncleared_items": total_items - cleared_items
    }
