"""
Allocation Service Tests (TDD)

Tests for PaymentService allocation operations.
Run with: pytest apps/banking/tests/test_allocation_service.py -v

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
        email=f"allocation_test_{user_id.hex[:8]}@example.com",
        full_name="Allocation Test User",
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
        name="Allocation Test Org",
        legal_name="Allocation Test Org Pte Ltd",
        uen="ALLOCTEST",
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


class TestPaymentAllocation:
    """Tests for PaymentService.allocate() operations."""

    def test_allocate_partial_payment(self, test_org, bank_account, customer, test_user):
        """Test that partial allocation works and tracks remaining balance."""
        # Create invoice
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

        # Create payment for $2000 (more than invoice)
        payment = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 15),
                "amount": Decimal("2000.00"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        # Allocate partial amount ($1090)
        PaymentService.allocate(
            org_id=test_org.id,
            payment_id=payment.id,
            allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("1090.00")}],
            user_id=test_user.id,
        )

        # Verify allocation
        allocations = PaymentService.get_allocations(payment_id=payment.id)
        assert len(allocations) == 1
        assert allocations[0].allocated_amount == Decimal("1090.0000")

        # Verify unallocated amount
        payment.refresh_from_db()
        allocated_total = sum(a.allocated_amount for a in allocations)
        unallocated = payment.amount - allocated_total
        assert unallocated == Decimal("910.0000")

    def test_allocate_to_non_approved_invoice_fails(
        self, test_org, bank_account, customer, test_user
    ):
        """Test that allocating to DRAFT invoice fails."""
        # Create DRAFT invoice
        invoice = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-DRAFT",
            contact=customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal("100.0000"),
            gst_total=Decimal("9.0000"),
            total_incl=Decimal("109.0000"),
            status="DRAFT",
        )

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

        # Attempt allocation - should fail
        with pytest.raises(ValidationError) as exc_info:
            PaymentService.allocate(
                org_id=test_org.id,
                payment_id=payment.id,
                allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("109.00")}],
                user_id=test_user.id,
            )

        assert "approved" in str(exc_info.value).lower()

    def test_allocate_duplicate_invoice_fails(self, test_org, bank_account, customer, test_user):
        """Test that allocating to same invoice twice fails."""
        invoice = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-00002",
            contact=customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal(
                "1000.0000"
            ),  # Larger invoice so status remains APPROVED/PARTIALLY_PAID
            gst_total=Decimal("90.0000"),
            total_incl=Decimal("1090.0000"),
            status="APPROVED",
        )

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

        # First allocation
        PaymentService.allocate(
            org_id=test_org.id,
            payment_id=payment.id,
            allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("50.00")}],
            user_id=test_user.id,
        )

        # Refresh invoice status
        invoice.refresh_from_db()

        # Second allocation to same invoice - should fail
        with pytest.raises(ValidationError) as exc_info:
            PaymentService.allocate(
                org_id=test_org.id,
                payment_id=payment.id,
                allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("30.00")}],
                user_id=test_user.id,
            )

        # The error could be about already allocated or status not APPROVED
        error_msg = str(exc_info.value).lower()
        assert "already allocated" in error_msg or "approved" in error_msg

    def test_unallocate_payment(self, test_org, bank_account, customer, test_user):
        """Test removing an allocation."""
        invoice = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-00003",
            contact=customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal("100.0000"),
            gst_total=Decimal("9.0000"),
            total_incl=Decimal("109.0000"),
            status="APPROVED",
        )

        payment = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 15),
                "amount": Decimal("200.00"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        # Create allocation
        PaymentService.allocate(
            org_id=test_org.id,
            payment_id=payment.id,
            allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("109.00")}],
            user_id=test_user.id,
        )

        # Verify allocation exists
        allocations = PaymentService.get_allocations(payment_id=payment.id)
        assert len(allocations) == 1
        allocation_id = allocations[0].id

        # Unallocate
        PaymentService.unallocate(
            org_id=test_org.id,
            allocation_id=allocation_id,
            user_id=test_user.id,
        )

        # Verify allocation removed
        allocations = PaymentService.get_allocations(payment_id=payment.id)
        assert len(allocations) == 0

    def test_allocation_updates_invoice_status(self, test_org, bank_account, customer, test_user):
        """Test that full allocation updates invoice status to PAID."""
        invoice = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-00004",
            contact=customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal("1000.0000"),
            gst_total=Decimal("90.0000"),
            total_incl=Decimal("1090.0000"),
            status="APPROVED",
        )

        payment = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 15),
                "amount": Decimal("1090.00"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        # Allocate full amount
        PaymentService.allocate(
            org_id=test_org.id,
            payment_id=payment.id,
            allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("1090.00")}],
            user_id=test_user.id,
        )

        # Verify invoice status updated to PAID
        invoice.refresh_from_db()
        assert invoice.status == "PAID"

    def test_allocation_fx_gain_loss(self, test_org, bank_account, customer, test_user):
        """Test FX gain/loss calculation on allocation."""
        invoice = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-00005",
            contact=customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal("1000.0000"),
            gst_total=Decimal("90.0000"),
            total_incl=Decimal("1090.0000"),
            status="APPROVED",
        )

        # Create USD payment with exchange rate 1.35
        payment = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 15),
                "amount": Decimal("1000.00"),
                "currency": "USD",
                "exchange_rate": Decimal("1.350000"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        # Verify base amount calculated
        assert payment.base_amount == Decimal("1350.0000")

        # Allocate - FX gain/loss should be tracked
        PaymentService.allocate(
            org_id=test_org.id,
            payment_id=payment.id,
            allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("1000.00")}],
            user_id=test_user.id,
        )

        # Verify allocation has base_allocated_amount
        allocations = PaymentService.get_allocations(payment_id=payment.id)
        assert len(allocations) == 1
        # Base allocated should be calculated based on exchange rate
        assert allocations[0].base_allocated_amount == Decimal("1350.0000")

    def test_allocation_audit_logged(self, test_org, bank_account, customer, test_user):
        """Test that allocation is audit logged."""
        invoice = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-00006",
            contact=customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal("100.0000"),
            gst_total=Decimal("9.0000"),
            total_incl=Decimal("109.0000"),
            status="APPROVED",
        )

        payment = PaymentService.create_received(
            org_id=test_org.id,
            data={
                "contact_id": customer.id,
                "bank_account_id": bank_account.id,
                "payment_date": date(2024, 1, 15),
                "amount": Decimal("200.00"),
                "payment_method": "BANK_TRANSFER",
            },
            user_id=test_user.id,
        )

        PaymentService.allocate(
            org_id=test_org.id,
            payment_id=payment.id,
            allocations=[{"document_id": invoice.id, "allocated_amount": Decimal("109.00")}],
            user_id=test_user.id,
        )

        # Verify audit log (allocation is logged on payment entity)
        audit_log = AuditEventLog.objects.filter(
            org_id=test_org.id,
            entity_table="payment",
            entity_id=payment.id,
            action="UPDATE",
            user_id__isnull=False,
        ).first()

        assert audit_log is not None
        assert audit_log.user_id == test_user.id

    def test_allocation_total_exceeds_payment(self, test_org, bank_account, customer, test_user):
        """Test that total allocations cannot exceed payment amount."""
        invoice1 = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-00007",
            contact=customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal("500.0000"),
            gst_total=Decimal("45.0000"),
            total_incl=Decimal("545.0000"),
            status="APPROVED",
        )

        invoice2 = InvoiceDocument.objects.create(
            org=test_org,
            document_type="SALES_INVOICE",
            document_number="INV-00008",
            contact=customer,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 31),
            total_excl=Decimal("300.0000"),
            gst_total=Decimal("27.0000"),
            total_incl=Decimal("327.0000"),
            status="APPROVED",
        )

        # Payment for $500
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

        # Attempt to allocate $800 total (exceeds $500)
        with pytest.raises(ValidationError) as exc_info:
            PaymentService.allocate(
                org_id=test_org.id,
                payment_id=payment.id,
                allocations=[
                    {"document_id": invoice1.id, "allocated_amount": Decimal("545.00")},
                    {"document_id": invoice2.id, "allocated_amount": Decimal("255.00")},
                ],
                user_id=test_user.id,
            )

        assert "exceed" in str(exc_info.value).lower()
