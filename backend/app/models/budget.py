from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Date, Boolean, Text, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import AuditMixin
import enum


class BudgetPeriodType(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BudgetStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    CLOSED = "closed"


class Budget(Base, AuditMixin):
    """Budget header"""
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_type: Mapped[BudgetPeriodType] = mapped_column(
        SQLEnum(BudgetPeriodType), default=BudgetPeriodType.MONTHLY, nullable=False
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[BudgetStatus] = mapped_column(
        SQLEnum(BudgetStatus), default=BudgetStatus.DRAFT, nullable=False
    )

    total_revenue: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_expense: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    net_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[List["BudgetLine"]] = relationship(
        "BudgetLine", back_populates="budget", cascade="all, delete-orphan"
    )


class BudgetLine(Base):
    """Budget line items by account and period"""
    __tablename__ = "budget_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    # Period (month number 1-12, quarter 1-4, or 1 for yearly)
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    budgeted_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    variance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    variance_percent: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0, nullable=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    budget: Mapped[Budget] = relationship("Budget", back_populates="lines")
