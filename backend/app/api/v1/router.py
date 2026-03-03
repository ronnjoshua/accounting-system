from fastapi import APIRouter
from app.api.v1 import (
    auth, users, company, accounts, currencies,
    journal_entries, customers, vendors,
    invoices, bills, products, warehouses,
    purchase_orders, reports, payments,
    stock_movements, audit, documents,
    banking, budgets, taxes, recurring
)

api_router = APIRouter()

# Auth routes (no prefix)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User management
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Company settings
api_router.include_router(company.router, prefix="/company", tags=["Company"])

# Currencies
api_router.include_router(currencies.router, prefix="/currencies", tags=["Currencies"])

# Accounting
api_router.include_router(accounts.router, prefix="/accounts", tags=["Chart of Accounts"])
api_router.include_router(journal_entries.router, prefix="/journal-entries", tags=["Journal Entries"])

# AR
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])

# AP
api_router.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
api_router.include_router(bills.router, prefix="/bills", tags=["Bills"])

# Payments
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])

# Inventory
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["Warehouses"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"])
api_router.include_router(stock_movements.router, prefix="/stock-movements", tags=["Stock Movements"])

# Banking
api_router.include_router(banking.router, prefix="/banking", tags=["Bank Reconciliation"])

# Budgeting
api_router.include_router(budgets.router, prefix="/budgets", tags=["Budgets"])

# Tax Management
api_router.include_router(taxes.router, prefix="/taxes", tags=["Tax Management"])

# Recurring Transactions
api_router.include_router(recurring.router, prefix="/recurring", tags=["Recurring Transactions"])

# Documents
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])

# Audit
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])

# Reports
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
