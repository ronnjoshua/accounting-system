from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.inventory import Product, Warehouse, StockMovement, MovementType
from app.schemas.inventory import (
    StockMovementCreate, StockMovementResponse,
    StockAdjustmentCreate, StockTransferCreate,
    ProductStockResponse
)

router = APIRouter()


def get_next_movement_number(db: Session) -> str:
    result = db.execute(select(func.count(StockMovement.id)))
    count = result.scalar() or 0
    return f"SM-{count + 1:06d}"


def update_product_stock(db: Session, product_id: int):
    """Recalculate product's total stock across all warehouses"""
    result = db.execute(
        select(func.sum(StockMovement.quantity))
        .where(StockMovement.product_id == product_id)
        .where(StockMovement.movement_type.in_([
            MovementType.PURCHASE, MovementType.TRANSFER_IN,
            MovementType.ADJUSTMENT_IN, MovementType.RETURN_IN
        ]))
    )
    total_in = result.scalar() or Decimal("0")

    result = db.execute(
        select(func.sum(StockMovement.quantity))
        .where(StockMovement.product_id == product_id)
        .where(StockMovement.movement_type.in_([
            MovementType.SALE, MovementType.TRANSFER_OUT,
            MovementType.ADJUSTMENT_OUT, MovementType.RETURN_OUT
        ]))
    )
    total_out = result.scalar() or Decimal("0")

    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one()
    product.quantity_on_hand = total_in - total_out


def calculate_average_cost(db: Session, product_id: int) -> Decimal:
    """Calculate weighted average cost for a product"""
    result = db.execute(
        select(
            func.sum(StockMovement.total_cost),
            func.sum(StockMovement.quantity)
        )
        .where(StockMovement.product_id == product_id)
        .where(StockMovement.movement_type.in_([
            MovementType.PURCHASE, MovementType.ADJUSTMENT_IN
        ]))
    )
    row = result.one()
    total_cost = row[0] or Decimal("0")
    total_qty = row[1] or Decimal("1")

    if total_qty <= 0:
        return Decimal("0")
    return total_cost / total_qty


@router.get("", response_model=List[StockMovementResponse])
def list_stock_movements(
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    movement_type: Optional[MovementType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(StockMovement)

    if product_id:
        query = query.where(StockMovement.product_id == product_id)
    if warehouse_id:
        query = query.where(StockMovement.warehouse_id == warehouse_id)
    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type)
    if start_date:
        query = query.where(StockMovement.movement_date >= start_date)
    if end_date:
        query = query.where(StockMovement.movement_date <= end_date)

    query = query.order_by(StockMovement.movement_date.desc(), StockMovement.id.desc())
    query = query.offset(skip).limit(limit)

    result = db.execute(query)
    return result.scalars().all()


@router.post("", response_model=StockMovementResponse)
def create_stock_movement(
    data: StockMovementCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    # Validate product
    product = db.execute(select(Product).where(Product.id == data.product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate warehouse
    warehouse = db.execute(select(Warehouse).where(Warehouse.id == data.warehouse_id)).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    movement_number = get_next_movement_number(db)
    total_cost = data.quantity * data.unit_cost

    # Get current quantity
    current_qty = product.quantity_on_hand

    # For outbound movements, check if we have enough stock
    if data.movement_type in [MovementType.SALE, MovementType.TRANSFER_OUT,
                               MovementType.ADJUSTMENT_OUT, MovementType.RETURN_OUT]:
        if data.quantity > current_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {current_qty}, Requested: {data.quantity}"
            )
        quantity_after = current_qty - data.quantity
    else:
        quantity_after = current_qty + data.quantity

    movement = StockMovement(
        movement_number=movement_number,
        product_id=data.product_id,
        warehouse_id=data.warehouse_id,
        movement_type=data.movement_type,
        movement_date=data.movement_date,
        quantity=data.quantity,
        unit_cost=data.unit_cost,
        total_cost=total_cost,
        quantity_after=quantity_after,
        source_type=data.source_type,
        source_id=data.source_id,
        notes=data.notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(movement)

    # Update product stock
    update_product_stock(db, data.product_id)
    product.average_cost = calculate_average_cost(db, data.product_id)

    db.commit()
    db.refresh(movement)
    return movement


@router.post("/adjustment", response_model=StockMovementResponse)
def create_stock_adjustment(
    data: StockAdjustmentCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    """Create a stock adjustment (increase or decrease)"""
    # Validate product
    product = db.execute(select(Product).where(Product.id == data.product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate warehouse
    warehouse = db.execute(select(Warehouse).where(Warehouse.id == data.warehouse_id)).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    movement_number = get_next_movement_number(db)

    # Determine movement type based on adjustment
    if data.adjustment_quantity >= 0:
        movement_type = MovementType.ADJUSTMENT_IN
        quantity = data.adjustment_quantity
    else:
        movement_type = MovementType.ADJUSTMENT_OUT
        quantity = abs(data.adjustment_quantity)
        # Check if we have enough stock
        if quantity > product.quantity_on_hand:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reduce stock below zero. Current: {product.quantity_on_hand}"
            )

    total_cost = quantity * data.unit_cost

    if movement_type == MovementType.ADJUSTMENT_IN:
        quantity_after = product.quantity_on_hand + quantity
    else:
        quantity_after = product.quantity_on_hand - quantity

    movement = StockMovement(
        movement_number=movement_number,
        product_id=data.product_id,
        warehouse_id=data.warehouse_id,
        movement_type=movement_type,
        movement_date=data.adjustment_date,
        quantity=quantity,
        unit_cost=data.unit_cost,
        total_cost=total_cost,
        quantity_after=quantity_after,
        source_type="adjustment",
        notes=data.reason,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(movement)

    # Update product stock
    update_product_stock(db, data.product_id)
    product.average_cost = calculate_average_cost(db, data.product_id)

    db.commit()
    db.refresh(movement)
    return movement


@router.post("/transfer", response_model=List[StockMovementResponse])
def create_stock_transfer(
    data: StockTransferCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    """Transfer stock between warehouses"""
    # Validate product
    product = db.execute(select(Product).where(Product.id == data.product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate source warehouse
    source_warehouse = db.execute(
        select(Warehouse).where(Warehouse.id == data.from_warehouse_id)
    ).scalar_one_or_none()
    if not source_warehouse:
        raise HTTPException(status_code=404, detail="Source warehouse not found")

    # Validate destination warehouse
    dest_warehouse = db.execute(
        select(Warehouse).where(Warehouse.id == data.to_warehouse_id)
    ).scalar_one_or_none()
    if not dest_warehouse:
        raise HTTPException(status_code=404, detail="Destination warehouse not found")

    if data.from_warehouse_id == data.to_warehouse_id:
        raise HTTPException(status_code=400, detail="Source and destination warehouses must be different")

    # Check stock availability
    if data.quantity > product.quantity_on_hand:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {product.quantity_on_hand}"
        )

    total_cost = data.quantity * (product.average_cost or product.purchase_price)

    # Create transfer out movement
    out_number = get_next_movement_number(db)
    transfer_out = StockMovement(
        movement_number=out_number,
        product_id=data.product_id,
        warehouse_id=data.from_warehouse_id,
        movement_type=MovementType.TRANSFER_OUT,
        movement_date=data.transfer_date,
        quantity=data.quantity,
        unit_cost=product.average_cost or product.purchase_price,
        total_cost=total_cost,
        quantity_after=product.quantity_on_hand - data.quantity,
        source_type="transfer",
        destination_warehouse_id=data.to_warehouse_id,
        notes=data.notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )
    db.add(transfer_out)

    # Create transfer in movement
    in_number = get_next_movement_number(db)
    transfer_in = StockMovement(
        movement_number=in_number,
        product_id=data.product_id,
        warehouse_id=data.to_warehouse_id,
        movement_type=MovementType.TRANSFER_IN,
        movement_date=data.transfer_date,
        quantity=data.quantity,
        unit_cost=product.average_cost or product.purchase_price,
        total_cost=total_cost,
        quantity_after=product.quantity_on_hand,  # Will be the same after in/out
        source_type="transfer",
        destination_warehouse_id=data.from_warehouse_id,
        notes=data.notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )
    db.add(transfer_in)

    db.commit()
    db.refresh(transfer_out)
    db.refresh(transfer_in)

    return [transfer_out, transfer_in]


@router.get("/product/{product_id}", response_model=ProductStockResponse)
def get_product_stock(
    product_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get stock summary for a product across all warehouses"""
    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get stock by warehouse
    warehouse_stock = []
    warehouses = db.execute(select(Warehouse).where(Warehouse.is_active == True)).scalars().all()

    for warehouse in warehouses:
        # Calculate stock for this warehouse
        result = db.execute(
            select(func.sum(StockMovement.quantity))
            .where(StockMovement.product_id == product_id)
            .where(StockMovement.warehouse_id == warehouse.id)
            .where(StockMovement.movement_type.in_([
                MovementType.PURCHASE, MovementType.TRANSFER_IN,
                MovementType.ADJUSTMENT_IN, MovementType.RETURN_IN
            ]))
        )
        total_in = result.scalar() or Decimal("0")

        result = db.execute(
            select(func.sum(StockMovement.quantity))
            .where(StockMovement.product_id == product_id)
            .where(StockMovement.warehouse_id == warehouse.id)
            .where(StockMovement.movement_type.in_([
                MovementType.SALE, MovementType.TRANSFER_OUT,
                MovementType.ADJUSTMENT_OUT, MovementType.RETURN_OUT
            ]))
        )
        total_out = result.scalar() or Decimal("0")

        qty = total_in - total_out
        if qty != 0:
            warehouse_stock.append({
                "warehouse_id": warehouse.id,
                "warehouse_name": warehouse.name,
                "quantity": qty
            })

    return {
        "product_id": product.id,
        "product_code": product.code,
        "product_name": product.name,
        "total_quantity": product.quantity_on_hand,
        "average_cost": product.average_cost,
        "total_value": product.quantity_on_hand * product.average_cost,
        "warehouse_breakdown": warehouse_stock
    }


@router.get("/{movement_id}", response_model=StockMovementResponse)
def get_stock_movement(
    movement_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(StockMovement).where(StockMovement.id == movement_id))
    movement = result.scalar_one_or_none()
    if not movement:
        raise HTTPException(status_code=404, detail="Stock movement not found")
    return movement
