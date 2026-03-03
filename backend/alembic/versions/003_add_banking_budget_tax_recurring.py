"""Add banking, budget, tax, and recurring tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============ BANK RECONCILIATION TABLES ============

    # Bank Transactions (imported from bank)
    op.create_table('bank_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('is_cleared', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('matched_entry_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['matched_entry_id'], ['journal_entries.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bank_transactions_account_date', 'bank_transactions', ['account_id', 'transaction_date'])

    # Bank Reconciliations
    op.create_table('bank_reconciliations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('statement_date', sa.Date(), nullable=False),
        sa.Column('statement_balance', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('gl_balance', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('reconciled_balance', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('difference', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='in_progress'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['completed_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Bank Reconciliation Items
    op.create_table('bank_reconciliation_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reconciliation_id', sa.Integer(), nullable=False),
        sa.Column('journal_entry_line_id', sa.Integer(), nullable=False),
        sa.Column('is_cleared', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cleared_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['reconciliation_id'], ['bank_reconciliations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['journal_entry_line_id'], ['journal_entry_lines.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # ============ BUDGET TABLES ============

    # Budgets
    op.create_table('budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False, server_default='monthly'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('total_revenue', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('total_expense', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('net_income', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_budgets_fiscal_year', 'budgets', ['fiscal_year'])

    # Budget Lines
    op.create_table('budget_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('budget_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('period', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['budget_id'], ['budgets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_budget_lines_budget_account', 'budget_lines', ['budget_id', 'account_id', 'period'])

    # ============ TAX TABLES ============

    # Tax Rates
    op.create_table('tax_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tax_type', sa.String(length=50), nullable=False),
        sa.Column('rate', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('effective_from', sa.Date(), nullable=True),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    # Tax Exemptions
    op.create_table('tax_exemptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('tax_rate_id', sa.Integer(), nullable=False),
        sa.Column('exemption_certificate', sa.String(length=255), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tax_rate_id'], ['tax_rates.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Tax Periods
    op.create_table('tax_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tax_type', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('tax_collected', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('tax_paid', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('net_tax_due', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('is_filed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('filed_date', sa.Date(), nullable=True),
        sa.Column('filed_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['filed_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # ============ RECURRING TRANSACTION TABLES ============

    # Recurring Templates
    op.create_table('recurring_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('recurring_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('interval_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('day_of_month', sa.Integer(), nullable=True),
        sa.Column('day_of_week', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('next_run_date', sa.Date(), nullable=False),
        sa.Column('last_run_date', sa.Date(), nullable=True),
        sa.Column('total_occurrences', sa.Integer(), nullable=True),
        sa.Column('occurrences_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('template_data', sa.JSON(), nullable=True),
        sa.Column('notify_before_days', sa.Integer(), nullable=True),
        sa.Column('auto_post', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_recurring_templates_next_run', 'recurring_templates', ['next_run_date', 'status'])

    # Recurring Executions (history)
    op.create_table('recurring_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('execution_date', sa.Date(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_entry_id', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('executed_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['recurring_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['executed_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # ============ NOTES/ATTACHMENTS TABLES ============

    # Notes
    op.create_table('notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notes_entity', 'notes', ['entity_type', 'entity_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('notes')
    op.drop_table('recurring_executions')
    op.drop_table('recurring_templates')
    op.drop_table('tax_periods')
    op.drop_table('tax_exemptions')
    op.drop_table('tax_rates')
    op.drop_table('budget_lines')
    op.drop_table('budgets')
    op.drop_table('bank_reconciliation_items')
    op.drop_table('bank_reconciliations')
    op.drop_table('bank_transactions')
