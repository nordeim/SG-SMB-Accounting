"""
pytest configuration for LedgerSG backend.

Fixtures and utilities for integration testing.
"""

import pytest
import uuid
from decimal import Decimal
from datetime import date, timedelta
from typing import Generator

from django.test import Client
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient

# Import models
from apps.core.models import (
    AppUser,
    Organisation,
    Role,
    UserOrganisation,
    FiscalYear,
    FiscalPeriod,
    TaxCode,
    Account,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def api_client() -> APIClient:
    """Return a fresh APIClient."""
    return APIClient()


@pytest.fixture
def test_user() -> AppUser:
    """Create and return a test user."""
    user_id = uuid.uuid4()
    user = AppUser.objects.create(
        id=user_id,
        email=f"test_{user_id.hex[:8]}@example.com",
        full_name="Test User",
        is_active=True,
    )
    user.password = make_password("testpassword123")
    user.save()
    return user


@pytest.fixture
def test_organisation(test_user) -> Organisation:
    """Create and return a test organisation with the user as Owner."""
    org_id = uuid.uuid4()
    org = Organisation.objects.create(
        id=org_id,
        name="Test Organisation",
        legal_name="Test Organisation Pte Ltd",
        uen="123456789A",
        gst_registered=True,
        gst_reg_number="M12345678",
        gst_reg_date=date(2024, 1, 1),
        fy_start_month=1,
        base_currency="SGD",
        is_active=True,
    )
    
    # Create Owner role
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
    
    # Assign user as Owner
    UserOrganisation.objects.create(
        user=test_user,
        org=org,
        role=owner_role,
        is_default=True,
    )
    
    return org


@pytest.fixture
def auth_client(api_client, test_user) -> APIClient:
    """Return an authenticated APIClient."""
    from rest_framework_simplejwt.tokens import RefreshToken
    
    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client


@pytest.fixture
def test_tax_codes(test_organisation) -> dict:
    """Create standard tax codes for the organisation."""
    codes = {}
    
    tax_code_data = [
        ("SR", "Standard-Rated", Decimal("0.09"), True, "box1"),
        ("ZR", "Zero-Rated", Decimal("0.00"), True, "box2"),
        ("ES", "Exempt", None, False, "box3"),
        ("OS", "Out-of-Scope", None, False, None),
    ]
    
    for code, name, rate, is_gst_charged, box_mapping in tax_code_data:
        tc = TaxCode.objects.create(
            org=test_organisation,
            code=code,
            name=name,
            rate=rate,
            is_gst_charged=is_gst_charged,
            box_mapping=box_mapping,
            is_system=True,
            is_active=True,
            effective_from=date(2024, 1, 1),
        )
        codes[code] = tc
    
    return codes


@pytest.fixture
def test_accounts(test_organisation) -> dict:
    """Create standard accounts for the organisation."""
    accounts = {}
    
    account_data = [
        ("1200", "Accounts Receivable", "ASSET_CURRENT"),
        ("2200", "GST Output Tax", "LIABILITY_CURRENT"),
        ("4000", "Sales Revenue", "REVENUE"),
        ("5000", "Cost of Sales", "COS"),
        ("6100", "Rent Expense", "EXPENSE_ADMIN"),
    ]
    
    for code, name, account_type in account_data:
        acc = Account.objects.create(
            org=test_organisation,
            code=code,
            name=name,
            account_type=account_type,
            is_system=True,
            is_active=True,
        )
        accounts[code] = acc
    
    return accounts


@pytest.fixture
def test_fiscal_period(test_organisation) -> FiscalPeriod:
    """Create a fiscal year with periods for the organisation."""
    fy = FiscalYear.objects.create(
        org=test_organisation,
        label="FY2024",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        is_closed=False,
    )
    
    # Create January period
    period = FiscalPeriod.objects.create(
        org=test_organisation,
        fiscal_year=fy,
        label="January 2024",
        period_number=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        is_open=True,
    )
    
    return period


# =============================================================================
# Helper Functions
# =============================================================================

def get_auth_token(user: AppUser) -> str:
    """Generate JWT access token for a user."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def create_test_contact(org: Organisation, **kwargs) -> "Contact":
    """Create a test contact for an organisation."""
    from apps.core.models import Contact
    
    defaults = {
        "name": "Test Contact",
        "company_name": "Test Company",
        "email": "contact@example.com",
        "is_customer": True,
        "is_supplier": False,
        "payment_terms_days": 30,
        "is_active": True,
    }
    defaults.update(kwargs)
    
    return Contact.objects.create(org=org, **defaults)


def create_test_invoice(org: Organisation, contact: "Contact", **kwargs) -> "InvoiceDocument":
    """Create a test invoice for testing."""
    from apps.core.models import InvoiceDocument
    from apps.invoicing.services import DocumentService
    
    defaults = {
        "document_type": "INVOICE",
        "contact": contact,
        "issue_date": date.today(),
        "due_date": date.today() + timedelta(days=30),
        "status": "DRAFT",
    }
    defaults.update(kwargs)
    
    # Use service to create with proper numbering
    from unittest.mock import patch
    with patch.object(DocumentService, '_get_next_document_number', return_value="INV-00001"):
        invoice = InvoiceDocument.objects.create(org=org, **defaults)
    
    return invoice


# =============================================================================
# pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest environment."""
    import django
    django.setup()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Set up test database."""
    with django_db_blocker.unblock():
        # Any global database setup
        pass


# Markers
pytest.mark.integration = pytest.mark.django_db(transaction=True)
pytest.mark.unit = pytest.mark.django_db(transaction=False)
pytest.mark.security = pytest.mark.django_db(transaction=True)
pytest.mark.workflow = pytest.mark.django_db(transaction=True)
