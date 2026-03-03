from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Date, Boolean, Text, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import AuditMixin
import enum


class ReconciliationStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BankReconciliation(Base, AuditMixin):
    """Bank reconciliation header"""
    __tablename__ = "bank_reconciliations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    statement_date: Mapped[date] = mapped_column(Date, nullable=False)
    statement_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    gl_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reconciled_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    difference: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    status: Mapped[ReconciliationStatus] = mapped_column(
        SQLEnum(ReconciliationStatus), default=ReconciliationStatus.IN_PROGRESS, nullable=False
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    items: Mapped[List["BankReconciliationItem"]] = relationship(
        "BankReconciliationItem", back_populates="reconciliation", cascade="all, delete-orphan"
    )


class BankReconciliationItem(Base):
    """Individual reconciliation items (matched transactions)"""
    __tablename__ = "bank_reconciliation_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    reconciliation_id: Mapped[int] = mapped_column(
        ForeignKey("bank_reconciliations.id", ondelete="CASCADE"), nullable=False
    )

    # Journal entry line that this matches
    journal_entry_line_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("journal_entry_lines.id"), nullable=True
    )

    # Or manual entry for statement items not in GL
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    is_cleared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cleared_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    reconciliation: Mapped[BankReconciliation] = relationship("BankReconciliation", back_populates="items")


class BankTransaction(Base, AuditMixin):
    """Imported bank transactions (for bank feed integration)"""
    __tablename__ = "bank_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # Bank's transaction ID
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    post_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Matching
    is_matched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    matched_journal_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)
    matched_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    matched_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Categorization
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    memo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
