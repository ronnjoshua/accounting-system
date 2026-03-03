"""Seed data

Revision ID: 002
Revises: 001
Create Date: 2024-01-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from passlib.context import CryptContext

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    # Insert roles
    op.execute("""
        INSERT INTO roles (id, name, description, created_at, updated_at) VALUES
        (1, 'admin', 'Full system access', NOW(), NOW()),
        (2, 'accountant', 'Can manage all accounting functions', NOW(), NOW()),
        (3, 'manager', 'Can view and approve transactions', NOW(), NOW()),
        (4, 'viewer', 'Read-only access to reports', NOW(), NOW())
    """)

    # Insert default admin user (password: admin123)
    hashed_password = pwd_context.hash("admin123")
    op.execute(f"""
        INSERT INTO users (id, email, hashed_password, first_name, last_name, is_active, is_superuser, created_at, updated_at)
        VALUES (1, 'admin@company.com', '{hashed_password}', 'System', 'Administrator', true, true, NOW(), NOW())
    """)

    # Assign admin role to admin user
    op.execute("""
        INSERT INTO user_roles (user_id, role_id) VALUES (1, 1)
    """)

    # Insert account types
    op.execute("""
        INSERT INTO account_types (id, name, category, description, normal_balance, created_at, updated_at) VALUES
        (1, 'Current Assets', 'asset', 'Cash and assets convertible to cash within a year', 'debit', NOW(), NOW()),
        (2, 'Fixed Assets', 'asset', 'Long-term tangible assets', 'debit', NOW(), NOW()),
        (3, 'Other Assets', 'asset', 'Intangible and other assets', 'debit', NOW(), NOW()),
        (4, 'Current Liabilities', 'liability', 'Obligations due within a year', 'credit', NOW(), NOW()),
        (5, 'Long-term Liabilities', 'liability', 'Obligations due after one year', 'credit', NOW(), NOW()),
        (6, 'Equity', 'equity', 'Owner equity and retained earnings', 'credit', NOW(), NOW()),
        (7, 'Revenue', 'revenue', 'Income from business operations', 'credit', NOW(), NOW()),
        (8, 'Cost of Goods Sold', 'expense', 'Direct costs of goods sold', 'debit', NOW(), NOW()),
        (9, 'Operating Expenses', 'expense', 'Regular business expenses', 'debit', NOW(), NOW()),
        (10, 'Other Income', 'revenue', 'Non-operating income', 'credit', NOW(), NOW()),
        (11, 'Other Expenses', 'expense', 'Non-operating expenses', 'debit', NOW(), NOW())
    """)

    # Insert default chart of accounts
    op.execute("""
        INSERT INTO accounts (id, code, name, account_type_id, is_active, is_system, currency_code, current_balance, created_at, updated_at) VALUES
        -- Assets
        (1, '1000', 'Cash', 1, true, true, 'USD', 0, NOW(), NOW()),
        (2, '1010', 'Petty Cash', 1, true, false, 'USD', 0, NOW(), NOW()),
        (3, '1100', 'Accounts Receivable', 1, true, true, 'USD', 0, NOW(), NOW()),
        (4, '1200', 'Inventory', 1, true, true, 'USD', 0, NOW(), NOW()),
        (5, '1300', 'Prepaid Expenses', 1, true, false, 'USD', 0, NOW(), NOW()),
        (6, '1500', 'Equipment', 2, true, false, 'USD', 0, NOW(), NOW()),
        (7, '1510', 'Accumulated Depreciation - Equipment', 2, true, false, 'USD', 0, NOW(), NOW()),
        (8, '1600', 'Vehicles', 2, true, false, 'USD', 0, NOW(), NOW()),
        (9, '1610', 'Accumulated Depreciation - Vehicles', 2, true, false, 'USD', 0, NOW(), NOW()),

        -- Liabilities
        (10, '2000', 'Accounts Payable', 4, true, true, 'USD', 0, NOW(), NOW()),
        (11, '2100', 'Accrued Expenses', 4, true, false, 'USD', 0, NOW(), NOW()),
        (12, '2200', 'Sales Tax Payable', 4, true, false, 'USD', 0, NOW(), NOW()),
        (13, '2300', 'Wages Payable', 4, true, false, 'USD', 0, NOW(), NOW()),
        (14, '2500', 'Notes Payable', 5, true, false, 'USD', 0, NOW(), NOW()),
        (15, '2600', 'Long-term Debt', 5, true, false, 'USD', 0, NOW(), NOW()),

        -- Equity
        (16, '3000', 'Owner''s Capital', 6, true, true, 'USD', 0, NOW(), NOW()),
        (17, '3100', 'Retained Earnings', 6, true, true, 'USD', 0, NOW(), NOW()),
        (18, '3200', 'Owner''s Drawings', 6, true, false, 'USD', 0, NOW(), NOW()),

        -- Revenue
        (19, '4000', 'Sales Revenue', 7, true, true, 'USD', 0, NOW(), NOW()),
        (20, '4100', 'Service Revenue', 7, true, false, 'USD', 0, NOW(), NOW()),
        (21, '4200', 'Sales Discounts', 7, true, false, 'USD', 0, NOW(), NOW()),
        (22, '4300', 'Sales Returns', 7, true, false, 'USD', 0, NOW(), NOW()),
        (23, '4900', 'Other Income', 10, true, false, 'USD', 0, NOW(), NOW()),

        -- Cost of Goods Sold
        (24, '5000', 'Cost of Goods Sold', 8, true, true, 'USD', 0, NOW(), NOW()),
        (25, '5100', 'Purchase Discounts', 8, true, false, 'USD', 0, NOW(), NOW()),
        (26, '5200', 'Purchase Returns', 8, true, false, 'USD', 0, NOW(), NOW()),

        -- Operating Expenses
        (27, '6000', 'Advertising Expense', 9, true, false, 'USD', 0, NOW(), NOW()),
        (28, '6100', 'Bank Charges', 9, true, false, 'USD', 0, NOW(), NOW()),
        (29, '6200', 'Depreciation Expense', 9, true, false, 'USD', 0, NOW(), NOW()),
        (30, '6300', 'Insurance Expense', 9, true, false, 'USD', 0, NOW(), NOW()),
        (31, '6400', 'Office Supplies Expense', 9, true, false, 'USD', 0, NOW(), NOW()),
        (32, '6500', 'Rent Expense', 9, true, false, 'USD', 0, NOW(), NOW()),
        (33, '6600', 'Salaries Expense', 9, true, false, 'USD', 0, NOW(), NOW()),
        (34, '6700', 'Utilities Expense', 9, true, false, 'USD', 0, NOW(), NOW()),
        (35, '6800', 'Professional Fees', 9, true, false, 'USD', 0, NOW(), NOW()),
        (36, '6900', 'Miscellaneous Expense', 9, true, false, 'USD', 0, NOW(), NOW()),

        -- Other Expenses
        (37, '7000', 'Interest Expense', 11, true, false, 'USD', 0, NOW(), NOW()),
        (38, '7100', 'Loss on Sale of Assets', 11, true, false, 'USD', 0, NOW(), NOW())
    """)

    # Insert default currencies
    op.execute("""
        INSERT INTO currencies (id, code, name, symbol, decimal_places, is_active, created_at, updated_at) VALUES
        (1, 'USD', 'US Dollar', '$', 2, true, NOW(), NOW()),
        (2, 'EUR', 'Euro', '€', 2, true, NOW(), NOW()),
        (3, 'GBP', 'British Pound', '£', 2, true, NOW(), NOW()),
        (4, 'JPY', 'Japanese Yen', '¥', 0, true, NOW(), NOW()),
        (5, 'CAD', 'Canadian Dollar', 'C$', 2, true, NOW(), NOW()),
        (6, 'AUD', 'Australian Dollar', 'A$', 2, true, NOW(), NOW()),
        (7, 'PHP', 'Philippine Peso', '₱', 2, true, NOW(), NOW())
    """)

    # Update sequences
    op.execute("SELECT setval('roles_id_seq', 4)")
    op.execute("SELECT setval('users_id_seq', 1)")
    op.execute("SELECT setval('account_types_id_seq', 11)")
    op.execute("SELECT setval('accounts_id_seq', 38)")
    op.execute("SELECT setval('currencies_id_seq', 7)")


def downgrade() -> None:
    op.execute("DELETE FROM currencies")
    op.execute("DELETE FROM accounts")
    op.execute("DELETE FROM account_types")
    op.execute("DELETE FROM user_roles")
    op.execute("DELETE FROM users")
    op.execute("DELETE FROM roles")
