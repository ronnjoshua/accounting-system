from typing import Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.dependencies import require_viewer
from app.models.user import User
from app.models.accounting import Account, AccountType, AccountTypeEnum, JournalEntry, JournalEntryLine, JournalEntryStatus
from app.models.ar import Invoice, InvoiceStatus, Customer
from app.models.ap import Bill, BillStatus, Vendor
from app.services.accounting import get_trial_balance

router = APIRouter()


@router.get("/trial-balance")
async def trial_balance_report(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    return await get_trial_balance(db)


@router.get("/balance-sheet")
async def balance_sheet_report(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    # Get all accounts grouped by category
    result = await db.execute(
        select(Account, AccountType)
        .join(AccountType, Account.account_type_id == AccountType.id)
        .where(Account.is_active == True)
        .order_by(Account.code)
    )

    assets = []
    liabilities = []
    equity = []
    total_assets = Decimal("0")
    total_liabilities = Decimal("0")
    total_equity = Decimal("0")

    for account, account_type in result:
        if account.current_balance == 0:
            continue

        item = {
            "account_id": account.id,
            "account_code": account.code,
            "account_name": account.name,
            "balance": abs(account.current_balance)
        }

        if account_type.category == AccountTypeEnum.ASSET:
            assets.append(item)
            total_assets += account.current_balance
        elif account_type.category == AccountTypeEnum.LIABILITY:
            liabilities.append(item)
            total_liabilities += account.current_balance
        elif account_type.category == AccountTypeEnum.EQUITY:
            equity.append(item)
            total_equity += account.current_balance

    return {
        "as_of_date": as_of_date or date.today(),
        "assets": {
            "accounts": assets,
            "total": total_assets
        },
        "liabilities": {
            "accounts": liabilities,
            "total": total_liabilities
        },
        "equity": {
            "accounts": equity,
            "total": total_equity
        },
        "total_liabilities_and_equity": total_liabilities + total_equity,
        "is_balanced": total_assets == (total_liabilities + total_equity)
    }


@router.get("/income-statement")
async def income_statement_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Account, AccountType)
        .join(AccountType, Account.account_type_id == AccountType.id)
        .where(Account.is_active == True)
        .order_by(Account.code)
    )

    revenue = []
    expenses = []
    total_revenue = Decimal("0")
    total_expenses = Decimal("0")

    for account, account_type in result:
        if account.current_balance == 0:
            continue

        item = {
            "account_id": account.id,
            "account_code": account.code,
            "account_name": account.name,
            "balance": abs(account.current_balance)
        }

        if account_type.category == AccountTypeEnum.REVENUE:
            revenue.append(item)
            total_revenue += abs(account.current_balance)
        elif account_type.category == AccountTypeEnum.EXPENSE:
            expenses.append(item)
            total_expenses += abs(account.current_balance)

    net_income = total_revenue - total_expenses

    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date or date.today()
        },
        "revenue": {
            "accounts": revenue,
            "total": total_revenue
        },
        "expenses": {
            "accounts": expenses,
            "total": total_expenses
        },
        "net_income": net_income
    }


@router.get("/ar-aging")
async def ar_aging_report(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    today = as_of_date or date.today()

    result = await db.execute(
        select(Invoice, Customer)
        .join(Customer, Invoice.customer_id == Customer.id)
        .where(
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]),
            Invoice.balance_due > 0
        )
    )

    aging_buckets = {
        "current": [],
        "1_30": [],
        "31_60": [],
        "61_90": [],
        "over_90": []
    }

    totals = {
        "current": Decimal("0"),
        "1_30": Decimal("0"),
        "31_60": Decimal("0"),
        "61_90": Decimal("0"),
        "over_90": Decimal("0"),
        "total": Decimal("0")
    }

    for invoice, customer in result:
        days_overdue = (today - invoice.due_date).days

        item = {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "customer_name": customer.name,
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "balance_due": invoice.balance_due,
            "days_overdue": max(0, days_overdue)
        }

        if days_overdue <= 0:
            aging_buckets["current"].append(item)
            totals["current"] += invoice.balance_due
        elif days_overdue <= 30:
            aging_buckets["1_30"].append(item)
            totals["1_30"] += invoice.balance_due
        elif days_overdue <= 60:
            aging_buckets["31_60"].append(item)
            totals["31_60"] += invoice.balance_due
        elif days_overdue <= 90:
            aging_buckets["61_90"].append(item)
            totals["61_90"] += invoice.balance_due
        else:
            aging_buckets["over_90"].append(item)
            totals["over_90"] += invoice.balance_due

        totals["total"] += invoice.balance_due

    return {
        "as_of_date": today,
        "buckets": aging_buckets,
        "totals": totals
    }


@router.get("/ap-aging")
async def ap_aging_report(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    today = as_of_date or date.today()

    result = await db.execute(
        select(Bill, Vendor)
        .join(Vendor, Bill.vendor_id == Vendor.id)
        .where(
            Bill.status.in_([BillStatus.RECEIVED, BillStatus.PARTIALLY_PAID, BillStatus.OVERDUE]),
            Bill.balance_due > 0
        )
    )

    aging_buckets = {
        "current": [],
        "1_30": [],
        "31_60": [],
        "61_90": [],
        "over_90": []
    }

    totals = {
        "current": Decimal("0"),
        "1_30": Decimal("0"),
        "31_60": Decimal("0"),
        "61_90": Decimal("0"),
        "over_90": Decimal("0"),
        "total": Decimal("0")
    }

    for bill, vendor in result:
        days_overdue = (today - bill.due_date).days

        item = {
            "bill_id": bill.id,
            "bill_number": bill.bill_number,
            "vendor_name": vendor.name,
            "bill_date": bill.bill_date,
            "due_date": bill.due_date,
            "balance_due": bill.balance_due,
            "days_overdue": max(0, days_overdue)
        }

        if days_overdue <= 0:
            aging_buckets["current"].append(item)
            totals["current"] += bill.balance_due
        elif days_overdue <= 30:
            aging_buckets["1_30"].append(item)
            totals["1_30"] += bill.balance_due
        elif days_overdue <= 60:
            aging_buckets["31_60"].append(item)
            totals["31_60"] += bill.balance_due
        elif days_overdue <= 90:
            aging_buckets["61_90"].append(item)
            totals["61_90"] += bill.balance_due
        else:
            aging_buckets["over_90"].append(item)
            totals["over_90"] += bill.balance_due

        totals["total"] += bill.balance_due

    return {
        "as_of_date": today,
        "buckets": aging_buckets,
        "totals": totals
    }


@router.get("/dashboard")
async def dashboard_summary(
    current_user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db)
):
    # Total AR
    ar_result = await db.execute(
        select(func.sum(Invoice.balance_due))
        .where(Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]))
    )
    total_ar = ar_result.scalar() or Decimal("0")

    # Total AP
    ap_result = await db.execute(
        select(func.sum(Bill.balance_due))
        .where(Bill.status.in_([BillStatus.RECEIVED, BillStatus.PARTIALLY_PAID, BillStatus.OVERDUE]))
    )
    total_ap = ap_result.scalar() or Decimal("0")

    # Count of open invoices
    invoice_count = await db.execute(
        select(func.count(Invoice.id))
        .where(Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]))
    )
    open_invoices = invoice_count.scalar() or 0

    # Count of open bills
    bill_count = await db.execute(
        select(func.count(Bill.id))
        .where(Bill.status.in_([BillStatus.RECEIVED, BillStatus.PARTIALLY_PAID]))
    )
    open_bills = bill_count.scalar() or 0

    # Overdue invoices
    today = date.today()
    overdue_invoices_result = await db.execute(
        select(func.count(Invoice.id))
        .where(
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]),
            Invoice.due_date < today
        )
    )
    overdue_invoices = overdue_invoices_result.scalar() or 0

    # Overdue bills
    overdue_bills_result = await db.execute(
        select(func.count(Bill.id))
        .where(
            Bill.status.in_([BillStatus.RECEIVED, BillStatus.PARTIALLY_PAID]),
            Bill.due_date < today
        )
    )
    overdue_bills = overdue_bills_result.scalar() or 0

    return {
        "accounts_receivable": {
            "total": total_ar,
            "open_invoices": open_invoices,
            "overdue_invoices": overdue_invoices
        },
        "accounts_payable": {
            "total": total_ap,
            "open_bills": open_bills,
            "overdue_bills": overdue_bills
        },
        "net_position": total_ar - total_ap
    }
