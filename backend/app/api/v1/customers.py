from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.ar import Customer
from app.schemas.ar import CustomerCreate, CustomerUpdate, CustomerResponse

router = APIRouter()


def get_next_customer_code(db: Session) -> str:
    result = db.execute(select(func.count(Customer.id)))
    count = result.scalar() or 0
    return f"CUST-{count + 1:05d}"


@router.get("", response_model=List[CustomerResponse])
def list_customers(
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(Customer).where(Customer.is_active == is_active)
    query = query.order_by(Customer.name).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("", response_model=CustomerResponse)
def create_customer(
    data: CustomerCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    # Check if code already exists
    result = db.execute(select(Customer).where(Customer.code == data.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Customer code already exists")

    customer = Customer(
        **data.dict(),
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(customer, field, value)

    customer.updated_by_id = current_user.id
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Soft delete
    customer.is_active = False
    customer.updated_by_id = current_user.id
    db.commit()
    return {"message": "Customer deactivated successfully"}
