from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import require_admin, require_viewer
from app.models.user import User
from app.models.company import CompanySettings
from app.schemas.company import (
    CompanySettingsCreate, CompanySettingsUpdate, CompanySettingsResponse
)

router = APIRouter()


@router.get("", response_model=CompanySettingsResponse)
def get_company_settings(
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(CompanySettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Company settings not configured")
    return settings


@router.post("", response_model=CompanySettingsResponse)
def create_company_settings(
    data: CompanySettingsCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # Check if settings already exist
    result = db.execute(select(CompanySettings).limit(1))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Company settings already exist. Use PATCH to update."
        )

    settings = CompanySettings(
        **data.dict(),
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


@router.patch("", response_model=CompanySettingsResponse)
def update_company_settings(
    data: CompanySettingsUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    result = db.execute(select(CompanySettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Company settings not configured")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(settings, field, value)

    settings.updated_by_id = current_user.id
    db.commit()
    db.refresh(settings)
    return settings
