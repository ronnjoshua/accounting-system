from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Date, Boolean, Text, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import AuditMixin
import enum


class Customer(Base, AuditMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Billing Address
    billing_address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    billing_address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    billing_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    billing_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    billing_postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    billing_country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Shipping Address
    shipping_address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shipping_address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shipping_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipping_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipping_postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    shipping_country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Financial
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # AR Account for this customer
    receivable_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="customer")
    payments: Mapped[List["CustomerPayment"]] = relationship("CustomerPayment", back_populates="customer")


class InvoiceStatus(str, enum.Enum):
    # Names must match database enum values (lowercase)
    draft = "draft"
    sent = "sent"
    partially_paid = "partially_paid"
    paid = "paid"
    overdue = "overdue"
    void = "void"


class Invoice(Base, AuditMixin):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)

    invoice_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        SQLEnum(InvoiceStatus), default=InvoiceStatus.draft, nullable=False
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
    terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Journal entry reference
    journal_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)

    # Relationships
    customer: Mapped[Customer] = relationship("Customer", back_populates="invoices")
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine", back_populates="invoice", cascade="all, delete-orphan"
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    tax_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Account to credit (revenue account)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    # Relationships
    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="lines")


class CustomerPayment(Base, AuditMixin):
    __tablename__ = "customer_payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payment_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Multi-currency
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=1, nullable=False)

    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)  # cash, check, bank_transfer, etc.
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Bank account to debit
    bank_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    # Journal entry reference
    journal_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)

    # Invoice application (which invoices this payment applies to)
    invoice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("invoices.id"), nullable=True)

    # Relationships
    customer: Mapped[Customer] = relationship("Customer", back_populates="payments")


class CreditNote(Base, AuditMixin):
    __tablename__ = "credit_notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    credit_note_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    invoice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("invoices.id"), nullable=True)

    credit_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=1, nullable=False)

    journal_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)
