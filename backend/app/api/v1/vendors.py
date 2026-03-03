from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.ap import Vendor
from app.schemas.ap import VendorCreate, VendorUpdate, VendorResponse

router = APIRouter()


@router.get("", response_model=List[VendorResponse])
def list_vendors(
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(Vendor).where(Vendor.is_active == is_active)
    query = query.order_by(Vendor.name).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("", response_model=VendorResponse)
def create_vendor(
    data: VendorCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Vendor).where(Vendor.code == data.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Vendor code already exists")

    vendor = Vendor(
        **data.dict(),
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.patch("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: int,
    data: VendorUpdate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(vendor, field, value)

    vendor.updated_by_id = current_user.id
    db.commit()
    db.refresh(vendor)
    return vendor


@router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor.is_active = False
    vendor.updated_by_id = current_user.id
    db.commit()
    return {"message": "Vendor deactivated successfully"}
