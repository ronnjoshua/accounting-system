from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.ar import Customer, Invoice, InvoiceStatus, CustomerPayment, CreditNote
from app.models.ap import Vendor, Bill, BillStatus, VendorPayment, DebitNote
from app.models.accounting import Account, JournalEntry, JournalEntryLine, JournalEntryStatus
from app.schemas.payments import (
    CustomerPaymentCreate, CustomerPaymentResponse,
    VendorPaymentCreate, VendorPaymentResponse,
    CreditNoteCreate, CreditNoteResponse,
    DebitNoteCreate, DebitNoteResponse
)

router = APIRouter()


# ============== Customer Payments ==============

def get_next_customer_payment_number(db: Session) -> str:
    result = db.execute(select(func.count(CustomerPayment.id)))
    count = result.scalar() or 0
    return f"RCPT-{count + 1:06d}"


def get_default_ar_account(db: Session) -> int:
    """Get default Accounts Receivable account"""
    result = db.execute(
        select(Account).where(Account.code.like("1200%")).where(Account.is_active == True).limit(1)
    )
    account = result.scalar_one_or_none()
    if account:
        return account.id
    # Fallback to any asset account
    result = db.execute(
        select(Account).where(Account.code.like("1%")).where(Account.is_active == True).limit(1)
    )
    account = result.scalar_one_or_none()
    if account:
        return account.id
    raise HTTPException(status_code=400, detail="No AR account found")


@router.get("/customer-payments", response_model=List[CustomerPaymentResponse])
def list_customer_payments(
    customer_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(CustomerPayment)

    if customer_id:
        query = query.where(CustomerPayment.customer_id == customer_id)
    if start_date:
        query = query.where(CustomerPayment.payment_date >= start_date)
    if end_date:
        query = query.where(CustomerPayment.payment_date <= end_date)

    query = query.order_by(CustomerPayment.payment_date.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("/customer-payments", response_model=CustomerPaymentResponse)
def create_customer_payment(
    data: CustomerPaymentCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    # Validate customer exists
    customer = db.execute(select(Customer).where(Customer.id == data.customer_id)).scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Validate bank account
    bank_account = db.execute(select(Account).where(Account.id == data.bank_account_id)).scalar_one_or_none()
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")

    # Validate invoice if provided
    invoice = None
    if data.invoice_id:
        invoice = db.execute(select(Invoice).where(Invoice.id == data.invoice_id)).scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice.customer_id != data.customer_id:
            raise HTTPException(status_code=400, detail="Invoice does not belong to this customer")
        if invoice.status == InvoiceStatus.paid:
            raise HTTPException(status_code=400, detail="Invoice is already fully paid")
        if invoice.status == InvoiceStatus.void:
            raise HTTPException(status_code=400, detail="Cannot pay a voided invoice")

    payment_number = get_next_customer_payment_number(db)

    # Create payment
    payment = CustomerPayment(
        payment_number=payment_number,
        customer_id=data.customer_id,
        payment_date=data.payment_date,
        amount=data.amount,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        payment_method=data.payment_method,
        reference=data.reference,
        notes=data.notes,
        bank_account_id=data.bank_account_id,
        invoice_id=data.invoice_id,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(payment)

    # Update invoice if linked
    if invoice:
        invoice.amount_paid += data.amount
        invoice.balance_due = invoice.total - invoice.amount_paid

        if invoice.balance_due <= 0:
            invoice.status = InvoiceStatus.paid
            invoice.balance_due = Decimal("0")
        else:
            invoice.status = InvoiceStatus.partially_paid

    # Create journal entry for the payment
    ar_account_id = customer.receivable_account_id or get_default_ar_account(db)

    je_number_result = db.execute(select(func.count(JournalEntry.id)))
    je_count = je_number_result.scalar() or 0
    je_number = f"JE-{je_count + 1:06d}"

    journal_entry = JournalEntry(
        entry_number=je_number,
        entry_date=data.payment_date,
        description=f"Customer payment {payment_number} from {customer.name}",
        reference=data.reference,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        source_type="customer_payment",
        source_id=None,  # Will update after commit
        status=JournalEntryStatus.posted,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
        posted_by_id=current_user.id
    )
    db.add(journal_entry)
    db.flush()

    # Debit Bank, Credit AR
    base_amount = data.amount * data.exchange_rate

    line1 = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=data.bank_account_id,
        description=f"Payment received from {customer.name}",
        debit=data.amount,
        credit=Decimal("0"),
        base_debit=base_amount,
        base_credit=Decimal("0")
    )
    line2 = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=ar_account_id,
        description=f"Payment received from {customer.name}",
        debit=Decimal("0"),
        credit=data.amount,
        base_debit=Decimal("0"),
        base_credit=base_amount
    )
    db.add(line1)
    db.add(line2)

    # Update account balances
    bank_account.current_balance += base_amount
    ar_account = db.execute(select(Account).where(Account.id == ar_account_id)).scalar_one()
    ar_account.current_balance -= base_amount

    payment.journal_entry_id = journal_entry.id

    db.commit()
    db.refresh(payment)
    return payment


@router.get("/customer-payments/{payment_id}", response_model=CustomerPaymentResponse)
def get_customer_payment(
    payment_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(CustomerPayment).where(CustomerPayment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


# ============== Vendor Payments ==============

def get_next_vendor_payment_number(db: Session) -> str:
    result = db.execute(select(func.count(VendorPayment.id)))
    count = result.scalar() or 0
    return f"PMT-{count + 1:06d}"


def get_default_ap_account(db: Session) -> int:
    """Get default Accounts Payable account"""
    result = db.execute(
        select(Account).where(Account.code.like("2000%")).where(Account.is_active == True).limit(1)
    )
    account = result.scalar_one_or_none()
    if account:
        return account.id
    # Fallback to any liability account
    result = db.execute(
        select(Account).where(Account.code.like("2%")).where(Account.is_active == True).limit(1)
    )
    account = result.scalar_one_or_none()
    if account:
        return account.id
    raise HTTPException(status_code=400, detail="No AP account found")


@router.get("/vendor-payments", response_model=List[VendorPaymentResponse])
def list_vendor_payments(
    vendor_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(VendorPayment)

    if vendor_id:
        query = query.where(VendorPayment.vendor_id == vendor_id)
    if start_date:
        query = query.where(VendorPayment.payment_date >= start_date)
    if end_date:
        query = query.where(VendorPayment.payment_date <= end_date)

    query = query.order_by(VendorPayment.payment_date.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("/vendor-payments", response_model=VendorPaymentResponse)
def create_vendor_payment(
    data: VendorPaymentCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    # Validate vendor exists
    vendor = db.execute(select(Vendor).where(Vendor.id == data.vendor_id)).scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Validate bank account
    bank_account = db.execute(select(Account).where(Account.id == data.bank_account_id)).scalar_one_or_none()
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")

    # Validate bill if provided
    bill = None
    if data.bill_id:
        bill = db.execute(select(Bill).where(Bill.id == data.bill_id)).scalar_one_or_none()
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        if bill.vendor_id != data.vendor_id:
            raise HTTPException(status_code=400, detail="Bill does not belong to this vendor")
        if bill.status == BillStatus.paid:
            raise HTTPException(status_code=400, detail="Bill is already fully paid")
        if bill.status == BillStatus.void:
            raise HTTPException(status_code=400, detail="Cannot pay a voided bill")

    payment_number = get_next_vendor_payment_number(db)

    # Create payment
    payment = VendorPayment(
        payment_number=payment_number,
        vendor_id=data.vendor_id,
        payment_date=data.payment_date,
        amount=data.amount,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        payment_method=data.payment_method,
        reference=data.reference,
        notes=data.notes,
        bank_account_id=data.bank_account_id,
        bill_id=data.bill_id,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(payment)

    # Update bill if linked
    if bill:
        bill.amount_paid += data.amount
        bill.balance_due = bill.total - bill.amount_paid

        if bill.balance_due <= 0:
            bill.status = BillStatus.paid
            bill.balance_due = Decimal("0")
        else:
            bill.status = BillStatus.partially_paid

    # Create journal entry for the payment
    ap_account_id = vendor.payable_account_id or get_default_ap_account(db)

    je_number_result = db.execute(select(func.count(JournalEntry.id)))
    je_count = je_number_result.scalar() or 0
    je_number = f"JE-{je_count + 1:06d}"

    journal_entry = JournalEntry(
        entry_number=je_number,
        entry_date=data.payment_date,
        description=f"Vendor payment {payment_number} to {vendor.name}",
        reference=data.reference,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        source_type="vendor_payment",
        source_id=None,
        status=JournalEntryStatus.posted,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
        posted_by_id=current_user.id
    )
    db.add(journal_entry)
    db.flush()

    # Debit AP, Credit Bank
    base_amount = data.amount * data.exchange_rate

    line1 = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=ap_account_id,
        description=f"Payment to {vendor.name}",
        debit=data.amount,
        credit=Decimal("0"),
        base_debit=base_amount,
        base_credit=Decimal("0")
    )
    line2 = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=data.bank_account_id,
        description=f"Payment to {vendor.name}",
        debit=Decimal("0"),
        credit=data.amount,
        base_debit=Decimal("0"),
        base_credit=base_amount
    )
    db.add(line1)
    db.add(line2)

    # Update account balances
    bank_account.current_balance -= base_amount
    ap_account = db.execute(select(Account).where(Account.id == ap_account_id)).scalar_one()
    ap_account.current_balance -= base_amount

    payment.journal_entry_id = journal_entry.id

    db.commit()
    db.refresh(payment)
    return payment


@router.get("/vendor-payments/{payment_id}", response_model=VendorPaymentResponse)
def get_vendor_payment(
    payment_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(VendorPayment).where(VendorPayment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


# ============== Credit Notes ==============

def get_next_credit_note_number(db: Session) -> str:
    result = db.execute(select(func.count(CreditNote.id)))
    count = result.scalar() or 0
    return f"CN-{count + 1:06d}"


@router.get("/credit-notes", response_model=List[CreditNoteResponse])
def list_credit_notes(
    customer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(CreditNote)
    if customer_id:
        query = query.where(CreditNote.customer_id == customer_id)
    query = query.order_by(CreditNote.credit_date.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("/credit-notes", response_model=CreditNoteResponse)
def create_credit_note(
    data: CreditNoteCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    # Validate customer
    customer = db.execute(select(Customer).where(Customer.id == data.customer_id)).scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Validate invoice if provided
    invoice = None
    if data.invoice_id:
        invoice = db.execute(select(Invoice).where(Invoice.id == data.invoice_id)).scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice.customer_id != data.customer_id:
            raise HTTPException(status_code=400, detail="Invoice does not belong to this customer")

    credit_note_number = get_next_credit_note_number(db)

    credit_note = CreditNote(
        credit_note_number=credit_note_number,
        customer_id=data.customer_id,
        invoice_id=data.invoice_id,
        credit_date=data.credit_date,
        amount=data.amount,
        reason=data.reason,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(credit_note)

    # If linked to invoice, reduce the balance due
    if invoice:
        invoice.balance_due -= data.amount
        if invoice.balance_due <= 0:
            invoice.status = InvoiceStatus.paid
            invoice.balance_due = Decimal("0")

    # Create journal entry (Debit Revenue/Sales Returns, Credit AR)
    ar_account_id = customer.receivable_account_id or get_default_ar_account(db)

    # Try to find a sales returns account (typically 4xxx range)
    revenue_account = db.execute(
        select(Account).where(Account.code.like("4%")).where(Account.is_active == True).limit(1)
    ).scalar_one_or_none()
    revenue_account_id = revenue_account.id if revenue_account else ar_account_id

    je_number_result = db.execute(select(func.count(JournalEntry.id)))
    je_count = je_number_result.scalar() or 0
    je_number = f"JE-{je_count + 1:06d}"

    journal_entry = JournalEntry(
        entry_number=je_number,
        entry_date=data.credit_date,
        description=f"Credit note {credit_note_number} for {customer.name}",
        reference=credit_note_number,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        source_type="credit_note",
        status=JournalEntryStatus.posted,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
        posted_by_id=current_user.id
    )
    db.add(journal_entry)
    db.flush()

    base_amount = data.amount * data.exchange_rate

    # Debit Sales Returns, Credit AR
    line1 = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=revenue_account_id,
        description=f"Credit note for {customer.name}: {data.reason}",
        debit=data.amount,
        credit=Decimal("0"),
        base_debit=base_amount,
        base_credit=Decimal("0")
    )
    line2 = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=ar_account_id,
        description=f"Credit note for {customer.name}: {data.reason}",
        debit=Decimal("0"),
        credit=data.amount,
        base_debit=Decimal("0"),
        base_credit=base_amount
    )
    db.add(line1)
    db.add(line2)

    credit_note.journal_entry_id = journal_entry.id

    db.commit()
    db.refresh(credit_note)
    return credit_note


@router.get("/credit-notes/{credit_note_id}", response_model=CreditNoteResponse)
def get_credit_note(
    credit_note_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(CreditNote).where(CreditNote.id == credit_note_id))
    credit_note = result.scalar_one_or_none()
    if not credit_note:
        raise HTTPException(status_code=404, detail="Credit note not found")
    return credit_note


# ============== Debit Notes ==============

def get_next_debit_note_number(db: Session) -> str:
    result = db.execute(select(func.count(DebitNote.id)))
    count = result.scalar() or 0
    return f"DN-{count + 1:06d}"


@router.get("/debit-notes", response_model=List[DebitNoteResponse])
def list_debit_notes(
    vendor_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    query = select(DebitNote)
    if vendor_id:
        query = query.where(DebitNote.vendor_id == vendor_id)
    query = query.order_by(DebitNote.debit_date.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.post("/debit-notes", response_model=DebitNoteResponse)
def create_debit_note(
    data: DebitNoteCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    # Validate vendor
    vendor = db.execute(select(Vendor).where(Vendor.id == data.vendor_id)).scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Validate bill if provided
    bill = None
    if data.bill_id:
        bill = db.execute(select(Bill).where(Bill.id == data.bill_id)).scalar_one_or_none()
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        if bill.vendor_id != data.vendor_id:
            raise HTTPException(status_code=400, detail="Bill does not belong to this vendor")

    debit_note_number = get_next_debit_note_number(db)

    debit_note = DebitNote(
        debit_note_number=debit_note_number,
        vendor_id=data.vendor_id,
        bill_id=data.bill_id,
        debit_date=data.debit_date,
        amount=data.amount,
        reason=data.reason,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(debit_note)

    # If linked to bill, reduce the balance due
    if bill:
        bill.balance_due -= data.amount
        if bill.balance_due <= 0:
            bill.status = BillStatus.paid
            bill.balance_due = Decimal("0")

    # Create journal entry (Debit AP, Credit Purchase Returns/Expense)
    ap_account_id = vendor.payable_account_id or get_default_ap_account(db)

    # Try to find an expense account
    expense_account = db.execute(
        select(Account).where(Account.code.like("5%")).where(Account.is_active == True).limit(1)
    ).scalar_one_or_none()
    expense_account_id = expense_account.id if expense_account else ap_account_id

    je_number_result = db.execute(select(func.count(JournalEntry.id)))
    je_count = je_number_result.scalar() or 0
    je_number = f"JE-{je_count + 1:06d}"

    journal_entry = JournalEntry(
        entry_number=je_number,
        entry_date=data.debit_date,
        description=f"Debit note {debit_note_number} for {vendor.name}",
        reference=debit_note_number,
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        source_type="debit_note",
        status=JournalEntryStatus.posted,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
        posted_by_id=current_user.id
    )
    db.add(journal_entry)
    db.flush()

    base_amount = data.amount * data.exchange_rate

    # Debit AP, Credit Expense
    line1 = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=ap_account_id,
        description=f"Debit note for {vendor.name}: {data.reason}",
        debit=data.amount,
        credit=Decimal("0"),
        base_debit=base_amount,
        base_credit=Decimal("0")
    )
    line2 = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=expense_account_id,
        description=f"Debit note for {vendor.name}: {data.reason}",
        debit=Decimal("0"),
        credit=data.amount,
        base_debit=Decimal("0"),
        base_credit=base_amount
    )
    db.add(line1)
    db.add(line2)

    debit_note.journal_entry_id = journal_entry.id

    db.commit()
    db.refresh(debit_note)
    return debit_note


@router.get("/debit-notes/{debit_note_id}", response_model=DebitNoteResponse)
def get_debit_note(
    debit_note_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(DebitNote).where(DebitNote.id == debit_note_id))
    debit_note = result.scalar_one_or_none()
    if not debit_note:
        raise HTTPException(status_code=404, detail="Debit note not found")
    return debit_note
