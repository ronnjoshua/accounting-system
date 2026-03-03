from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class CompanySettingsBase(BaseModel):
    company_name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    fiscal_year_start_month: int = 1
    fiscal_year_start_day: int = 1
    base_currency_code: str = "USD"


class CompanySettingsCreate(CompanySettingsBase):
    pass


class CompanySettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    fiscal_year_start_month: Optional[int] = None
    fiscal_year_start_day: Optional[int] = None
    base_currency_code: Optional[str] = None


class CompanySettingsResponse(CompanySettingsBase):
    id: int
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
