from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Date, Boolean, Text, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import AuditMixin
import enum


class Vendor(Base, AuditMixin):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Financial
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # AP Account for this vendor
    payable_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)

    # Bank details for payments
    bank_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_routing_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    bills: Mapped[List["Bill"]] = relationship("Bill", back_populates="vendor")
    payments: Mapped[List["VendorPayment"]] = relationship("VendorPayment", back_populates="vendor")


class BillStatus(str, enum.Enum):
    # Names must match database enum values (lowercase)
    draft = "draft"
    received = "received"
    partially_paid = "partially_paid"
    paid = "paid"
    overdue = "overdue"
    void = "void"


class Bill(Base, AuditMixin):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bill_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vendor_bill_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Vendor's invoice number
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)

    bill_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[BillStatus] = mapped_column(
        SQLEnum(BillStatus), default=BillStatus.draft, nullable=False
    )

    # Amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    balance_due: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    # Multi-currency
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=1, nullable=False)

    # References
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Purchase order reference
    purchase_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True)

    # Journal entry reference
    journal_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)

    # Relationships
    vendor: Mapped[Vendor] = relationship("Vendor", back_populates="bills")
    lines: Mapped[List["BillLine"]] = relationship(
        "BillLine", back_populates="bill", cascade="all, delete-orphan"
    )


class BillLine(Base):
    __tablename__ = "bill_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    tax_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Account to debit (expense account)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    # Relationships
    bill: Mapped[Bill] = relationship("Bill", back_populates="lines")


class VendorPayment(Base, AuditMixin):
    __tablename__ = "vendor_payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payment_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Multi-currency
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=1, nullable=False)

    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Bank account to credit
    bank_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    # Journal entry reference
    journal_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)

    # Bill application
    bill_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bills.id"), nullable=True)

    # Relationships
    vendor: Mapped[Vendor] = relationship("Vendor", back_populates="payments")


class DebitNote(Base, AuditMixin):
    __tablename__ = "debit_notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    debit_note_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    bill_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bills.id"), nullable=True)

    debit_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=1, nullable=False)

    journal_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)
