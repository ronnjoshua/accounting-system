from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Date, Boolean, Text, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import AuditMixin
import enum


class ProductType(str, enum.Enum):
    inventory = "inventory"
    non_inventory = "non_inventory"
    service = "service"


class Product(Base, AuditMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_type: Mapped[ProductType] = mapped_column(
        SQLEnum(ProductType), default=ProductType.inventory, nullable=False
    )

    # Categorization
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Pricing
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="unit", nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)

    # Inventory settings (for inventory type products)
    track_inventory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    reorder_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)

    # Accounts
    inventory_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    revenue_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    expense_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)

    # Costing method
    costing_method: Mapped[str] = mapped_column(String(20), default="weighted_average", nullable=False)  # fifo, weighted_average

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Current stock (aggregated from all warehouses)
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    average_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)


class Warehouse(Base, AuditMixin):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class MovementType(str, enum.Enum):
    purchase = "purchase"
    sale = "sale"
    transfer_in = "transfer_in"
    transfer_out = "transfer_out"
    adjustment_in = "adjustment_in"
    adjustment_out = "adjustment_out"
    return_in = "return_in"
    return_out = "return_out"


class StockMovement(Base, AuditMixin):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    movement_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)

    movement_type: Mapped[MovementType] = mapped_column(SQLEnum(MovementType), nullable=False)
    movement_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Running balance after movement
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # Source reference
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # invoice, bill, po, adjustment
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # For transfers
    destination_warehouse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouses.id"), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PurchaseOrderStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    partially_received = "partially_received"
    received = "received"
    cancelled = "cancelled"


class PurchaseOrder(Base, AuditMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)

    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        SQLEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.draft, nullable=False
    )

    # Amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    # Multi-currency
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=1, nullable=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan"
    )


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    tax_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Relationships
    purchase_order: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="lines")
