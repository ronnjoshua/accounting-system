from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Date, Boolean, Text, Numeric, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import AuditMixin
import enum


class RecurringFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"


class RecurringStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"


class RecurringType(str, enum.Enum):
    journal_entry = "journal_entry"
    invoice = "invoice"
    bill = "bill"


class RecurringTemplate(Base, AuditMixin):
    """Template for recurring transactions"""
    __tablename__ = "recurring_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    recurring_type: Mapped[RecurringType] = mapped_column(SQLEnum(RecurringType), nullable=False)
    frequency: Mapped[RecurringFrequency] = mapped_column(SQLEnum(RecurringFrequency), nullable=False)

    # Schedule
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # Null = no end
    next_run_date: Mapped[date] = mapped_column(Date, nullable=False)

    # For monthly/quarterly: day of month (1-31, or -1 for last day)
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # For weekly: day of week (0=Monday, 6=Sunday)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[RecurringStatus] = mapped_column(
        SQLEnum(RecurringStatus), default=RecurringStatus.active, nullable=False
    )

    # Execution tracking
    total_occurrences: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Max runs, null = unlimited
    occurrences_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_run_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_run_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Template data (stored as JSON)
    template_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Auto-post option
    auto_post: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    executions: Mapped[List["RecurringExecution"]] = relationship(
        "RecurringExecution", back_populates="template", cascade="all, delete-orphan"
    )


class RecurringExecution(Base):
    """Log of recurring transaction executions"""
    __tablename__ = "recurring_executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("recurring_templates.id", ondelete="CASCADE"), nullable=False
    )

    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False)  # success, failed, skipped
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reference to created entity
    created_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    executed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    template: Mapped[RecurringTemplate] = relationship("RecurringTemplate", back_populates="executions")
