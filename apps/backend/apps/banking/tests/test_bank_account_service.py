"""
Bank Account Service Tests (TDD)

Tests for BankAccountService CRUD operations.
Run with: pytest apps/banking/tests/test_bank_account_service.py -v

SEC-001 Remediation: Tests validate all security controls.
"""

import pytest
import uuid
from datetime import date
from decimal import Decimal
from django.contrib.auth.hashers import make_password

pytestmark = pytest.mark.django_db

from apps.core.models import (
    AppUser,
    Organisation,
    Role,
    UserOrganisation,
    Account,
    AccountType,
    AccountSubType,
    BankAccount,
    AuditEventLog,
)
from apps.banking.services import BankAccountService
from common.exceptions import ValidationError, ResourceNotFound, DuplicateResource


@pytest.fixture
def test_user():
    """Create and return a test user."""
    user_id = uuid.uuid4()
    user = AppUser.objects.create(
        id=user_id,
        email=f"bank_test_{user_id.hex[:8]}@example.com",
        full_name="Bank Test User",
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
        name="Bank Test Org",
        legal_name="Bank Test Org Pte Ltd",
        uen="BANKTEST1",
        entity_type="PRIVATE_LIMITED",
        gst_registered=True,
        gst_reg_number="M98765432",
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


class TestBankAccountServiceCreate:
    """Tests for BankAccountService.create()"""

    def test_create_bank_account_success(self, test_org, gl_account, test_user):
        """Test successful bank account creation."""
        data = {
            "account_name": "Main Operating Account",
            "bank_name": "DBS Bank",
            "account_number": "1234567890",
            "currency": "SGD",
            "gl_account": gl_account,
            "opening_balance": Decimal("1000.00"),
            "is_default": True,
        }

        bank_account = BankAccountService.create(
            org_id=test_org.id,
            data=data,
            user_id=test_user.id,
        )

        assert bank_account.id is not None
        assert bank_account.account_name == "Main Operating Account"
        assert bank_account.bank_name == "DBS Bank"
        assert bank_account.account_number == "1234567890"
        assert bank_account.currency == "SGD"
        assert bank_account.is_default is True
        assert bank_account.is_active is True
        assert bank_account.opening_balance == Decimal("1000.0000")

    def test_create_bank_account_duplicate_number_fails(self, test_org, gl_account, test_user):
        """Test that duplicate account_number fails."""
        data1 = {
            "account_name": "Account 1",
            "bank_name": "DBS Bank",
            "account_number": "1234567890",
            "gl_account": gl_account,
        }
        BankAccountService.create(org_id=test_org.id, data=data1, user_id=test_user.id)

        data2 = {
            "account_name": "Account 2",
            "bank_name": "UOB Bank",
            "account_number": "1234567890",
            "gl_account": gl_account,
        }

        with pytest.raises(DuplicateResource) as exc_info:
            BankAccountService.create(org_id=test_org.id, data=data2, user_id=test_user.id)

        assert "already exists" in str(exc_info.value)

    def test_create_bank_account_sets_single_default(self, test_org, gl_account, test_user):
        """Test that creating a new default clears previous default."""
        data1 = {
            "account_name": "First Account",
            "bank_name": "DBS Bank",
            "account_number": "1111111111",
            "gl_account": gl_account,
            "is_default": True,
        }
        account1 = BankAccountService.create(org_id=test_org.id, data=data1, user_id=test_user.id)

        data2 = {
            "account_name": "Second Account",
            "bank_name": "UOB Bank",
            "account_number": "2222222222",
            "gl_account": gl_account,
            "is_default": True,
        }
        account2 = BankAccountService.create(org_id=test_org.id, data=data2, user_id=test_user.id)

        account1.refresh_from_db()
        assert account1.is_default is False
        assert account2.is_default is True

    def test_create_bank_account_audit_logged(self, test_org, gl_account, test_user):
        """Test that bank account creation is audit logged."""
        data = {
            "account_name": "Audited Account",
            "bank_name": "DBS Bank",
            "account_number": "9999999999",
            "gl_account": gl_account,
        }

        bank_account = BankAccountService.create(
            org_id=test_org.id,
            data=data,
            user_id=test_user.id,
        )

        audit_log = AuditEventLog.objects.filter(
            org_id=test_org.id,
            entity_table="bank_account",
            entity_id=bank_account.id,
            action="CREATE",
        ).first()

        assert audit_log is not None
        assert audit_log.user == test_user
        assert audit_log.new_data["account_name"] == "Audited Account"


class TestBankAccountServiceList:
    """Tests for BankAccountService.list()"""

    def test_list_bank_accounts_success(self, test_org, gl_account, test_user):
        """Test listing bank accounts."""
        BankAccount.objects.create(
            org=test_org,
            account_name="Account 1",
            bank_name="DBS Bank",
            account_number="1111111111",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )
        BankAccount.objects.create(
            org=test_org,
            account_name="Account 2",
            bank_name="UOB Bank",
            account_number="2222222222",
            gl_account=gl_account,
            is_active=False,
            paynow_type=None,
            paynow_id=None,
        )

        accounts = BankAccountService.list(org_id=test_org.id)

        assert len(accounts) == 2

    def test_list_bank_accounts_filter_active(self, test_org, gl_account, test_user):
        """Test filtering by active status."""
        BankAccount.objects.create(
            org=test_org,
            account_name="Active Account",
            bank_name="DBS Bank",
            account_number="1111111111",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )
        BankAccount.objects.create(
            org=test_org,
            account_name="Inactive Account",
            bank_name="UOB Bank",
            account_number="2222222222",
            gl_account=gl_account,
            is_active=False,
            paynow_type=None,
            paynow_id=None,
        )

        active_accounts = BankAccountService.list(org_id=test_org.id, is_active=True)

        assert len(active_accounts) == 1
        assert active_accounts[0].account_name == "Active Account"

    def test_list_bank_accounts_search(self, test_org, gl_account, test_user):
        """Test searching bank accounts."""
        BankAccount.objects.create(
            org=test_org,
            account_name="Operating Account",
            bank_name="DBS Bank",
            account_number="1111111111",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )
        BankAccount.objects.create(
            org=test_org,
            account_name="Payroll Account",
            bank_name="UOB Bank",
            account_number="2222222222",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )

        results = BankAccountService.list(org_id=test_org.id, search="Operating")

        assert len(results) == 1
        assert results[0].account_name == "Operating Account"


class TestBankAccountServiceGet:
    """Tests for BankAccountService.get()"""

    def test_get_bank_account_success(self, test_org, gl_account, test_user):
        """Test getting a single bank account."""
        created = BankAccount.objects.create(
            org=test_org,
            account_name="Test Account",
            bank_name="DBS Bank",
            account_number="1234567890",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )

        retrieved = BankAccountService.get(org_id=test_org.id, account_id=created.id)

        assert retrieved.id == created.id
        assert retrieved.account_name == "Test Account"

    def test_get_bank_account_not_found(self, test_org):
        """Test getting non-existent bank account."""
        with pytest.raises(ResourceNotFound):
            BankAccountService.get(org_id=test_org.id, account_id=uuid.uuid4())


class TestBankAccountServiceUpdate:
    """Tests for BankAccountService.update()"""

    def test_update_bank_account_success(self, test_org, gl_account, test_user):
        """Test updating bank account."""
        bank_account = BankAccount.objects.create(
            org=test_org,
            account_name="Original Name",
            bank_name="DBS Bank",
            account_number="1234567890",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )

        updated = BankAccountService.update(
            org_id=test_org.id,
            account_id=bank_account.id,
            data={"account_name": "Updated Name"},
            user_id=test_user.id,
        )

        assert updated.account_name == "Updated Name"

    def test_update_bank_account_audit_logged(self, test_org, gl_account, test_user):
        """Test that update is audit logged."""
        bank_account = BankAccount.objects.create(
            org=test_org,
            account_name="Original",
            bank_name="DBS Bank",
            account_number="1234567890",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )

        BankAccountService.update(
            org_id=test_org.id,
            account_id=bank_account.id,
            data={"account_name": "Updated"},
            user_id=test_user.id,
        )

        audit_log = AuditEventLog.objects.filter(
            org_id=test_org.id,
            entity_table="bank_account",
            entity_id=bank_account.id,
            action="UPDATE",
        ).first()

        assert audit_log is not None
        assert audit_log.old_data["account_name"] == "Original"
        assert audit_log.new_data["account_name"] == "Updated"


class TestBankAccountServiceDeactivate:
    """Tests for BankAccountService.deactivate()"""

    def test_deactivate_bank_account_success(self, test_org, gl_account, test_user):
        """Test deactivating bank account."""
        BankAccount.objects.create(
            org=test_org,
            account_name="Account 1",
            bank_name="DBS Bank",
            account_number="1111111111",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )

        account2 = BankAccount.objects.create(
            org=test_org,
            account_name="Account 2",
            bank_name="UOB Bank",
            account_number="2222222222",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )

        deactivated = BankAccountService.deactivate(
            org_id=test_org.id,
            account_id=account2.id,
            user_id=test_user.id,
        )

        assert deactivated.is_active is False

    def test_deactivate_only_account_fails(self, test_org, gl_account, test_user):
        """Test that deactivating the only account fails."""
        bank_account = BankAccount.objects.create(
            org=test_org,
            account_name="Only Account",
            bank_name="DBS Bank",
            account_number="1234567890",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )

        with pytest.raises(ValidationError) as exc_info:
            BankAccountService.deactivate(
                org_id=test_org.id,
                account_id=bank_account.id,
                user_id=test_user.id,
            )

        assert "only active bank account" in str(exc_info.value)


class TestBankAccountRLS:
    """Tests for Row-Level Security enforcement."""

    def test_cross_org_access_blocked(self, test_org, gl_account, test_user):
        """Test that cross-org access is blocked."""
        other_org_id = uuid.uuid4()

        bank_account = BankAccount.objects.create(
            org=test_org,
            account_name="Test Account",
            bank_name="DBS Bank",
            account_number="1234567890",
            gl_account=gl_account,
            is_active=True,
            paynow_type=None,
            paynow_id=None,
        )

        with pytest.raises(ResourceNotFound):
            BankAccountService.get(org_id=other_org_id, account_id=bank_account.id)
