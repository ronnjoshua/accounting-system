from typing import Optional
from datetime import date
from decimal import Decimal
import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.dependencies import require_viewer
from app.models.user import User
from app.models.accounting import Account, AccountType, AccountTypeEnum, JournalEntry, JournalEntryLine, JournalEntryStatus
from app.models.ar import Invoice, InvoiceStatus, Customer
from app.models.ap import Bill, BillStatus, Vendor
from app.services.accounting import get_trial_balance

router = APIRouter()


def generate_csv(headers: list, rows: list, filename: str) -> StreamingResponse:
    """Generate a CSV file for download"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/trial-balance")
def trial_balance_report(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    return get_trial_balance(db)


@router.get("/balance-sheet")
def balance_sheet_report(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(
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
def income_statement_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(
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
def ar_aging_report(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    today = as_of_date or date.today()

    result = db.execute(
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
def ap_aging_report(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    today = as_of_date or date.today()

    result = db.execute(
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
def dashboard_summary(
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    # Total AR - use enum members directly (not .value)
    ar_result = db.execute(
        select(func.sum(Invoice.balance_due))
        .where(Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]))
    )
    total_ar = ar_result.scalar() or Decimal("0")

    # Total AP
    ap_result = db.execute(
        select(func.sum(Bill.balance_due))
        .where(Bill.status.in_([BillStatus.RECEIVED, BillStatus.PARTIALLY_PAID, BillStatus.OVERDUE]))
    )
    total_ap = ap_result.scalar() or Decimal("0")

    # Count of open invoices
    invoice_count = db.execute(
        select(func.count(Invoice.id))
        .where(Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]))
    )
    open_invoices = invoice_count.scalar() or 0

    # Count of open bills
    bill_count = db.execute(
        select(func.count(Bill.id))
        .where(Bill.status.in_([BillStatus.RECEIVED, BillStatus.PARTIALLY_PAID]))
    )
    open_bills = bill_count.scalar() or 0

    # Overdue invoices
    today = date.today()
    overdue_invoices_result = db.execute(
        select(func.count(Invoice.id))
        .where(
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]),
            Invoice.due_date < today
        )
    )
    overdue_invoices = overdue_invoices_result.scalar() or 0

    # Overdue bills
    overdue_bills_result = db.execute(
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


@router.get("/general-ledger")
def general_ledger_report(
    account_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """General Ledger report showing all transactions by account"""
    query = (
        select(JournalEntryLine, JournalEntry, Account)
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .where(JournalEntry.status == JournalEntryStatus.POSTED)
    )

    if account_id:
        query = query.where(JournalEntryLine.account_id == account_id)
    if start_date:
        query = query.where(JournalEntry.entry_date >= start_date)
    if end_date:
        query = query.where(JournalEntry.entry_date <= end_date)

    query = query.order_by(Account.code, JournalEntry.entry_date, JournalEntry.id)

    result = db.execute(query)

    # Group by account
    accounts = {}
    for line, entry, account in result:
        acc_id = account.id
        if acc_id not in accounts:
            accounts[acc_id] = {
                "account_id": account.id,
                "account_code": account.code,
                "account_name": account.name,
                "transactions": [],
                "total_debits": Decimal("0"),
                "total_credits": Decimal("0"),
                "net_change": Decimal("0")
            }

        accounts[acc_id]["transactions"].append({
            "entry_id": entry.id,
            "entry_number": entry.entry_number,
            "entry_date": entry.entry_date.isoformat(),
            "description": line.description or entry.description,
            "reference": entry.reference,
            "debit": float(line.debit),
            "credit": float(line.credit)
        })

        accounts[acc_id]["total_debits"] += line.debit
        accounts[acc_id]["total_credits"] += line.credit

    # Calculate net change
    for acc_id in accounts:
        accounts[acc_id]["net_change"] = accounts[acc_id]["total_debits"] - accounts[acc_id]["total_credits"]
        accounts[acc_id]["total_debits"] = float(accounts[acc_id]["total_debits"])
        accounts[acc_id]["total_credits"] = float(accounts[acc_id]["total_credits"])
        accounts[acc_id]["net_change"] = float(accounts[acc_id]["net_change"])

    return {
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else date.today().isoformat()
        },
        "accounts": list(accounts.values())
    }


@router.get("/cash-flow")
def cash_flow_statement(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Cash Flow Statement using indirect method"""
    end = end_date or date.today()

    # Get all cash/bank accounts (typically start with 1000 or 1100)
    cash_accounts = db.execute(
        select(Account)
        .where(Account.code.like("1%"))
        .where(Account.is_active == True)
    ).scalars().all()

    cash_account_ids = [a.id for a in cash_accounts if a.code.startswith(("100", "101", "102", "110"))]

    if not cash_account_ids:
        # Fallback: use all asset accounts starting with 1
        cash_account_ids = [a.id for a in cash_accounts]

    # Net Income from Income Statement
    result = db.execute(
        select(Account, AccountType)
        .join(AccountType, Account.account_type_id == AccountType.id)
        .where(Account.is_active == True)
    )

    total_revenue = Decimal("0")
    total_expenses = Decimal("0")

    for account, account_type in result:
        if account_type.category == AccountTypeEnum.REVENUE:
            total_revenue += abs(account.current_balance)
        elif account_type.category == AccountTypeEnum.EXPENSE:
            total_expenses += abs(account.current_balance)

    net_income = total_revenue - total_expenses

    # Operating Activities (simplified - cash from operations)
    # Get cash transactions related to AR (customer payments)
    from app.models.ar import CustomerPayment
    from app.models.ap import VendorPayment

    customer_payments_query = select(func.sum(CustomerPayment.amount))
    if start_date:
        customer_payments_query = customer_payments_query.where(CustomerPayment.payment_date >= start_date)
    if end_date:
        customer_payments_query = customer_payments_query.where(CustomerPayment.payment_date <= end)

    customer_payments = db.execute(customer_payments_query).scalar() or Decimal("0")

    # Get cash transactions related to AP (vendor payments)
    vendor_payments_query = select(func.sum(VendorPayment.amount))
    if start_date:
        vendor_payments_query = vendor_payments_query.where(VendorPayment.payment_date >= start_date)
    if end_date:
        vendor_payments_query = vendor_payments_query.where(VendorPayment.payment_date <= end)

    vendor_payments = db.execute(vendor_payments_query).scalar() or Decimal("0")

    operating_cash_flow = customer_payments - vendor_payments

    # For investing and financing, we'd need more detailed tracking
    # For now, we'll show a simplified version

    # Get total change in cash accounts
    cash_change_query = (
        select(func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit))
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(
            JournalEntryLine.account_id.in_(cash_account_ids),
            JournalEntry.status == JournalEntryStatus.POSTED
        )
    )
    if start_date:
        cash_change_query = cash_change_query.where(JournalEntry.entry_date >= start_date)
    if end_date:
        cash_change_query = cash_change_query.where(JournalEntry.entry_date <= end)

    total_cash_change = db.execute(cash_change_query).scalar() or Decimal("0")

    # Calculate ending cash balance
    ending_cash = Decimal("0")
    for acc_id in cash_account_ids:
        account = db.execute(select(Account).where(Account.id == acc_id)).scalar_one_or_none()
        if account:
            ending_cash += account.current_balance

    beginning_cash = ending_cash - total_cash_change

    return {
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end.isoformat()
        },
        "operating_activities": {
            "net_income": float(net_income),
            "customer_payments_received": float(customer_payments),
            "vendor_payments_made": float(-vendor_payments),
            "net_cash_from_operations": float(operating_cash_flow)
        },
        "investing_activities": {
            "net_cash_from_investing": 0  # Would need asset purchase/sale tracking
        },
        "financing_activities": {
            "net_cash_from_financing": 0  # Would need loan/equity tracking
        },
        "summary": {
            "net_increase_in_cash": float(total_cash_change),
            "beginning_cash_balance": float(beginning_cash),
            "ending_cash_balance": float(ending_cash)
        }
    }


@router.get("/account-transactions/{account_id}")
def account_transactions(
    account_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get all transactions for a specific account"""
    account = db.execute(select(Account).where(Account.id == account_id)).scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    query = (
        select(JournalEntryLine, JournalEntry)
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(
            JournalEntryLine.account_id == account_id,
            JournalEntry.status == JournalEntryStatus.POSTED
        )
    )

    if start_date:
        query = query.where(JournalEntry.entry_date >= start_date)
    if end_date:
        query = query.where(JournalEntry.entry_date <= end_date)

    query = query.order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc())
    query = query.offset(skip).limit(limit)

    result = db.execute(query)

    transactions = []
    running_balance = account.current_balance

    for line, entry in result:
        transactions.append({
            "entry_id": entry.id,
            "entry_number": entry.entry_number,
            "entry_date": entry.entry_date.isoformat(),
            "description": line.description or entry.description,
            "reference": entry.reference,
            "debit": float(line.debit),
            "credit": float(line.credit),
            "balance": float(running_balance)
        })
        # Adjust running balance going backwards
        running_balance -= (line.debit - line.credit)

    return {
        "account": {
            "id": account.id,
            "code": account.code,
            "name": account.name,
            "current_balance": float(account.current_balance)
        },
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else date.today().isoformat()
        },
        "transactions": transactions
    }


# ============ EXPORT ENDPOINTS ============

@router.get("/export/trial-balance")
def export_trial_balance(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Export Trial Balance to CSV"""
    data = get_trial_balance(db)

    headers = ["Account Code", "Account Name", "Debit", "Credit"]
    rows = []

    for item in data.get("accounts", []):
        rows.append([
            item["account_code"],
            item["account_name"],
            item["debit"],
            item["credit"]
        ])

    # Add totals row
    rows.append([])
    rows.append(["", "TOTALS", data.get("total_debits", 0), data.get("total_credits", 0)])

    return generate_csv(headers, rows, f"trial_balance_{date.today().isoformat()}.csv")


@router.get("/export/balance-sheet")
def export_balance_sheet(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Export Balance Sheet to CSV"""
    data = balance_sheet_report(as_of_date, current_user, db)

    headers = ["Category", "Account Code", "Account Name", "Balance"]
    rows = []

    # Assets
    rows.append(["ASSETS", "", "", ""])
    for item in data["assets"]["accounts"]:
        rows.append(["", item["account_code"], item["account_name"], item["balance"]])
    rows.append(["", "", "Total Assets", data["assets"]["total"]])
    rows.append([])

    # Liabilities
    rows.append(["LIABILITIES", "", "", ""])
    for item in data["liabilities"]["accounts"]:
        rows.append(["", item["account_code"], item["account_name"], item["balance"]])
    rows.append(["", "", "Total Liabilities", data["liabilities"]["total"]])
    rows.append([])

    # Equity
    rows.append(["EQUITY", "", "", ""])
    for item in data["equity"]["accounts"]:
        rows.append(["", item["account_code"], item["account_name"], item["balance"]])
    rows.append(["", "", "Total Equity", data["equity"]["total"]])
    rows.append([])

    rows.append(["", "", "Total Liabilities & Equity", data["total_liabilities_and_equity"]])

    return generate_csv(headers, rows, f"balance_sheet_{as_of_date or date.today()}.csv")


@router.get("/export/income-statement")
def export_income_statement(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Export Income Statement to CSV"""
    data = income_statement_report(start_date, end_date, current_user, db)

    headers = ["Category", "Account Code", "Account Name", "Amount"]
    rows = []

    # Revenue
    rows.append(["REVENUE", "", "", ""])
    for item in data["revenue"]["accounts"]:
        rows.append(["", item["account_code"], item["account_name"], item["balance"]])
    rows.append(["", "", "Total Revenue", data["revenue"]["total"]])
    rows.append([])

    # Expenses
    rows.append(["EXPENSES", "", "", ""])
    for item in data["expenses"]["accounts"]:
        rows.append(["", item["account_code"], item["account_name"], item["balance"]])
    rows.append(["", "", "Total Expenses", data["expenses"]["total"]])
    rows.append([])

    rows.append(["", "", "NET INCOME", data["net_income"]])

    return generate_csv(headers, rows, f"income_statement_{end_date or date.today()}.csv")


@router.get("/export/ar-aging")
def export_ar_aging(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Export AR Aging Report to CSV"""
    data = ar_aging_report(as_of_date, current_user, db)

    headers = ["Invoice #", "Customer", "Invoice Date", "Due Date", "Balance Due", "Days Overdue", "Aging Bucket"]
    rows = []

    bucket_names = {
        "current": "Current",
        "1_30": "1-30 Days",
        "31_60": "31-60 Days",
        "61_90": "61-90 Days",
        "over_90": "Over 90 Days"
    }

    for bucket, items in data["buckets"].items():
        for item in items:
            rows.append([
                item["invoice_number"],
                item["customer_name"],
                item["invoice_date"],
                item["due_date"],
                item["balance_due"],
                item["days_overdue"],
                bucket_names[bucket]
            ])

    # Add summary
    rows.append([])
    rows.append(["SUMMARY", "", "", "", "", "", ""])
    rows.append(["Current", "", "", "", data["totals"]["current"], "", ""])
    rows.append(["1-30 Days", "", "", "", data["totals"]["1_30"], "", ""])
    rows.append(["31-60 Days", "", "", "", data["totals"]["31_60"], "", ""])
    rows.append(["61-90 Days", "", "", "", data["totals"]["61_90"], "", ""])
    rows.append(["Over 90 Days", "", "", "", data["totals"]["over_90"], "", ""])
    rows.append(["TOTAL", "", "", "", data["totals"]["total"], "", ""])

    return generate_csv(headers, rows, f"ar_aging_{as_of_date or date.today()}.csv")


@router.get("/export/ap-aging")
def export_ap_aging(
    as_of_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Export AP Aging Report to CSV"""
    data = ap_aging_report(as_of_date, current_user, db)

    headers = ["Bill #", "Vendor", "Bill Date", "Due Date", "Balance Due", "Days Overdue", "Aging Bucket"]
    rows = []

    bucket_names = {
        "current": "Current",
        "1_30": "1-30 Days",
        "31_60": "31-60 Days",
        "61_90": "61-90 Days",
        "over_90": "Over 90 Days"
    }

    for bucket, items in data["buckets"].items():
        for item in items:
            rows.append([
                item["bill_number"],
                item["vendor_name"],
                item["bill_date"],
                item["due_date"],
                item["balance_due"],
                item["days_overdue"],
                bucket_names[bucket]
            ])

    # Add summary
    rows.append([])
    rows.append(["SUMMARY", "", "", "", "", "", ""])
    rows.append(["Current", "", "", "", data["totals"]["current"], "", ""])
    rows.append(["1-30 Days", "", "", "", data["totals"]["1_30"], "", ""])
    rows.append(["31-60 Days", "", "", "", data["totals"]["31_60"], "", ""])
    rows.append(["61-90 Days", "", "", "", data["totals"]["61_90"], "", ""])
    rows.append(["Over 90 Days", "", "", "", data["totals"]["over_90"], "", ""])
    rows.append(["TOTAL", "", "", "", data["totals"]["total"], "", ""])

    return generate_csv(headers, rows, f"ap_aging_{as_of_date or date.today()}.csv")


@router.get("/export/general-ledger")
def export_general_ledger(
    account_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Export General Ledger to CSV"""
    data = general_ledger_report(account_id, start_date, end_date, current_user, db)

    headers = ["Account Code", "Account Name", "Entry #", "Date", "Description", "Reference", "Debit", "Credit"]
    rows = []

    for account in data["accounts"]:
        for tx in account["transactions"]:
            rows.append([
                account["account_code"],
                account["account_name"],
                tx["entry_number"],
                tx["entry_date"],
                tx["description"],
                tx["reference"] or "",
                tx["debit"],
                tx["credit"]
            ])
        # Account totals
        rows.append([
            account["account_code"],
            "TOTAL",
            "",
            "",
            "",
            "",
            account["total_debits"],
            account["total_credits"]
        ])
        rows.append([])

    return generate_csv(headers, rows, f"general_ledger_{end_date or date.today()}.csv")


@router.get("/export/cash-flow")
def export_cash_flow(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Export Cash Flow Statement to CSV"""
    data = cash_flow_statement(start_date, end_date, current_user, db)

    headers = ["Category", "Item", "Amount"]
    rows = []

    # Operating Activities
    rows.append(["OPERATING ACTIVITIES", "", ""])
    rows.append(["", "Net Income", data["operating_activities"]["net_income"]])
    rows.append(["", "Customer Payments Received", data["operating_activities"]["customer_payments_received"]])
    rows.append(["", "Vendor Payments Made", data["operating_activities"]["vendor_payments_made"]])
    rows.append(["", "Net Cash from Operations", data["operating_activities"]["net_cash_from_operations"]])
    rows.append([])

    # Investing Activities
    rows.append(["INVESTING ACTIVITIES", "", ""])
    rows.append(["", "Net Cash from Investing", data["investing_activities"]["net_cash_from_investing"]])
    rows.append([])

    # Financing Activities
    rows.append(["FINANCING ACTIVITIES", "", ""])
    rows.append(["", "Net Cash from Financing", data["financing_activities"]["net_cash_from_financing"]])
    rows.append([])

    # Summary
    rows.append(["SUMMARY", "", ""])
    rows.append(["", "Net Increase in Cash", data["summary"]["net_increase_in_cash"]])
    rows.append(["", "Beginning Cash Balance", data["summary"]["beginning_cash_balance"]])
    rows.append(["", "Ending Cash Balance", data["summary"]["ending_cash_balance"]])

    return generate_csv(headers, rows, f"cash_flow_{end_date or date.today()}.csv")
