from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Integer, Date, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import AuditMixin


class CompanySettings(Base, AuditMixin):
    __tablename__ = "company_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Contact
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Fiscal Settings
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-12
    fiscal_year_start_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)   # 1-31
    base_currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Logo (Cloudinary URL)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class FiscalPeriod(Base, AuditMixin):
    __tablename__ = "fiscal_periods"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "FY 2024", "Q1 2024"
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # year, quarter, month
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    closed_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
