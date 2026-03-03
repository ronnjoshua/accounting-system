from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.accounting import Account, AccountType, AccountTypeEnum
from app.schemas.accounting import (
    AccountCreate, AccountUpdate, AccountResponse, AccountTypeResponse
)

router = APIRouter()


@router.get("/types", response_model=List[AccountTypeResponse])
async def list_account_types(
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AccountType))
    return result.scalars().all()


@router.get("", response_model=List[AccountResponse])
async def list_accounts(
    category: Optional[AccountTypeEnum] = None,
    is_active: bool = True,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    query = select(Account).where(Account.is_active == is_active)

    if category:
        query = query.join(AccountType).where(AccountType.category == category)

    query = query.order_by(Account.code)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=AccountResponse)
async def create_account(
    data: AccountCreate,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    # Check if code already exists
    result = await db.execute(select(Account).where(Account.code == data.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Account code already exists")

    # Verify account type exists
    result = await db.execute(
        select(AccountType).where(AccountType.id == data.account_type_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invalid account type")

    # Verify parent if provided
    if data.parent_id:
        result = await db.execute(
            select(Account).where(Account.id == data.parent_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invalid parent account")

    account = Account(
        **data.model_dump(),
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    data: AccountUpdate,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.is_system:
        raise HTTPException(
            status_code=400,
            detail="System accounts cannot be modified"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)

    account.updated_by_id = current_user.id
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.is_system:
        raise HTTPException(
            status_code=400,
            detail="System accounts cannot be deleted"
        )

    if account.current_balance != 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete account with non-zero balance"
        )

    # Check for child accounts
    result = await db.execute(
        select(Account).where(Account.parent_id == account_id)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete account with child accounts"
        )

    await db.delete(account)
    await db.commit()
    return {"message": "Account deleted successfully"}
