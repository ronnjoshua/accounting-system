from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.accounting import (
    Account, AccountType, JournalEntry, JournalEntryLine,
    JournalEntryStatus, Currency, ExchangeRate
)
from app.schemas.accounting import JournalEntryCreate, JournalEntryLineCreate


async def get_next_journal_entry_number(db: AsyncSession) -> str:
    result = await db.execute(
        select(func.count(JournalEntry.id))
    )
    count = result.scalar() or 0
    return f"JE-{count + 1:06d}"


async def create_journal_entry(
    db: AsyncSession,
    data: JournalEntryCreate,
    created_by_id: int,
    source_type: Optional[str] = None,
    source_id: Optional[int] = None
) -> JournalEntry:
    # Validate double-entry: debits must equal credits
    total_debit = sum(line.debit for line in data.lines)
    total_credit = sum(line.credit for line in data.lines)

    if total_debit != total_credit:
        raise ValueError(f"Debits ({total_debit}) must equal credits ({total_credit})")

    if total_debit == 0:
        raise ValueError("Journal entry must have at least one debit/credit")

    entry_number = await get_next_journal_entry_number(db)

    entry = JournalEntry(
        entry_number=entry_number,
        entry_date=data.entry_date,
        description=data.description,
        reference=data.reference,
        is_adjusting=data.is_adjusting,
        source_type=source_type,
        source_id=source_id,
        created_by_id=created_by_id
    )

    # Create lines
    for line_data in data.lines:
        # Calculate base currency amounts
        base_debit = line_data.debit * line_data.exchange_rate
        base_credit = line_data.credit * line_data.exchange_rate

        line = JournalEntryLine(
            account_id=line_data.account_id,
            description=line_data.description,
            debit=line_data.debit,
            credit=line_data.credit,
            currency_code=line_data.currency_code,
            exchange_rate=line_data.exchange_rate,
            base_debit=base_debit,
            base_credit=base_credit
        )
        entry.lines.append(line)

    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def post_journal_entry(
    db: AsyncSession,
    entry: JournalEntry,
    posted_by_id: int
) -> JournalEntry:
    if entry.status != JournalEntryStatus.DRAFT:
        raise ValueError("Only draft entries can be posted")

    # Update account balances
    for line in entry.lines:
        result = await db.execute(
            select(Account).where(Account.id == line.account_id)
        )
        account = result.scalar_one()

        # Get account type to determine normal balance
        result = await db.execute(
            select(AccountType).where(AccountType.id == account.account_type_id)
        )
        account_type = result.scalar_one()

        # Update balance based on normal balance (debit or credit)
        if account_type.normal_balance == "debit":
            account.current_balance += line.base_debit - line.base_credit
        else:
            account.current_balance += line.base_credit - line.base_debit

    # Update entry status
    entry.status = JournalEntryStatus.POSTED
    entry.posted_at = datetime.utcnow()
    entry.posted_by_id = posted_by_id

    await db.commit()
    await db.refresh(entry)
    return entry


async def void_journal_entry(
    db: AsyncSession,
    entry: JournalEntry,
    voided_by_id: int,
    reason: str
) -> JournalEntry:
    if entry.status == JournalEntryStatus.VOID:
        raise ValueError("Entry is already voided")

    if entry.status == JournalEntryStatus.POSTED:
        # Reverse the account balance updates
        for line in entry.lines:
            result = await db.execute(
                select(Account).where(Account.id == line.account_id)
            )
            account = result.scalar_one()

            result = await db.execute(
                select(AccountType).where(AccountType.id == account.account_type_id)
            )
            account_type = result.scalar_one()

            # Reverse the balance
            if account_type.normal_balance == "debit":
                account.current_balance -= line.base_debit - line.base_credit
            else:
                account.current_balance -= line.base_credit - line.base_debit

    entry.status = JournalEntryStatus.VOID
    entry.voided_at = datetime.utcnow()
    entry.voided_by_id = voided_by_id
    entry.void_reason = reason

    await db.commit()
    await db.refresh(entry)
    return entry


async def get_account_balance(
    db: AsyncSession,
    account_id: int,
    as_of_date: Optional[datetime] = None
) -> Decimal:
    result = await db.execute(
        select(Account).where(Account.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise ValueError("Account not found")

    return account.current_balance


async def get_trial_balance(db: AsyncSession) -> List[dict]:
    result = await db.execute(
        select(Account, AccountType)
        .join(AccountType, Account.account_type_id == AccountType.id)
        .where(Account.is_active == True)
        .order_by(Account.code)
    )

    trial_balance = []
    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for account, account_type in result:
        balance = account.current_balance
        debit = balance if balance > 0 and account_type.normal_balance == "debit" else Decimal("0")
        credit = abs(balance) if balance < 0 and account_type.normal_balance == "debit" else Decimal("0")

        if account_type.normal_balance == "credit":
            debit = abs(balance) if balance < 0 else Decimal("0")
            credit = balance if balance > 0 else Decimal("0")

        if balance != 0:
            trial_balance.append({
                "account_id": account.id,
                "account_code": account.code,
                "account_name": account.name,
                "account_type": account_type.category.value,
                "debit": debit if debit != 0 else None,
                "credit": credit if credit != 0 else None
            })
            total_debit += debit
            total_credit += credit

    return {
        "accounts": trial_balance,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": total_debit == total_credit
    }
