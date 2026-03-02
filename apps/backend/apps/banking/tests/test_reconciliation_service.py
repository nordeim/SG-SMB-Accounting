"""
Reconciliation Service Tests (TDD)

Tests for ReconciliationService operations.
Run with: pytest apps/banking/tests/test_reconciliation_service.py -v

SEC-001 Remediation: Tests validate all security controls.
"""

import pytest
import uuid
from datetime import date
from decimal import Decimal
from django.contrib.auth.hashers import make_password
from io import BytesIO

from apps.core.models import (
    AppUser,
    Organisation,
    Role,
    UserOrganisation,
    Account,
    Contact,
    BankAccount,
    BankTransaction,
    Payment,
    FiscalYear,
    FiscalPeriod,
)
from apps.banking.services import ReconciliationService, PaymentService
from common.exceptions import ValidationError, ResourceNotFound


pytestmark = pytest.mark.django_db


@pytest.fixture
def test_user():
    """Create and return a test user."""
    user_id = uuid.uuid4()
    user = AppUser.objects.create(
        id=user_id,
        email=f"recon_test_{user_id.hex[:8]}@example.com",
        full_name="Reconciliation Test User",
        is_active=True,
    )
    user.password = make_password("testpassword123")
    user.save()
    return user


@pytest.fixture
def test_org(test_user):
    """Create organisation for testing."""
    org_id = uuid.uuid4()
    org = Organisation.objects.create(
        id=org_id,
        name="Reconciliation Test Org",
        legal_name="Reconciliation Test Org Pte Ltd",
        uen="RECONTEST",
        entity_type="PRIVATE_LIMITED",
        gst_registered=True,
        gst_reg_number="M12345678",
        gst_reg_date=date(2024, 1, 1),
        fy_start_month=1,
        base_currency="SGD",
        is_active=True,
    )

    owner_role = Role.objects.create(
        org=org,
        name="Owner",
        description="Full access",
        can_manage_org=True,
        can_manage_users=True,
        can_manage_coa=True,
        can_create_invoices=True,
        can_approve_invoices=True,
        can_void_invoices=True,
        can_create_journals=True,
        can_manage_banking=True,
        can_file_gst=True,
        can_view_reports=True,
        can_export_data=True,
        is_system=True,
    )

    UserOrganisation.objects.create(
        user=test_user,
        org=org,
        role=owner_role,
        is_default=True,
    )

    # Seed document sequences
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO core.document_sequence
                (org_id, document_type, prefix, next_number, padding)
            VALUES
                (%s, 'PAYMENT_RECEIVED', 'RCP-', 1, 5),
                (%s, 'PAYMENT_MADE', 'PAY-', 1, 5),
                (%s, 'SALES_INVOICE', 'INV-', 1, 5),
                (%s, 'JOURNAL_ENTRY', 'JE-', 1, 6)
            ON CONFLICT (org_id, document_type) DO NOTHING
            """,
            [str(org_id), str(org_id), str(org_id), str(org_id)],
        )

    # Create fiscal year and period
    fiscal_year = FiscalYear.objects.create(
        org=org,
        label="FY2024",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        is_closed=False,
    )
    FiscalPeriod.objects.create(
        org=org,
        fiscal_year_id=fiscal_year.id,
        label="Jan 2024",
        period_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        is_open=True,
    )

    return org


@pytest.fixture
def gl_account(test_org):
    """Create a GL account for bank accounts."""
    return Account.objects.create(
        org=test_org,
        code="1100",
        name="DBS Bank Account",
        account_type="ASSET",
        description="Main DBS Bank Account",
        is_active=True,
        is_bank=True,
    )


@pytest.fixture
def ar_account(test_org):
    """Create Accounts Receivable account."""
    return Account.objects.create(
        org=test_org,
        code="1200",
        name="Accounts Receivable",
        account_type="ASSET",
        description="Accounts Receivable",
        is_active=True,
    )


@pytest.fixture
def bank_account(test_org, gl_account):
    """Create a bank account."""
    return BankAccount.objects.create(
        org=test_org,
        account_name="Main Operating Account",
        bank_name="DBS Bank",
        account_number="1234567890",
        gl_account=gl_account,
        is_active=True,
        paynow_type=None,
        paynow_id=None,
    )


@pytest.fixture
def customer(test_org, ar_account):
    """Create a customer contact with AR account."""
    return Contact.objects.create(
        org=test_org,
        contact_type="CUSTOMER",
        name="Test Customer Pte Ltd",
        company_name="Test Customer Pte Ltd",
        email="customer@test.com",
        is_customer=True,
        is_supplier=False,
        payment_terms_days=30,
        receivable_account=ar_account,
    )


class TestReconciliationService:
    """Tests for ReconciliationService operations."""

    def test_import_transactions_success(self, test_org, bank_account, test_user):
        """Test successful import of bank transactions from CSV."""
        csv_content = b"""transaction_date,amount,description,reference
2024-01-15,1000.00,Payment from Customer A,REF-001
2024-01-16,-500.00,Payment to Supplier B,REF-002
2024-01-17,250.00,Interest Credit,
"""
        csv_file = BytesIO(csv_content)

        result = ReconciliationService.import_csv(
            org_id=test_org.id,
            bank_account_id=bank_account.id,
            csv_file=csv_file,
            user_id=test_user.id,
        )

        assert result["imported"] == 3
        assert result["skipped"] == 0
        assert len(result["errors"]) == 0
        assert result["batch_id"] is not None

        # Verify transactions created
        transactions = ReconciliationService.list_transactions(
            org_id=test_org.id,
            bank_account_id=bank_account.id,
        )
        assert len(transactions) == 3

        # Verify first transaction
        first_txn = transactions[0]
        assert first_txn.amount == Decimal("250.0000")
        assert first_txn.description == "Interest Credit"
        assert first_txn.is_reconciled is False
        assert first_txn.import_source == "CSV"

    def test_reconcile_transaction_to_payment(self, test_org, bank_account, customer, test_user):
        """Test reconciling a bank transaction to a payment."""
        # Create payment
        payment = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 15),
                "amount": Decimal("1000.00"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        # Create bank transaction
        transaction = BankTransaction.objects.create(
            org=test_org,
            bank_account=bank_account,
            transaction_date=date(2024, 1, 15),
            description="Payment from Customer",
            amount=Decimal("1000.0000"),
            is_reconciled=False,
        )

        # Reconcile
        reconciled = ReconciliationService.reconcile(
            org_id=test_org.id,
            transaction_id=transaction.id,
            payment_id=payment.id,
            user_id=test_user.id,
        )

        assert reconciled.is_reconciled is True
        assert reconciled.matched_payment == payment
        assert reconciled.reconciled_at is not None

        # Verify payment also marked as reconciled
        payment.refresh_from_db()
        assert payment.is_reconciled is True

    def test_unreconcile_transaction(self, test_org, bank_account, customer, test_user):
        """Test removing reconciliation from a transaction."""
        # Create payment and transaction
        payment = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 15),
                "amount": Decimal("500.00"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        transaction = BankTransaction.objects.create(
            org=test_org,
            bank_account=bank_account,
            transaction_date=date(2024, 1, 15),
            description="Payment",
            amount=Decimal("500.0000"),
            is_reconciled=False,
        )

        # Reconcile first
        ReconciliationService.reconcile(
            org_id=test_org.id,
            transaction_id=transaction.id,
            payment_id=payment.id,
            user_id=test_user.id,
        )

        # Unreconcile
        unreconciled = ReconciliationService.unreconcile(
            org_id=test_org.id,
            transaction_id=transaction.id,
            user_id=test_user.id,
        )

        assert unreconciled.is_reconciled is False
        assert unreconciled.matched_payment is None
        assert unreconciled.reconciled_at is None

        # Verify payment also unreconciled
        payment.refresh_from_db()
        assert payment.is_reconciled is False

    def test_list_unreconciled_transactions(self, test_org, bank_account, customer, test_user):
        """Test listing only unreconciled transactions."""
        # Create payment
        payment = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 15),
                "amount": Decimal("1000.00"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        # Create multiple transactions
        txn1 = BankTransaction.objects.create(
            org=test_org,
            bank_account=bank_account,
            transaction_date=date(2024, 1, 15),
            description="Reconciled TXN",
            amount=Decimal("1000.0000"),
            is_reconciled=False,
        )

        txn2 = BankTransaction.objects.create(
            org=test_org,
            bank_account=bank_account,
            transaction_date=date(2024, 1, 16),
            description="Unreconciled TXN",
            amount=Decimal("500.0000"),
            is_reconciled=False,
        )

        # Reconcile one
        ReconciliationService.reconcile(
            org_id=test_org.id,
            transaction_id=txn1.id,
            payment_id=payment.id,
            user_id=test_user.id,
        )

        # List unreconciled
        unreconciled = ReconciliationService.list_transactions(
            org_id=test_org.id,
            bank_account_id=bank_account.id,
            unreconciled_only=True,
        )

        assert len(unreconciled) == 1
        assert unreconciled[0].id == txn2.id

    def test_import_duplicate_detection(self, test_org, bank_account, test_user):
        """Test that duplicate transactions are skipped on import."""
        # Import first batch
        csv_content1 = b"""transaction_date,amount,description
2024-01-15,1000.00,Payment from Customer
"""
        csv_file1 = BytesIO(csv_content1)

        result1 = ReconciliationService.import_csv(
            org_id=test_org.id,
            bank_account_id=bank_account.id,
            csv_file=csv_file1,
            user_id=test_user.id,
        )

        assert result1["imported"] == 1

        # Import duplicate
        csv_content2 = b"""transaction_date,amount,description
2024-01-15,1000.00,Payment from Customer
2024-01-16,500.00,Another Payment
"""
        csv_file2 = BytesIO(csv_content2)

        result2 = ReconciliationService.import_csv(
            org_id=test_org.id,
            bank_account_id=bank_account.id,
            csv_file=csv_file2,
            user_id=test_user.id,
        )

        # First should be skipped, second imported
        assert result2["imported"] == 1
        assert result2["skipped"] == 1

        # Verify total transactions
        transactions = ReconciliationService.list_transactions(
            org_id=test_org.id,
            bank_account_id=bank_account.id,
        )
        assert len(transactions) == 2

    def test_reconcile_amount_mismatch_fails(self, test_org, bank_account, customer, test_user):
        """Test that amount mismatch beyond tolerance fails."""
        # Create payment for $1000
        payment = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 15),
                "amount": Decimal("1000.00"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        # Create transaction for $900 (>$1 tolerance)
        transaction = BankTransaction.objects.create(
            org=test_org,
            bank_account=bank_account,
            transaction_date=date(2024, 1, 15),
            description="Payment",
            amount=Decimal("900.0000"),
            is_reconciled=False,
        )

        # Attempt reconcile - should fail
        with pytest.raises(ValidationError) as exc_info:
            ReconciliationService.reconcile(
                org_id=test_org.id,
                transaction_id=transaction.id,
                payment_id=payment.id,
                user_id=test_user.id,
            )

        assert "mismatch" in str(exc_info.value).lower()

    def test_reconcile_already_reconciled_fails(self, test_org, bank_account, customer, test_user):
        """Test that reconciling an already reconciled transaction fails."""
        # Create payment
        payment = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 15),
                "amount": Decimal("1000.00"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        # Create and reconcile transaction
        transaction = BankTransaction.objects.create(
            org=test_org,
            bank_account=bank_account,
            transaction_date=date(2024, 1, 15),
            description="Payment",
            amount=Decimal("1000.0000"),
            is_reconciled=False,
        )

        ReconciliationService.reconcile(
            org_id=test_org.id,
            transaction_id=transaction.id,
            payment_id=payment.id,
            user_id=test_user.id,
        )

        # Try to reconcile again
        payment2 = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 16),
                "amount": Decimal("1000.00"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        with pytest.raises(ValidationError) as exc_info:
            ReconciliationService.reconcile(
                org_id=test_org.id,
                transaction_id=transaction.id,
                payment_id=payment2.id,
                user_id=test_user.id,
            )

        assert "already reconciled" in str(exc_info.value).lower()
