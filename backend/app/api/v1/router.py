from fastapi import APIRouter
from app.api.v1 import (
    auth, users, company, accounts,
    journal_entries, customers, vendors,
    invoices, bills, products, warehouses,
    purchase_orders, reports
)

api_router = APIRouter()

# Auth routes (no prefix)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User management
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Company settings
api_router.include_router(company.router, prefix="/company", tags=["Company"])

# Accounting
api_router.include_router(accounts.router, prefix="/accounts", tags=["Chart of Accounts"])
api_router.include_router(journal_entries.router, prefix="/journal-entries", tags=["Journal Entries"])

# AR
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])

# AP
api_router.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
api_router.include_router(bills.router, prefix="/bills", tags=["Bills"])

# Inventory
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["Warehouses"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"])

# Reports
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
