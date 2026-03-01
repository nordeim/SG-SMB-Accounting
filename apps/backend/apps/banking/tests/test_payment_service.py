"""
Payment Service Tests (TDD)

Tests for PaymentService operations.
Run with: pytest apps/banking/tests/test_payment_service.py -v

SEC-001 Remediation: Tests validate all security controls.
"""

import pytest
import uuid
from datetime import date
from decimal import Decimal
from django.contrib.auth.hashers import make_password

from apps.core.models import (
    AppUser,
    Organisation,
    Role,
    UserOrganisation,
    Account,
    Contact,
    BankAccount,
    Payment,
    PaymentAllocation,
    InvoiceDocument,
    FiscalYear,
    FiscalPeriod,
    AuditEventLog,
)
from apps.banking.services import PaymentService
from common.exceptions import ValidationError, ResourceNotFound


pytestmark = pytest.mark.django_db


@pytest.fixture
def test_user():
    """Create and return a test user."""
    user_id = uuid.uuid4()
    user = AppUser.objects.create(
        id=user_id,
        email=f"payment_test_{user_id.hex[:8]}@example.com",
        full_name="Payment Test User",
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
        name="Payment Test Org",
        legal_name="Payment Test Org Pte Ltd",
        uen="PAYTEST01",
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

    # Seed document sequences for banking tests
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

    # Create fiscal year and period for 2024
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
def ap_account(test_org):
    """Create Accounts Payable account."""
    return Account.objects.create(
        org=test_org,
        code="2100",
        name="Accounts Payable",
        account_type="LIABILITY",
        description="Accounts Payable",
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


@pytest.fixture
def supplier(test_org, ap_account):
    """Create a supplier contact with AP account."""
    return Contact.objects.create(
        org=test_org,
        contact_type="SUPPLIER",
        name="Test Supplier Pte Ltd",
        company_name="Test Supplier Pte Ltd",
        email="supplier@test.com",
        is_customer=False,
        is_supplier=True,
        payment_terms_days=30,
        payable_account=ap_account,
    )


class TestPaymentServiceCreateReceived:
    """Tests for PaymentService.create_received()"""

    def test_create_received_payment_success(self, test_org, bank_account, customer, test_user):
        """Test successful customer payment creation."""
        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("1000.00"),
            "currency": "SGD",
            "exchange_rate": Decimal("1.000000"),
            "payment_method": "BANK_TRANSFER",
            "payment_reference": "REF-001",
            "notes": "Test payment",
        }

        payment = PaymentService.create_received(
            org_id=test_org.id,
            data=data,
            user_id=test_user.id,
        )

        assert payment.id is not None
        assert payment.payment_type == "RECEIVED"
        assert payment.payment_number.startswith("RCP-")
        assert payment.amount == Decimal("1000.0000")
        assert payment.base_amount == Decimal("1000.0000")
        assert payment.contact == customer
        assert payment.bank_account == bank_account
        assert payment.currency == "SGD"
        assert payment.is_voided is False

    def test_create_received_payment_generates_number(
        self, test_org, bank_account, customer, test_user
    ):
        """Test that payment numbers are unique and sequential."""
        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("100.00"),
            "payment_method": "BANK_TRANSFER",
        }

        payment1 = PaymentService.create_received(
            org_id=test_org.id, data=data, user_id=test_user.id
        )
        payment2 = PaymentService.create_received(
            org_id=test_org.id, data=data, user_id=test_user.id
        )

        assert payment1.payment_number != payment2.payment_number
        assert payment1.payment_number.startswith("RCP-")
        assert payment2.payment_number.startswith("RCP-")

    def test_create_received_payment_audit_logged(
        self, test_org, bank_account, customer, test_user
    ):
        """Test that payment creation is audit logged."""
        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("500.00"),
            "payment_method": "PAYNOW",
        }

        payment = PaymentService.create_received(
            org_id=test_org.id,
            data=data,
            user_id=test_user.id,
        )

        audit_log = AuditEventLog.objects.filter(
            org_id=test_org.id,
            entity_table="payment",
            entity_id=payment.id,
            action="CREATE",
            user_id__isnull=False,  # Service-created record has explicit user_id
        ).first()

        assert audit_log is not None
        assert audit_log.user_id == test_user.id


class TestPaymentServiceCreateMade:
    """Tests for PaymentService.create_made()"""

    def test_create_made_payment_success(self, test_org, bank_account, supplier, test_user):
        """Test successful supplier payment creation."""
        data = {
            "contact_id": supplier.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("2000.00"),
            "currency": "SGD",
            "exchange_rate": Decimal("1.000000"),
            "payment_method": "GIRO",
            "payment_reference": "GIRO-001",
        }

        payment = PaymentService.create_made(
            org_id=test_org.id,
            data=data,
            user_id=test_user.id,
        )

        assert payment.id is not None
        assert payment.payment_type == "MADE"
        assert payment.payment_number.startswith("PAY-")
        assert payment.amount == Decimal("2000.0000")
        assert payment.contact == supplier

    def test_create_made_payment_number_format(self, test_org, bank_account, supplier, test_user):
        """Test that supplier payments use PAY- prefix."""
        data = {
            "contact_id": supplier.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("100.00"),
            "payment_method": "BANK_TRANSFER",
        }

        payment = PaymentService.create_made(org_id=test_org.id, data=data, user_id=test_user.id)

        assert payment.payment_number.startswith("PAY-")


class TestPaymentServiceList:
    """Tests for PaymentService.list()"""

    def test_list_payments_filter_by_type(
        self, test_org, bank_account, customer, supplier, test_user
    ):
        """Test filtering by payment type."""
        received_data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("100.00"),
            "payment_method": "BANK_TRANSFER",
        }
        PaymentService.create_received(org_id=test_org.id, data=received_data, user_id=test_user.id)

        made_data = {
            "contact_id": supplier.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("200.00"),
            "payment_method": "BANK_TRANSFER",
        }
        PaymentService.create_made(org_id=test_org.id, data=made_data, user_id=test_user.id)

        received_payments = PaymentService.list(org_id=test_org.id, payment_type="RECEIVED")
        made_payments = PaymentService.list(org_id=test_org.id, payment_type="MADE")

        assert len(received_payments) == 1
        assert received_payments[0].payment_type == "RECEIVED"
        assert len(made_payments) == 1
        assert made_payments[0].payment_type == "MADE"


class TestPaymentServiceGet:
    """Tests for PaymentService.get()"""

    def test_get_payment_success(self, test_org, bank_account, customer, test_user):
        """Test getting a single payment."""
        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("100.00"),
            "payment_method": "BANK_TRANSFER",
        }
        created = PaymentService.create_received(
            org_id=test_org.id, data=data, user_id=test_user.id
        )

        retrieved = PaymentService.get(org_id=test_org.id, payment_id=created.id)

        assert retrieved.id == created.id
        assert retrieved.payment_number == created.payment_number

    def test_get_payment_not_found(self, test_org):
        """Test getting non-existent payment."""
        with pytest.raises(ResourceNotFound):
            PaymentService.get(org_id=test_org.id, payment_id=uuid.uuid4())


class TestPaymentServiceVoid:
    """Tests for PaymentService.void()"""

    def test_void_payment_success(self, test_org, bank_account, customer, test_user):
        """Test voiding a payment."""
        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("100.00"),
            "payment_method": "BANK_TRANSFER",
        }
        payment = PaymentService.create_received(
            org_id=test_org.id, data=data, user_id=test_user.id
        )

        voided = PaymentService.void(
            org_id=test_org.id,
            payment_id=payment.id,
            reason="Duplicate payment",
            user_id=test_user.id,
        )

        assert voided.is_voided is True
        assert "Duplicate payment" in voided.notes

    def test_void_already_voided_payment_fails(
        self, test_org, bank_account, customer, test_user, fiscal_period
    ):
        """Test that voiding an already voided payment fails."""
        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("100.00"),
            "payment_method": "BANK_TRANSFER",
        }
        payment = PaymentService.create_received(
            org_id=test_org.id, data=data, user_id=test_user.id
        )

        PaymentService.void(
            org_id=test_org.id,
            payment_id=payment.id,
            reason="First void",
            user_id=test_user.id,
        )

        with pytest.raises(ValidationError) as exc_info:
            PaymentService.void(
                org_id=test_org.id,
                payment_id=payment.id,
                reason="Second void",
                user_id=test_user.id,
            )

        assert "already voided" in str(exc_info.value).lower()

    def test_void_payment_audit_logged(
        self, test_org, bank_account, customer, test_user, fiscal_period
    ):
        """Test that voiding is audit logged."""
        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("100.00"),
            "payment_method": "BANK_TRANSFER",
        }
        payment = PaymentService.create_received(
            org_id=test_org.id, data=data, user_id=test_user.id
        )

        PaymentService.void(
            org_id=test_org.id,
            payment_id=payment.id,
            reason="Test void",
            user_id=test_user.id,
        )

        audit_log = AuditEventLog.objects.filter(
            org_id=test_org.id,
            entity_table="payment",
            entity_id=payment.id,
            action="VOID",
        ).first()

        assert audit_log is not None


class TestPaymentServiceAllocate:
    """Tests for PaymentService.allocate()"""

    def test_allocate_payment_to_invoice(self, test_org, bank_account, customer, test_user):
        """Test allocating payment to an invoice."""
        invoice = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-00001",
            contact=customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal("1000.0000"),
            gst_total=Decimal("90.0000"),
            total_incl=Decimal("1090.0000"),
            status="APPROVED",
        )

        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("1090.00"),
            "payment_method": "BANK_TRANSFER",
        }
        payment = PaymentService.create_received(
            org_id=test_org.id, data=data, user_id=test_user.id
        )

        PaymentService.allocate(
            org_id=test_org.id,
            payment_id=payment.id,
            allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("1090.00")}],
            user_id=test_user.id,
        )

        allocations = PaymentService.get_allocations(payment_id=payment.id)
        assert len(allocations) == 1
        assert allocations[0].allocated_amount == Decimal("1090.0000")

    def test_allocate_exceeds_payment_amount_fails(
        self, test_org, bank_account, customer, test_user, fiscal_period
    ):
        """Test that allocation exceeding payment amount fails."""
        invoice = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-00002",
            contact=customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal("1000.0000"),
            gst_total=Decimal("90.0000"),
            total_incl=Decimal("1090.0000"),
            status="APPROVED",
        )

        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("500.00"),
            "payment_method": "BANK_TRANSFER",
        }
        payment = PaymentService.create_received(
            org_id=test_org.id, data=data, user_id=test_user.id
        )

        with pytest.raises(ValidationError) as exc_info:
            PaymentService.allocate(
                org_id=test_org.id,
                payment_id=payment.id,
                allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("600.00")}],
                user_id=test_user.id,
            )

        assert "exceed" in str(exc_info.value).lower()

    def test_allocate_to_wrong_contact_fails(
        self, test_org, bank_account, customer, test_user, fiscal_period, ar_account
    ):
        """Test that allocating to different contact's invoice fails."""
        other_customer = Contact.objects.create(
            org=test_org,
            contact_type="CUSTOMER",
            name="Other Customer",
            is_customer=True,
            payment_terms_days=30,
            receivable_account=ar_account,
        )

        invoice = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-00003",
            contact=other_customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal("100.0000"),
            gst_total=Decimal("9.0000"),
            total_incl=Decimal("109.0000"),
            status="APPROVED",
        )

        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("200.00"),
            "payment_method": "BANK_TRANSFER",
        }
        payment = PaymentService.create_received(
            org_id=test_org.id, data=data, user_id=test_user.id
        )

        with pytest.raises(ValidationError) as exc_info:
            PaymentService.allocate(
                org_id=test_org.id,
                payment_id=payment.id,
                allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("100.00")}],
                user_id=test_user.id,
            )

        assert "contact" in str(exc_info.value).lower()


class TestPaymentMultiCurrency:
    """Tests for multi-currency payment handling."""

    def test_multi_currency_payment_base_amount(self, test_org, bank_account, customer, test_user):
        """Test that base_amount is calculated correctly for foreign currency."""
        data = {
            "contact_id": customer.id,
            "bank_account_id": bank_account.id,
            "payment_date": date(2024, 1, 15),
            "amount": Decimal("1000.00"),
            "currency": "USD",
            "exchange_rate": Decimal("1.350000"),
            "payment_method": "BANK_TRANSFER",
        }

        payment = PaymentService.create_received(
            org_id=test_org.id, data=data, user_id=test_user.id
        )

        assert payment.currency == "USD"
        assert payment.exchange_rate == Decimal("1.350000")
        assert payment.base_amount == Decimal("1350.0000")
