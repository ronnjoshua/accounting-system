from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.inventory import Product, ProductType
from app.schemas.inventory import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter()


@router.get("", response_model=List[ProductResponse])
def list_products(
    product_type: Optional[ProductType] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(Product).where(Product.is_active == is_active)

    if product_type:
        query = query.where(Product.product_type == product_type)

    query = query.order_by(Product.name).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ProductResponse)
def create_product(
    data: ProductCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Product).where(Product.code == data.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Product code already exists")

    product = Product(
        **data.dict(),
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(product, field, value)

    product.updated_by_id = current_user.id
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.quantity_on_hand != 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product with inventory on hand"
        )

    product.is_active = False
    product.updated_by_id = current_user.id
    db.commit()
    return {"message": "Product deactivated successfully"}
