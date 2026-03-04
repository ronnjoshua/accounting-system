from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Date, Boolean, Text, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import AuditMixin
import enum


class AccountTypeEnum(str, enum.Enum):
    # Names must match database enum values (lowercase)
    asset = "asset"
    liability = "liability"
    equity = "equity"
    revenue = "revenue"
    expense = "expense"


class AccountType(Base, AuditMixin):
    __tablename__ = "account_types"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[AccountTypeEnum] = mapped_column(SQLEnum(AccountTypeEnum), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    normal_balance: Mapped[str] = mapped_column(String(10), nullable=False)  # debit or credit

    # Relationships
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="account_type")


class Account(Base, AuditMixin):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    account_type_id: Mapped[int] = mapped_column(ForeignKey("account_types.id"), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # System accounts can't be deleted
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Current balance (updated on each transaction)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    # Relationships
    account_type: Mapped[AccountType] = relationship("AccountType", back_populates="accounts")
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side=[id], back_populates="children")
    children: Mapped[List["Account"]] = relationship("Account", back_populates="parent")
    journal_lines: Mapped[List["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="account")


class Currency(Base, AuditMixin):
    __tablename__ = "currencies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    decimal_places: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ExchangeRate(Base, AuditMixin):
    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    from_currency_code: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    to_currency_code: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)


class JournalEntryStatus(str, enum.Enum):
    # Names must match database enum values (lowercase)
    draft = "draft"
    posted = "posted"
    void = "void"


class JournalEntry(Base, AuditMixin):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entry_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[JournalEntryStatus] = mapped_column(
        SQLEnum(JournalEntryStatus), default=JournalEntryStatus.draft, nullable=False
    )
    is_adjusting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_closing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fiscal_period_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fiscal_periods.id"), nullable=True)

    # For recurring entries
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurring_template_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Source document reference (e.g., invoice, bill)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # invoice, bill, payment, etc.
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Posting info
    posted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    posted_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    voided_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    voided_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    void_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan"
    )


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    journal_entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    debit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    credit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    # Multi-currency support
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=1, nullable=False)
    base_debit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)  # In base currency
    base_credit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)  # In base currency

    # Relationships
    journal_entry: Mapped[JournalEntry] = relationship("JournalEntry", back_populates="lines")
    account: Mapped[Account] = relationship("Account", back_populates="journal_lines")
