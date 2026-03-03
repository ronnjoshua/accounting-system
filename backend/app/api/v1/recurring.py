from typing import List, Optional
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.accounting import JournalEntry, JournalEntryLine, JournalEntryStatus
from app.models.ar import Invoice, InvoiceLine, Customer
from app.models.ap import Bill, BillLine, Vendor
from app.models.recurring import (
    RecurringTemplate, RecurringExecution,
    RecurringFrequency, RecurringStatus, RecurringType
)
from app.schemas.recurring import (
    RecurringTemplateCreate, RecurringTemplateUpdate, RecurringTemplateResponse,
    RecurringExecutionResponse
)

router = APIRouter()


def calculate_next_run_date(current_date: date, frequency: RecurringFrequency,
                            day_of_month: Optional[int] = None,
                            day_of_week: Optional[int] = None) -> date:
    """Calculate the next run date based on frequency"""
    if frequency == RecurringFrequency.DAILY:
        return current_date + timedelta(days=1)
    elif frequency == RecurringFrequency.WEEKLY:
        return current_date + timedelta(weeks=1)
    elif frequency == RecurringFrequency.BIWEEKLY:
        return current_date + timedelta(weeks=2)
    elif frequency == RecurringFrequency.MONTHLY:
        next_date = current_date + relativedelta(months=1)
        if day_of_month:
            if day_of_month == -1:
                # Last day of month
                next_date = next_date + relativedelta(day=31)
            else:
                try:
                    next_date = next_date.replace(day=min(day_of_month, 28))
                except ValueError:
                    next_date = next_date + relativedelta(day=28)
        return next_date
    elif frequency == RecurringFrequency.QUARTERLY:
        return current_date + relativedelta(months=3)
    elif frequency == RecurringFrequency.YEARLY:
        return current_date + relativedelta(years=1)
    return current_date + timedelta(days=1)


@router.get("", response_model=List[RecurringTemplateResponse])
def list_recurring_templates(
    recurring_type: Optional[RecurringType] = None,
    status: Optional[RecurringStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(RecurringTemplate)

    if recurring_type:
        query = query.where(RecurringTemplate.recurring_type == recurring_type)
    if status:
        query = query.where(RecurringTemplate.status == status)

    query = query.order_by(RecurringTemplate.next_run_date).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("", response_model=RecurringTemplateResponse)
def create_recurring_template(
    data: RecurringTemplateCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    template = RecurringTemplate(
        name=data.name,
        description=data.description,
        recurring_type=data.recurring_type,
        frequency=data.frequency,
        start_date=data.start_date,
        end_date=data.end_date,
        next_run_date=data.start_date,
        day_of_month=data.day_of_month,
        day_of_week=data.day_of_week,
        total_occurrences=data.total_occurrences,
        template_data=data.template_data,
        auto_post=data.auto_post,
        notes=data.notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=RecurringTemplateResponse)
def get_recurring_template(
    template_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(RecurringTemplate).where(RecurringTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Recurring template not found")
    return template


@router.patch("/{template_id}", response_model=RecurringTemplateResponse)
def update_recurring_template(
    template_id: int,
    data: RecurringTemplateUpdate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    template = db.execute(
        select(RecurringTemplate).where(RecurringTemplate.id == template_id)
    ).scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Recurring template not found")

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    template.updated_by_id = current_user.id
    db.commit()
    db.refresh(template)
    return template


@router.post("/{template_id}/pause", response_model=RecurringTemplateResponse)
def pause_recurring_template(
    template_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    template = db.execute(
        select(RecurringTemplate).where(RecurringTemplate.id == template_id)
    ).scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Recurring template not found")

    if template.status != RecurringStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Only active templates can be paused")

    template.status = RecurringStatus.PAUSED
    db.commit()
    db.refresh(template)
    return template


@router.post("/{template_id}/resume", response_model=RecurringTemplateResponse)
def resume_recurring_template(
    template_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    template = db.execute(
        select(RecurringTemplate).where(RecurringTemplate.id == template_id)
    ).scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Recurring template not found")

    if template.status != RecurringStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Only paused templates can be resumed")

    template.status = RecurringStatus.ACTIVE
    # Update next run date to today or later
    if template.next_run_date < date.today():
        template.next_run_date = date.today()

    db.commit()
    db.refresh(template)
    return template


@router.post("/{template_id}/execute", response_model=RecurringExecutionResponse)
def execute_recurring_template(
    template_id: int,
    execution_date: Optional[date] = None,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    """Manually execute a recurring template"""
    template = db.execute(
        select(RecurringTemplate).where(RecurringTemplate.id == template_id)
    ).scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Recurring template not found")

    if template.status not in [RecurringStatus.ACTIVE, RecurringStatus.PAUSED]:
        raise HTTPException(status_code=400, detail="Template is not active or paused")

    exec_date = execution_date or date.today()
    execution = RecurringExecution(
        template_id=template_id,
        scheduled_date=exec_date,
        executed_by_id=current_user.id,
        status="pending"
    )

    try:
        created_entity_type = None
        created_entity_id = None

        if template.recurring_type == RecurringType.JOURNAL_ENTRY:
            # Create journal entry from template
            data = template.template_data

            from sqlalchemy import func
            je_count_result = db.execute(select(func.count(JournalEntry.id)))
            je_count = je_count_result.scalar() or 0
            je_number = f"JE-{je_count + 1:06d}"

            je = JournalEntry(
                entry_number=je_number,
                entry_date=exec_date,
                description=data.get("description", template.name),
                reference=f"Recurring: {template.name}",
                currency_code=data.get("currency_code", "USD"),
                exchange_rate=data.get("exchange_rate", 1),
                is_recurring=True,
                recurring_template_id=template_id,
                status=JournalEntryStatus.POSTED if template.auto_post else JournalEntryStatus.DRAFT,
                created_by_id=current_user.id,
                updated_by_id=current_user.id
            )

            if template.auto_post:
                je.posted_by_id = current_user.id

            db.add(je)
            db.flush()

            for line_data in data.get("lines", []):
                line = JournalEntryLine(
                    journal_entry_id=je.id,
                    account_id=line_data["account_id"],
                    description=line_data.get("description", ""),
                    debit=line_data.get("debit", 0),
                    credit=line_data.get("credit", 0),
                    base_debit=line_data.get("debit", 0),
                    base_credit=line_data.get("credit", 0)
                )
                db.add(line)

            created_entity_type = "journal_entry"
            created_entity_id = je.id

        execution.status = "success"
        execution.created_entity_type = created_entity_type
        execution.created_entity_id = created_entity_id

    except Exception as e:
        execution.status = "failed"
        execution.error_message = str(e)

    db.add(execution)

    # Update template
    template.last_run_date = exec_date
    template.last_run_status = execution.status
    template.occurrences_completed += 1

    # Calculate next run date
    template.next_run_date = calculate_next_run_date(
        exec_date, template.frequency, template.day_of_month, template.day_of_week
    )

    # Check if completed
    if template.total_occurrences and template.occurrences_completed >= template.total_occurrences:
        template.status = RecurringStatus.COMPLETED
    elif template.end_date and template.next_run_date > template.end_date:
        template.status = RecurringStatus.COMPLETED

    db.commit()
    db.refresh(execution)
    return execution


@router.get("/{template_id}/executions", response_model=List[RecurringExecutionResponse])
def list_template_executions(
    template_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    template = db.execute(
        select(RecurringTemplate).where(RecurringTemplate.id == template_id)
    ).scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Recurring template not found")

    query = (
        select(RecurringExecution)
        .where(RecurringExecution.template_id == template_id)
        .order_by(RecurringExecution.executed_at.desc())
        .offset(skip).limit(limit)
    )
    result = db.execute(query)
    return result.scalars().all()


@router.get("/due")
def get_due_recurring_templates(
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get recurring templates that are due for execution"""
    today = date.today()

    query = select(RecurringTemplate).where(and_(
        RecurringTemplate.status == RecurringStatus.ACTIVE,
        RecurringTemplate.next_run_date <= today
    )).order_by(RecurringTemplate.next_run_date)

    result = db.execute(query)
    templates = result.scalars().all()

    return [
        {
            "id": t.id,
            "name": t.name,
            "recurring_type": t.recurring_type,
            "next_run_date": t.next_run_date.isoformat(),
            "days_overdue": (today - t.next_run_date).days
        }
        for t in templates
    ]
