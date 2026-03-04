from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.inventory import ProductType, MovementType, PurchaseOrderStatus


class ProductBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    product_type: ProductType = ProductType.inventory
    category: Optional[str] = None
    brand: Optional[str] = None
    unit_of_measure: str = "unit"
    purchase_price: Decimal = Decimal("0")
    selling_price: Decimal = Decimal("0")
    track_inventory: bool = True
    reorder_point: Decimal = Decimal("0")
    reorder_quantity: Decimal = Decimal("0")
    inventory_account_id: Optional[int] = None
    revenue_account_id: Optional[int] = None
    expense_account_id: Optional[int] = None
    costing_method: str = "weighted_average"


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    product_type: Optional[ProductType] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    unit_of_measure: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    track_inventory: Optional[bool] = None
    reorder_point: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    inventory_account_id: Optional[int] = None
    revenue_account_id: Optional[int] = None
    expense_account_id: Optional[int] = None
    costing_method: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    quantity_on_hand: Decimal
    average_cost: Decimal
    created_at: datetime
    updated_at: datetime


class WarehouseBase(BaseModel):
    code: str
    name: str
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class WarehouseCreate(WarehouseBase):
    is_default: bool = False


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class StockMovementCreate(BaseModel):
    product_id: int
    warehouse_id: int
    movement_type: MovementType
    movement_date: date
    quantity: Decimal
    unit_cost: Decimal
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    destination_warehouse_id: Optional[int] = None
    notes: Optional[str] = None


class StockAdjustmentCreate(BaseModel):
    product_id: int
    warehouse_id: int
    adjustment_date: date
    adjustment_quantity: Decimal
    unit_cost: Decimal
    reason: str


class StockTransferCreate(BaseModel):
    product_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    transfer_date: date
    quantity: Decimal
    notes: Optional[str] = None


class WarehouseStockItem(BaseModel):
    warehouse_id: int
    warehouse_name: str
    quantity: Decimal


class ProductStockResponse(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    total_quantity: Decimal
    average_cost: Decimal
    total_value: Decimal
    warehouse_breakdown: List[WarehouseStockItem]


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movement_number: str
    product_id: int
    warehouse_id: int
    movement_type: MovementType
    movement_date: date
    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    quantity_after: Decimal
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    destination_warehouse_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime


class PurchaseOrderLineCreate(BaseModel):
    product_id: int
    description: Optional[str] = None
    quantity_ordered: Decimal
    unit_price: Decimal
    tax_percent: Decimal = Decimal("0")


class PurchaseOrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    description: Optional[str] = None
    quantity_ordered: Decimal
    quantity_received: Decimal
    unit_price: Decimal
    tax_percent: Decimal
    line_total: Decimal


class PurchaseOrderCreate(BaseModel):
    vendor_id: int
    warehouse_id: int
    order_date: date
    expected_date: Optional[date] = None
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("1")
    notes: Optional[str] = None
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderUpdate(BaseModel):
    expected_date: Optional[date] = None
    notes: Optional[str] = None
    lines: Optional[List[PurchaseOrderLineCreate]] = None


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    po_number: str
    vendor_id: int
    warehouse_id: int
    order_date: date
    expected_date: Optional[date] = None
    status: PurchaseOrderStatus
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    currency_code: str
    exchange_rate: Decimal
    notes: Optional[str] = None
    lines: List[PurchaseOrderLineResponse] = []
    created_at: datetime
    updated_at: datetime
