from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.inventory import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from app.schemas.inventory import (
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse
)

router = APIRouter()


def get_next_po_number(db: Session) -> str:
    result = db.execute(select(func.count(PurchaseOrder.id)))
    count = result.scalar() or 0
    return f"PO-{count + 1:06d}"


@router.get("", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(
    status: Optional[PurchaseOrderStatus] = None,
    vendor_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(PurchaseOrder)

    if status:
        query = query.where(PurchaseOrder.status == status)
    if vendor_id:
        query = query.where(PurchaseOrder.vendor_id == vendor_id)
    if start_date:
        query = query.where(PurchaseOrder.order_date >= start_date)
    if end_date:
        query = query.where(PurchaseOrder.order_date <= end_date)

    query = query.order_by(PurchaseOrder.order_date.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("", response_model=PurchaseOrderResponse)
def create_purchase_order(
    data: PurchaseOrderCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    po_number = get_next_po_number(db)

    subtotal = Decimal("0")
    tax_amount = Decimal("0")

    po = PurchaseOrder(
        po_number=po_number,
        vendor_id=data.vendor_id,
        warehouse_id=data.warehouse_id,
        order_date=data.order_date,
        expected_date=data.expected_date,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        notes=data.notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    for line_data in data.lines:
        line_subtotal = line_data.quantity_ordered * line_data.unit_price
        line_tax = line_subtotal * (line_data.tax_percent / 100)
        line_total = line_subtotal + line_tax

        line = PurchaseOrderLine(
            product_id=line_data.product_id,
            description=line_data.description,
            quantity_ordered=line_data.quantity_ordered,
            unit_price=line_data.unit_price,
            tax_percent=line_data.tax_percent,
            line_total=line_total
        )
        po.lines.append(line)

        subtotal += line_subtotal
        tax_amount += line_tax

    po.subtotal = subtotal
    po.tax_amount = tax_amount
    po.total = subtotal + tax_amount

    db.add(po)
    db.commit()
    db.refresh(po)
    return po


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    po_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@router.patch("/{po_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    po_id: int,
    data: PurchaseOrderUpdate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if po.status not in [PurchaseOrderStatus.draft]:
        raise HTTPException(
            status_code=400,
            detail="Only draft purchase orders can be modified"
        )

    if data.lines is not None:
        for line in po.lines:
            db.delete(line)

        subtotal = Decimal("0")
        tax_amount = Decimal("0")

        for line_data in data.lines:
            line_subtotal = line_data.quantity_ordered * line_data.unit_price
            line_tax = line_subtotal * (line_data.tax_percent / 100)
            line_total = line_subtotal + line_tax

            line = PurchaseOrderLine(
                purchase_order_id=po.id,
                product_id=line_data.product_id,
                description=line_data.description,
                quantity_ordered=line_data.quantity_ordered,
                unit_price=line_data.unit_price,
                tax_percent=line_data.tax_percent,
                line_total=line_total
            )
            db.add(line)

            subtotal += line_subtotal
            tax_amount += line_tax

        po.subtotal = subtotal
        po.tax_amount = tax_amount
        po.total = subtotal + tax_amount

    update_data = data.dict(exclude_unset=True, exclude={"lines"})
    for field, value in update_data.items():
        setattr(po, field, value)

    po.updated_by_id = current_user.id
    db.commit()
    db.refresh(po)
    return po


@router.post("/{po_id}/send", response_model=PurchaseOrderResponse)
def send_purchase_order(
    po_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if po.status != PurchaseOrderStatus.draft:
        raise HTTPException(status_code=400, detail="Only draft POs can be sent")

    po.status = PurchaseOrderStatus.sent
    po.updated_by_id = current_user.id
    db.commit()
    db.refresh(po)
    return po


@router.post("/{po_id}/cancel", response_model=PurchaseOrderResponse)
def cancel_purchase_order(
    po_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if po.status in [PurchaseOrderStatus.received, PurchaseOrderStatus.cancelled]:
        raise HTTPException(status_code=400, detail="Cannot cancel this PO")

    po.status = PurchaseOrderStatus.cancelled
    po.updated_by_id = current_user.id
    db.commit()
    db.refresh(po)
    return po
