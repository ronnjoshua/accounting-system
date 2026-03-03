from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.accounting import JournalEntry, JournalEntryStatus
from app.schemas.accounting import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryResponse
)
from app.services.accounting import (
    create_journal_entry, post_journal_entry, void_journal_entry
)

router = APIRouter()


@router.get("", response_model=List[JournalEntryResponse])
async def list_journal_entries(
    status: Optional[JournalEntryStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    query = select(JournalEntry)

    if status:
        query = query.where(JournalEntry.status == status)
    if start_date:
        query = query.where(JournalEntry.entry_date >= start_date)
    if end_date:
        query = query.where(JournalEntry.entry_date <= end_date)

    query = query.order_by(JournalEntry.entry_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=JournalEntryResponse)
async def create_entry(
    data: JournalEntryCreate,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    try:
        entry = await create_journal_entry(db, data, current_user.id)
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: int,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.patch("/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(
    entry_id: int,
    data: JournalEntryUpdate,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if entry.status != JournalEntryStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Only draft entries can be modified"
        )

    # Handle lines update separately if provided
    if data.lines is not None:
        # Delete existing lines and create new ones
        for line in entry.lines:
            await db.delete(line)

        for line_data in data.lines:
            from app.models.accounting import JournalEntryLine
            line = JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=line_data.account_id,
                description=line_data.description,
                debit=line_data.debit,
                credit=line_data.credit,
                currency_code=line_data.currency_code,
                exchange_rate=line_data.exchange_rate,
                base_debit=line_data.debit * line_data.exchange_rate,
                base_credit=line_data.credit * line_data.exchange_rate
            )
            db.add(line)

    # Update other fields
    update_data = data.model_dump(exclude_unset=True, exclude={"lines"})
    for field, value in update_data.items():
        setattr(entry, field, value)

    entry.updated_by_id = current_user.id
    await db.commit()
    await db.refresh(entry)
    return entry


@router.post("/{entry_id}/post", response_model=JournalEntryResponse)
async def post_entry(
    entry_id: int,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    try:
        entry = await post_journal_entry(db, entry, current_user.id)
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/void", response_model=JournalEntryResponse)
async def void_entry(
    entry_id: int,
    reason: str = Query(..., min_length=1),
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    try:
        entry = await void_journal_entry(db, entry, current_user.id, reason)
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
