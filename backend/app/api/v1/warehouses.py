from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.inventory import Warehouse
from app.schemas.inventory import WarehouseCreate, WarehouseUpdate, WarehouseResponse

router = APIRouter()


@router.get("", response_model=List[WarehouseResponse])
async def list_warehouses(
    is_active: bool = True,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    query = select(Warehouse).where(Warehouse.is_active == is_active)
    query = query.order_by(Warehouse.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=WarehouseResponse)
async def create_warehouse(
    data: WarehouseCreate,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Warehouse).where(Warehouse.code == data.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Warehouse code already exists")

    # If this is the first warehouse or marked as default, update others
    if data.is_default:
        result = await db.execute(select(Warehouse).where(Warehouse.is_default == True))
        for wh in result.scalars():
            wh.is_default = False

    warehouse = Warehouse(
        **data.model_dump(),
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )
    db.add(warehouse)
    await db.commit()
    await db.refresh(warehouse)
    return warehouse


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: int,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    warehouse = result.scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse


@router.patch("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    warehouse = result.scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    # Handle default flag
    if data.is_default:
        result = await db.execute(select(Warehouse).where(Warehouse.is_default == True))
        for wh in result.scalars():
            if wh.id != warehouse_id:
                wh.is_default = False

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(warehouse, field, value)

    warehouse.updated_by_id = current_user.id
    await db.commit()
    await db.refresh(warehouse)
    return warehouse


@router.delete("/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: int,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    warehouse = result.scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    warehouse.is_active = False
    warehouse.updated_by_id = current_user.id
    await db.commit()
    return {"message": "Warehouse deactivated successfully"}
