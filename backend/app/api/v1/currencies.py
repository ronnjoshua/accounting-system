from typing import Optional, List
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import require_viewer, require_manager
from app.models.user import User
from app.models.accounting import Currency, ExchangeRate

router = APIRouter()


@router.get("")
def list_currencies(
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """List all currencies"""
    result = db.execute(select(Currency).order_by(Currency.code))
    currencies = result.scalars().all()
    return [
        {
            "code": c.code,
            "name": c.name,
            "symbol": c.symbol,
            "decimal_places": c.decimal_places,
            "is_active": c.is_active
        }
        for c in currencies
    ]


@router.get("/{code}")
def get_currency(
    code: str,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get a specific currency"""
    currency = db.execute(
        select(Currency).where(Currency.code == code.upper())
    ).scalar_one_or_none()

    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    return {
        "code": currency.code,
        "name": currency.name,
        "symbol": currency.symbol,
        "decimal_places": currency.decimal_places,
        "is_active": currency.is_active
    }


@router.post("")
def create_currency(
    data: dict,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """Create a new currency"""
    existing = db.execute(
        select(Currency).where(Currency.code == data["code"].upper())
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Currency already exists")

    currency = Currency(
        code=data["code"].upper(),
        name=data["name"],
        symbol=data.get("symbol", data["code"]),
        decimal_places=data.get("decimal_places", 2),
        is_active=data.get("is_active", True)
    )

    db.add(currency)
    db.flush()

    return {
        "code": currency.code,
        "name": currency.name,
        "symbol": currency.symbol,
        "decimal_places": currency.decimal_places,
        "is_active": currency.is_active
    }


@router.patch("/{code}")
def update_currency(
    code: str,
    data: dict,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """Update a currency"""
    currency = db.execute(
        select(Currency).where(Currency.code == code.upper())
    ).scalar_one_or_none()

    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    if "name" in data:
        currency.name = data["name"]
    if "symbol" in data:
        currency.symbol = data["symbol"]
    if "decimal_places" in data:
        currency.decimal_places = data["decimal_places"]
    if "is_active" in data:
        currency.is_active = data["is_active"]

    db.flush()

    return {
        "code": currency.code,
        "name": currency.name,
        "symbol": currency.symbol,
        "decimal_places": currency.decimal_places,
        "is_active": currency.is_active
    }


@router.get("/exchange-rates")
def get_exchange_rates(
    base_currency: str = "USD",
    rate_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get exchange rates for a base currency"""
    query = select(ExchangeRate).where(
        ExchangeRate.from_currency_code == base_currency.upper()
    )

    if rate_date:
        query = query.where(ExchangeRate.effective_date <= rate_date)

    query = query.order_by(ExchangeRate.effective_date.desc())

    result = db.execute(query)
    rates = result.scalars().all()

    # Group by to_currency, keeping only the most recent rate
    latest_rates = {}
    for rate in rates:
        if rate.to_currency_code not in latest_rates:
            latest_rates[rate.to_currency_code] = {
                "from_currency": rate.from_currency_code,
                "to_currency": rate.to_currency_code,
                "rate": float(rate.rate),
                "effective_date": rate.effective_date.isoformat()
            }

    from datetime import date as date_type
    return {
        "base_currency": base_currency.upper(),
        "date": (rate_date or date_type.today()).isoformat() if rate_date else None,
        "rates": list(latest_rates.values())
    }
