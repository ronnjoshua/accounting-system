"""Fix schema mismatches between models and database

Revision ID: 004
Revises: 003
Create Date: 2024-01-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============ FIX BANK_TRANSACTIONS ============
    # Add missing columns
    op.add_column('bank_transactions', sa.Column('transaction_id', sa.String(100), nullable=True))
    op.add_column('bank_transactions', sa.Column('post_date', sa.Date(), nullable=True))
    op.add_column('bank_transactions', sa.Column('is_matched', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('bank_transactions', sa.Column('matched_journal_entry_id', sa.Integer(), nullable=True))
    op.add_column('bank_transactions', sa.Column('matched_at', sa.DateTime(), nullable=True))
    op.add_column('bank_transactions', sa.Column('matched_by_id', sa.Integer(), nullable=True))
    op.add_column('bank_transactions', sa.Column('category', sa.String(100), nullable=True))
    op.add_column('bank_transactions', sa.Column('memo', sa.Text(), nullable=True))
    op.add_column('bank_transactions', sa.Column('created_by_id', sa.Integer(), nullable=True))
    op.add_column('bank_transactions', sa.Column('updated_by_id', sa.Integer(), nullable=True))

    # Create unique constraint on transaction_id (after populating)
    op.execute("UPDATE bank_transactions SET transaction_id = 'TXN-' || id WHERE transaction_id IS NULL")
    op.alter_column('bank_transactions', 'transaction_id', nullable=False)
    op.create_unique_constraint('uq_bank_transactions_transaction_id', 'bank_transactions', ['transaction_id'])

    # ============ FIX BANK_RECONCILIATION_ITEMS ============
    op.add_column('bank_reconciliation_items', sa.Column('transaction_date', sa.Date(), nullable=True))
    op.add_column('bank_reconciliation_items', sa.Column('description', sa.String(500), nullable=True))
    op.add_column('bank_reconciliation_items', sa.Column('amount', sa.Numeric(18, 2), nullable=True))
    op.add_column('bank_reconciliation_items', sa.Column('cleared_date', sa.Date(), nullable=True))

    # Make journal_entry_line_id nullable
    op.alter_column('bank_reconciliation_items', 'journal_entry_line_id', nullable=True)

    # Set defaults for new required columns
    op.execute("UPDATE bank_reconciliation_items SET transaction_date = CURRENT_DATE WHERE transaction_date IS NULL")
    op.execute("UPDATE bank_reconciliation_items SET description = 'Reconciliation item' WHERE description IS NULL")
    op.execute("UPDATE bank_reconciliation_items SET amount = 0 WHERE amount IS NULL")
    op.alter_column('bank_reconciliation_items', 'transaction_date', nullable=False)
    op.alter_column('bank_reconciliation_items', 'description', nullable=False)
    op.alter_column('bank_reconciliation_items', 'amount', nullable=False)

    # ============ FIX BUDGETS ============
    op.add_column('budgets', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('budgets', sa.Column('end_date', sa.Date(), nullable=True))

    # Set default values for start_date and end_date
    op.execute("UPDATE budgets SET start_date = DATE_TRUNC('year', CURRENT_DATE), end_date = DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year' - INTERVAL '1 day' WHERE start_date IS NULL")
    op.alter_column('budgets', 'start_date', nullable=False)
    op.alter_column('budgets', 'end_date', nullable=False)

    # ============ FIX BUDGET_LINES ============
    op.add_column('budget_lines', sa.Column('period_start', sa.Date(), nullable=True))
    op.add_column('budget_lines', sa.Column('period_end', sa.Date(), nullable=True))
    op.add_column('budget_lines', sa.Column('budgeted_amount', sa.Numeric(18, 2), nullable=False, server_default='0'))
    op.add_column('budget_lines', sa.Column('actual_amount', sa.Numeric(18, 2), nullable=False, server_default='0'))
    op.add_column('budget_lines', sa.Column('variance', sa.Numeric(18, 2), nullable=False, server_default='0'))
    op.add_column('budget_lines', sa.Column('variance_percent', sa.Numeric(8, 2), nullable=False, server_default='0'))

    # Copy existing amount to budgeted_amount
    op.execute("UPDATE budget_lines SET budgeted_amount = COALESCE(amount, 0)")
    op.execute("UPDATE budget_lines SET period_start = CURRENT_DATE, period_end = CURRENT_DATE WHERE period_start IS NULL")
    op.alter_column('budget_lines', 'period_start', nullable=False)
    op.alter_column('budget_lines', 'period_end', nullable=False)

    # ============ FIX TAX_RATES ============
    op.add_column('tax_rates', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('tax_rates', sa.Column('tax_collected_account_id', sa.Integer(), nullable=True))
    op.add_column('tax_rates', sa.Column('tax_paid_account_id', sa.Integer(), nullable=True))
    op.add_column('tax_rates', sa.Column('is_compound', sa.Boolean(), nullable=False, server_default='false'))

    # ============ FIX TAX_EXEMPTIONS ============
    op.add_column('tax_exemptions', sa.Column('certificate_number', sa.String(100), nullable=True))
    op.add_column('tax_exemptions', sa.Column('exemption_reason', sa.String(255), nullable=True))
    op.add_column('tax_exemptions', sa.Column('effective_from', sa.Date(), nullable=True))
    op.add_column('tax_exemptions', sa.Column('effective_to', sa.Date(), nullable=True))
    op.add_column('tax_exemptions', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('tax_exemptions', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('tax_exemptions', sa.Column('created_by_id', sa.Integer(), nullable=True))
    op.add_column('tax_exemptions', sa.Column('updated_by_id', sa.Integer(), nullable=True))

    # Migrate existing data
    op.execute("UPDATE tax_exemptions SET certificate_number = COALESCE(exemption_certificate, 'N/A'), exemption_reason = COALESCE(reason, 'Not specified'), effective_from = COALESCE(valid_from, CURRENT_DATE)")
    op.alter_column('tax_exemptions', 'certificate_number', nullable=False)
    op.alter_column('tax_exemptions', 'exemption_reason', nullable=False)
    op.alter_column('tax_exemptions', 'effective_from', nullable=False)

    # Make tax_rate_id nullable per model
    op.alter_column('tax_exemptions', 'tax_rate_id', nullable=True)

    # ============ FIX TAX_PERIODS ============
    op.add_column('tax_periods', sa.Column('filed_at', sa.DateTime(), nullable=True))
    op.add_column('tax_periods', sa.Column('payment_reference', sa.String(100), nullable=True))
    op.add_column('tax_periods', sa.Column('payment_date', sa.Date(), nullable=True))
    op.add_column('tax_periods', sa.Column('payment_amount', sa.Numeric(18, 2), nullable=False, server_default='0'))

    # Migrate filed_date to filed_at
    op.execute("UPDATE tax_periods SET filed_at = filed_date::timestamp WHERE filed_date IS NOT NULL")

    # ============ FIX RECURRING_TEMPLATES ============
    op.add_column('recurring_templates', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('recurring_templates', sa.Column('last_run_status', sa.String(50), nullable=True))
    op.add_column('recurring_templates', sa.Column('notes', sa.Text(), nullable=True))

    # ============ FIX RECURRING_EXECUTIONS ============
    op.add_column('recurring_executions', sa.Column('executed_at', sa.DateTime(), nullable=True))
    op.add_column('recurring_executions', sa.Column('created_entity_type', sa.String(50), nullable=True))
    op.add_column('recurring_executions', sa.Column('created_entity_id', sa.Integer(), nullable=True))

    # Migrate existing data
    op.execute("UPDATE recurring_executions SET executed_at = COALESCE(created_at, NOW())")
    op.alter_column('recurring_executions', 'executed_at', nullable=False)


def downgrade() -> None:
    # RECURRING_EXECUTIONS
    op.drop_column('recurring_executions', 'created_entity_id')
    op.drop_column('recurring_executions', 'created_entity_type')
    op.drop_column('recurring_executions', 'executed_at')

    # RECURRING_TEMPLATES
    op.drop_column('recurring_templates', 'notes')
    op.drop_column('recurring_templates', 'last_run_status')
    op.drop_column('recurring_templates', 'description')

    # TAX_PERIODS
    op.drop_column('tax_periods', 'payment_amount')
    op.drop_column('tax_periods', 'payment_date')
    op.drop_column('tax_periods', 'payment_reference')
    op.drop_column('tax_periods', 'filed_at')

    # TAX_EXEMPTIONS
    op.drop_column('tax_exemptions', 'updated_by_id')
    op.drop_column('tax_exemptions', 'created_by_id')
    op.drop_column('tax_exemptions', 'notes')
    op.drop_column('tax_exemptions', 'is_active')
    op.drop_column('tax_exemptions', 'effective_to')
    op.drop_column('tax_exemptions', 'effective_from')
    op.drop_column('tax_exemptions', 'exemption_reason')
    op.drop_column('tax_exemptions', 'certificate_number')

    # TAX_RATES
    op.drop_column('tax_rates', 'is_compound')
    op.drop_column('tax_rates', 'tax_paid_account_id')
    op.drop_column('tax_rates', 'tax_collected_account_id')
    op.drop_column('tax_rates', 'description')

    # BUDGET_LINES
    op.drop_column('budget_lines', 'variance_percent')
    op.drop_column('budget_lines', 'variance')
    op.drop_column('budget_lines', 'actual_amount')
    op.drop_column('budget_lines', 'budgeted_amount')
    op.drop_column('budget_lines', 'period_end')
    op.drop_column('budget_lines', 'period_start')

    # BUDGETS
    op.drop_column('budgets', 'end_date')
    op.drop_column('budgets', 'start_date')

    # BANK_RECONCILIATION_ITEMS
    op.drop_column('bank_reconciliation_items', 'cleared_date')
    op.drop_column('bank_reconciliation_items', 'amount')
    op.drop_column('bank_reconciliation_items', 'description')
    op.drop_column('bank_reconciliation_items', 'transaction_date')

    # BANK_TRANSACTIONS
    op.drop_constraint('uq_bank_transactions_transaction_id', 'bank_transactions')
    op.drop_column('bank_transactions', 'updated_by_id')
    op.drop_column('bank_transactions', 'created_by_id')
    op.drop_column('bank_transactions', 'memo')
    op.drop_column('bank_transactions', 'category')
    op.drop_column('bank_transactions', 'matched_by_id')
    op.drop_column('bank_transactions', 'matched_at')
    op.drop_column('bank_transactions', 'matched_journal_entry_id')
    op.drop_column('bank_transactions', 'is_matched')
    op.drop_column('bank_transactions', 'post_date')
    op.drop_column('bank_transactions', 'transaction_id')
