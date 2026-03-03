from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel
from app.models.recurring import RecurringFrequency, RecurringStatus, RecurringType


class RecurringTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    recurring_type: RecurringType
    frequency: RecurringFrequency
    start_date: date
    end_date: Optional[date] = None
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    total_occurrences: Optional[int] = None
    template_data: dict
    auto_post: bool = False
    notes: Optional[str] = None


class RecurringTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[RecurringFrequency] = None
    end_date: Optional[date] = None
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    total_occurrences: Optional[int] = None
    template_data: Optional[dict] = None
    auto_post: Optional[bool] = None
    notes: Optional[str] = None


class RecurringExecutionResponse(BaseModel):
    id: int
    template_id: int
    scheduled_date: date
    executed_at: datetime
    status: str
    error_message: Optional[str] = None
    created_entity_type: Optional[str] = None
    created_entity_id: Optional[int] = None
    executed_by_id: Optional[int] = None

    class Config:
        orm_mode = True


class RecurringTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    recurring_type: RecurringType
    frequency: RecurringFrequency
    start_date: date
    end_date: Optional[date] = None
    next_run_date: date
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    status: RecurringStatus
    total_occurrences: Optional[int] = None
    occurrences_completed: int
    last_run_date: Optional[date] = None
    last_run_status: Optional[str] = None
    template_data: dict
    auto_post: bool
    notes: Optional[str] = None
    executions: List[RecurringExecutionResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
