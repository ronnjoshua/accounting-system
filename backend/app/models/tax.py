from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Date, Boolean, Text, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import AuditMixin
import enum


class TaxType(str, enum.Enum):
    sales_tax = "sales_tax"
    vat = "vat"
    gst = "gst"
    withholding = "withholding"
    excise = "excise"
    other = "other"


class TaxRate(Base, AuditMixin):
    """Tax rate configuration"""
    __tablename__ = "tax_rates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tax_type: Mapped[TaxType] = mapped_column(SQLEnum(TaxType), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)  # Percentage rate

    # Accounts for tax liability/receivable
    tax_collected_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    tax_paid_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)

    # Jurisdiction
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_compound: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Calculated on top of other taxes


class TaxExemption(Base, AuditMixin):
    """Tax exemption certificates"""
    __tablename__ = "tax_exemptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Entity that has exemption
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # customer, vendor
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    certificate_number: Mapped[str] = mapped_column(String(100), nullable=False)
    exemption_reason: Mapped[str] = mapped_column(String(255), nullable=False)

    # Which tax rates this exemption applies to (null = all)
    tax_rate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tax_rates.id"), nullable=True)

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class TaxPeriod(Base, AuditMixin):
    """Tax filing periods"""
    __tablename__ = "tax_periods"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_type: Mapped[TaxType] = mapped_column(SQLEnum(TaxType), nullable=False)

    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Calculated amounts
    tax_collected: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    tax_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    net_tax_due: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    is_filed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    filed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    filed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
