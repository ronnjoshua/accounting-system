"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create user_roles association table
    op.create_table('user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Create user_invites table
    op.create_table('user_invites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('invited_by_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_invites_email', 'user_invites', ['email'], unique=True)
    op.create_index('ix_user_invites_token', 'user_invites', ['token'], unique=True)

    # Create company_settings table
    op.create_table('company_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=True),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('fiscal_year_start_month', sa.Integer(), nullable=False, default=1),
        sa.Column('fiscal_year_start_day', sa.Integer(), nullable=False, default=1),
        sa.Column('base_currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create fiscal_periods table
    op.create_table('fiscal_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_closed', sa.Boolean(), nullable=False, default=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create account_types table
    op.create_table('account_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.Enum('asset', 'liability', 'equity', 'revenue', 'expense', name='accounttypeenum'), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('normal_balance', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create accounts table
    op.create_table('accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('account_type_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, default=False),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('current_balance', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['account_type_id'], ['account_types.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['accounts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_accounts_code', 'accounts', ['code'], unique=True)

    # Create currencies table
    op.create_table('currencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=3), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('decimal_places', sa.Integer(), nullable=False, default=2),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_currencies_code', 'currencies', ['code'], unique=True)

    # Create exchange_rates table
    op.create_table('exchange_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_currency_code', sa.String(length=3), nullable=False),
        sa.Column('to_currency_code', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_exchange_rates_from_currency', 'exchange_rates', ['from_currency_code'])
    op.create_index('ix_exchange_rates_to_currency', 'exchange_rates', ['to_currency_code'])
    op.create_index('ix_exchange_rates_effective_date', 'exchange_rates', ['effective_date'])

    # Create journal_entries table
    op.create_table('journal_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_number', sa.String(length=50), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('draft', 'posted', 'void', name='journalentrystatus'), nullable=False, default='draft'),
        sa.Column('is_adjusting', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_closing', sa.Boolean(), nullable=False, default=False),
        sa.Column('fiscal_period_id', sa.Integer(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, default=False),
        sa.Column('recurring_template_id', sa.Integer(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=True),
        sa.Column('posted_by_id', sa.Integer(), nullable=True),
        sa.Column('voided_at', sa.DateTime(), nullable=True),
        sa.Column('voided_by_id', sa.Integer(), nullable=True),
        sa.Column('void_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['fiscal_period_id'], ['fiscal_periods.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_journal_entries_entry_number', 'journal_entries', ['entry_number'], unique=True)
    op.create_index('ix_journal_entries_entry_date', 'journal_entries', ['entry_date'])

    # Create journal_entry_lines table
    op.create_table('journal_entry_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('journal_entry_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('debit', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('credit', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=8), nullable=False, default=1),
        sa.Column('base_debit', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('base_credit', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create customers table
    op.create_table('customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('billing_address_line1', sa.String(length=255), nullable=True),
        sa.Column('billing_address_line2', sa.String(length=255), nullable=True),
        sa.Column('billing_city', sa.String(length=100), nullable=True),
        sa.Column('billing_state', sa.String(length=100), nullable=True),
        sa.Column('billing_postal_code', sa.String(length=20), nullable=True),
        sa.Column('billing_country', sa.String(length=100), nullable=True),
        sa.Column('shipping_address_line1', sa.String(length=255), nullable=True),
        sa.Column('shipping_address_line2', sa.String(length=255), nullable=True),
        sa.Column('shipping_city', sa.String(length=100), nullable=True),
        sa.Column('shipping_state', sa.String(length=100), nullable=True),
        sa.Column('shipping_postal_code', sa.String(length=20), nullable=True),
        sa.Column('shipping_country', sa.String(length=100), nullable=True),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('credit_limit', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('payment_terms_days', sa.Integer(), nullable=False, default=30),
        sa.Column('receivable_account_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['receivable_account_id'], ['accounts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customers_code', 'customers', ['code'], unique=True)

    # Create vendors table
    op.create_table('vendors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('payment_terms_days', sa.Integer(), nullable=False, default=30),
        sa.Column('payable_account_id', sa.Integer(), nullable=True),
        sa.Column('bank_name', sa.String(length=255), nullable=True),
        sa.Column('bank_account_number', sa.String(length=50), nullable=True),
        sa.Column('bank_routing_number', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['payable_account_id'], ['accounts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vendors_code', 'vendors', ['code'], unique=True)

    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('product_type', sa.Enum('inventory', 'non_inventory', 'service', name='producttype'), nullable=False, default='inventory'),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('unit_of_measure', sa.String(length=50), nullable=False, default='unit'),
        sa.Column('purchase_price', sa.Numeric(precision=18, scale=4), nullable=False, default=0),
        sa.Column('selling_price', sa.Numeric(precision=18, scale=4), nullable=False, default=0),
        sa.Column('track_inventory', sa.Boolean(), nullable=False, default=True),
        sa.Column('reorder_point', sa.Numeric(precision=18, scale=4), nullable=False, default=0),
        sa.Column('reorder_quantity', sa.Numeric(precision=18, scale=4), nullable=False, default=0),
        sa.Column('inventory_account_id', sa.Integer(), nullable=True),
        sa.Column('revenue_account_id', sa.Integer(), nullable=True),
        sa.Column('expense_account_id', sa.Integer(), nullable=True),
        sa.Column('costing_method', sa.String(length=20), nullable=False, default='weighted_average'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('quantity_on_hand', sa.Numeric(precision=18, scale=4), nullable=False, default=0),
        sa.Column('average_cost', sa.Numeric(precision=18, scale=4), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['inventory_account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['revenue_account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['expense_account_id'], ['accounts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_products_code', 'products', ['code'], unique=True)

    # Create warehouses table
    op.create_table('warehouses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_warehouses_code', 'warehouses', ['code'], unique=True)

    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('draft', 'sent', 'partially_paid', 'paid', 'overdue', 'void', name='invoicestatus'), nullable=False, default='draft'),
        sa.Column('subtotal', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('tax_amount', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('discount_amount', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('total', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('amount_paid', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('balance_due', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=8), nullable=False, default=1),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('terms', sa.Text(), nullable=True),
        sa.Column('journal_entry_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'], unique=True)
    op.create_index('ix_invoices_invoice_date', 'invoices', ['invoice_date'])

    # Create invoice_lines table
    op.create_table('invoice_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False, default=1),
        sa.Column('unit_price', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), nullable=False, default=0),
        sa.Column('tax_percent', sa.Numeric(precision=5, scale=2), nullable=False, default=0),
        sa.Column('line_total', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create customer_payments table
    op.create_table('customer_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=8), nullable=False, default=1),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('bank_account_id', sa.Integer(), nullable=False),
        sa.Column('journal_entry_id', sa.Integer(), nullable=True),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['bank_account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customer_payments_payment_number', 'customer_payments', ['payment_number'], unique=True)

    # Create credit_notes table
    op.create_table('credit_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('credit_note_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('credit_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=8), nullable=False, default=1),
        sa.Column('journal_entry_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_credit_notes_credit_note_number', 'credit_notes', ['credit_note_number'], unique=True)

    # Create purchase_orders table
    op.create_table('purchase_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('po_number', sa.String(length=50), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('expected_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'sent', 'partially_received', 'received', 'cancelled', name='purchaseorderstatus'), nullable=False, default='draft'),
        sa.Column('subtotal', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('tax_amount', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('discount_amount', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('total', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=8), nullable=False, default=1),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_purchase_orders_po_number', 'purchase_orders', ['po_number'], unique=True)

    # Create purchase_order_lines table
    op.create_table('purchase_order_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('quantity_ordered', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('quantity_received', sa.Numeric(precision=18, scale=4), nullable=False, default=0),
        sa.Column('unit_price', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('tax_percent', sa.Numeric(precision=5, scale=2), nullable=False, default=0),
        sa.Column('line_total', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create bills table
    op.create_table('bills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bill_number', sa.String(length=50), nullable=False),
        sa.Column('vendor_bill_number', sa.String(length=100), nullable=True),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('bill_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('draft', 'received', 'partially_paid', 'paid', 'overdue', 'void', name='billstatus'), nullable=False, default='draft'),
        sa.Column('subtotal', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('tax_amount', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('discount_amount', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('total', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('amount_paid', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('balance_due', sa.Numeric(precision=18, scale=2), nullable=False, default=0),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=8), nullable=False, default=1),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('purchase_order_id', sa.Integer(), nullable=True),
        sa.Column('journal_entry_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id']),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id']),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bills_bill_number', 'bills', ['bill_number'], unique=True)
    op.create_index('ix_bills_bill_date', 'bills', ['bill_date'])

    # Create bill_lines table
    op.create_table('bill_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bill_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False, default=1),
        sa.Column('unit_price', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), nullable=False, default=0),
        sa.Column('tax_percent', sa.Numeric(precision=5, scale=2), nullable=False, default=0),
        sa.Column('line_total', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create vendor_payments table
    op.create_table('vendor_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_number', sa.String(length=50), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=8), nullable=False, default=1),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('bank_account_id', sa.Integer(), nullable=False),
        sa.Column('journal_entry_id', sa.Integer(), nullable=True),
        sa.Column('bill_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['bank_account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id']),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id']),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vendor_payments_payment_number', 'vendor_payments', ['payment_number'], unique=True)

    # Create debit_notes table
    op.create_table('debit_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('debit_note_number', sa.String(length=50), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('bill_id', sa.Integer(), nullable=True),
        sa.Column('debit_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('currency_code', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=8), nullable=False, default=1),
        sa.Column('journal_entry_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id']),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id']),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_debit_notes_debit_note_number', 'debit_notes', ['debit_note_number'], unique=True)

    # Create stock_movements table
    op.create_table('stock_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('movement_number', sa.String(length=50), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('movement_type', sa.Enum('purchase', 'sale', 'transfer_in', 'transfer_out', 'adjustment_in', 'adjustment_out', 'return_in', 'return_out', name='movementtype'), nullable=False),
        sa.Column('movement_date', sa.Date(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('quantity_after', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('destination_warehouse_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['destination_warehouse_id'], ['warehouses.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stock_movements_movement_number', 'stock_movements', ['movement_number'], unique=True)
    op.create_index('ix_stock_movements_movement_date', 'stock_movements', ['movement_date'])

    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('cloudinary_public_id', sa.String(length=255), nullable=False),
        sa.Column('cloudinary_url', sa.String(length=500), nullable=False),
        sa.Column('cloudinary_secure_url', sa.String(length=500), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_cloudinary_public_id', 'documents', ['cloudinary_public_id'], unique=True)

    # Create document_links table
    op.create_table('document_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_links_entity_type', 'document_links', ['entity_type'])
    op.create_index('ix_document_links_entity_id', 'document_links', ['entity_id'])

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('old_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('document_links')
    op.drop_table('documents')
    op.drop_table('stock_movements')
    op.drop_table('debit_notes')
    op.drop_table('vendor_payments')
    op.drop_table('bill_lines')
    op.drop_table('bills')
    op.drop_table('purchase_order_lines')
    op.drop_table('purchase_orders')
    op.drop_table('credit_notes')
    op.drop_table('customer_payments')
    op.drop_table('invoice_lines')
    op.drop_table('invoices')
    op.drop_table('warehouses')
    op.drop_table('products')
    op.drop_table('vendors')
    op.drop_table('customers')
    op.drop_table('journal_entry_lines')
    op.drop_table('journal_entries')
    op.drop_table('exchange_rates')
    op.drop_table('currencies')
    op.drop_table('accounts')
    op.drop_table('account_types')
    op.drop_table('fiscal_periods')
    op.drop_table('company_settings')
    op.drop_table('user_invites')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.drop_table('roles')

    op.execute('DROP TYPE IF EXISTS accounttypeenum')
    op.execute('DROP TYPE IF EXISTS journalentrystatus')
    op.execute('DROP TYPE IF EXISTS invoicestatus')
    op.execute('DROP TYPE IF EXISTS billstatus')
    op.execute('DROP TYPE IF EXISTS purchaseorderstatus')
    op.execute('DROP TYPE IF EXISTS producttype')
    op.execute('DROP TYPE IF EXISTS movementtype')
