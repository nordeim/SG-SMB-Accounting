"""
DashboardService Tests (TDD)

Tests for the dashboard data aggregation service.
Run with: pytest apps/core/tests/test_dashboard_service.py -v
"""

import pytest
import uuid
from datetime import date, timedelta
from decimal import Decimal
from rest_framework.test import APIClient
from django.contrib.auth.hashers import make_password

from apps.core.services.dashboard_service import DashboardService
from apps.core.models import (
    AppUser,
    Organisation,
    Role,
    UserOrganisation,
    FiscalYear,
    FiscalPeriod,
    Account,
    TaxCode,
    InvoiceDocument,
    Contact,
)


# Fixtures required for tests
@pytest.fixture
def api_client():
    """Return a fresh APIClient."""
    return APIClient()


@pytest.fixture
def test_user():
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
def dashboard_test_org(test_user):
    """Create organisation with full data for dashboard testing."""
    org_id = uuid.uuid4()
    org = Organisation.objects.create(
        id=org_id,
        name="Dashboard Test Org",
        legal_name="Dashboard Test Org Pte Ltd",
        uen="DASHBOARD1",
        entity_type="PRIVATE_LIMITED",
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
def dashboard_fiscal_data(dashboard_test_org):
    """Create fiscal year and periods for dashboard tests."""
    fy = FiscalYear.objects.create(
        org=dashboard_test_org,
        label="FY2024",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        is_closed=False,
    )
    
    # Create current period (March 2024)
    current_period = FiscalPeriod.objects.create(
        org=dashboard_test_org,
        fiscal_year=fy,
        label="March 2024",
        period_number=3,
        start_date=date(2024, 3, 1),
        end_date=date(2024, 3, 31),
        is_open=True,
    )
    
    return {"fiscal_year": fy, "current_period": current_period}


@pytest.fixture
def dashboard_invoices(dashboard_test_org):
    """Create invoices for dashboard tests."""
    # Create a customer contact
    contact = Contact.objects.create(
        org=dashboard_test_org,
        contact_type="CUSTOMER",
        name="Test Customer",
        company_name="Test Customer Pte Ltd",
        email="customer@example.com",
        is_customer=True,
        is_active=True,
    )
    
    invoices = []
    
    # Create pending invoices (SENT, not yet due)
    for i in range(5):
        amount = Decimal(f"{5000 + i * 1000}.0000")
        gst = amount * Decimal("0.09")
        inv = InvoiceDocument.objects.create(
            org=dashboard_test_org,
            document_type="SALES_INVOICE",
            contact=contact,
            document_number=f"INV-{1000 + i}",
            issue_date=date.today() - timedelta(days=i),
            due_date=date.today() + timedelta(days=30 - i),  # Not yet due
            status="SENT",
            total_excl=amount,
            gst_total=gst,
            total_incl=amount + gst,
        )
        invoices.append(inv)
    
    # Create overdue invoices (SENT with past due date)
    for i in range(3):
        amount = Decimal(f"{3000 + i * 500}.0000")
        gst = amount * Decimal("0.09")
        inv = InvoiceDocument.objects.create(
            org=dashboard_test_org,
            document_type="SALES_INVOICE",
            contact=contact,
            document_number=f"INV-{2000 + i}",
            issue_date=date.today() - timedelta(days=45 + i),
            due_date=date.today() - timedelta(days=15 + i),  # Past due
            status="OVERDUE",  # Mark as OVERDUE
            total_excl=amount,
            gst_total=gst,
            total_incl=amount + gst,
        )
        invoices.append(inv)
    
    # Create paid invoices
    for i in range(10):
        amount = Decimal(f"{2000 + i * 200}.0000")
        gst = amount * Decimal("0.09")
        inv = InvoiceDocument.objects.create(
            org=dashboard_test_org,
            document_type="SALES_INVOICE",
            contact=contact,
            document_number=f"INV-{3000 + i}",
            issue_date=date.today() - timedelta(days=60 + i),
            due_date=date.today() - timedelta(days=30 + i),
            status="PAID",
            total_excl=amount,
            gst_total=gst,
            total_incl=amount + gst,
            amount_paid=amount + gst,
        )
        invoices.append(inv)
    
    return invoices


@pytest.mark.django_db
class TestDashboardService:
    """Test suite for DashboardService."""
    
    def test_service_exists(self):
        """Test that DashboardService exists and has required methods."""
        assert hasattr(DashboardService, 'get_dashboard_data')
        assert callable(getattr(DashboardService, 'get_dashboard_data'))
    
    def test_get_dashboard_data_structure(self, dashboard_test_org, dashboard_fiscal_data):
        """Test that get_dashboard_data returns correct structure."""
        data = DashboardService.get_dashboard_data(dashboard_test_org.id)
        
        # Check required keys
        required_keys = [
            'gst_payable',
            'gst_payable_display',
            'outstanding_receivables',
            'outstanding_payables',
            'revenue_mtd',
            'revenue_ytd',
            'cash_on_hand',
            'gst_threshold_status',
            'gst_threshold_utilization',
            'gst_threshold_amount',
            'gst_threshold_limit',
            'compliance_alerts',
            'invoices_pending',
            'invoices_overdue',
            'invoices_peppol_pending',
            'current_gst_period',
            'last_updated',
        ]
        
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"
    
    def test_gst_threshold_calculation(self, dashboard_test_org):
        """Test GST threshold monitoring calculations."""
        data = DashboardService.get_dashboard_data(dashboard_test_org.id)
        
        # Threshold limit should be 1,000,000.00
        assert data['gst_threshold_limit'] == "1,000,000.00"
        
        # Utilization should be 0-100
        assert 0 <= data['gst_threshold_utilization'] <= 100
        
        # Status should be one of allowed values
        assert data['gst_threshold_status'] in ['SAFE', 'WARNING', 'CRITICAL', 'EXCEEDED']
    
    def test_cash_on_hand_calculation(self, dashboard_test_org, dashboard_invoices):
        """Test cash on hand is calculated from paid invoices."""
        data = DashboardService.get_dashboard_data(dashboard_test_org.id)
        
        # Should have cash_on_hand value (formatted string)
        assert 'cash_on_hand' in data
        assert isinstance(data['cash_on_hand'], str)
        # Value should be parseable
        cash = Decimal(data['cash_on_hand'].replace(',', ''))
        assert cash >= 0  # Cash shouldn't be negative in this test scenario
    
    def test_gst_payable_calculation(self, dashboard_test_org, dashboard_invoices):
        """Test GST payable calculation from invoices."""
        data = DashboardService.get_dashboard_data(dashboard_test_org.id)
        
        # Should have GST values
        assert 'gst_payable' in data
        assert 'gst_payable_display' in data
        # Display should be formatted
        assert ',' in data['gst_payable_display'] or float(data['gst_payable']) == 0
    
    def test_outstanding_receivables(self, dashboard_test_org, dashboard_invoices):
        """Test outstanding receivables calculation."""
        data = DashboardService.get_dashboard_data(dashboard_test_org.id)
        
        # Should calculate from SENT/OVERDUE invoices (not paid)
        assert 'outstanding_receivables' in data
        receivables = Decimal(data['outstanding_receivables'].replace(',', ''))
        # Should be positive with our test data
        assert receivables > 0
    
    def test_invoice_counts(self, dashboard_test_org, dashboard_invoices):
        """Test invoice pending and overdue counts."""
        data = DashboardService.get_dashboard_data(dashboard_test_org.id)
        
        # Should count SENT invoices not yet due as pending
        assert data['invoices_pending'] == 5
        
        # Should count OVERDUE invoices
        assert data['invoices_overdue'] == 3
    
    def test_revenue_calculations(self, dashboard_test_org, dashboard_invoices):
        """Test MTD and YTD revenue calculations."""
        data = DashboardService.get_dashboard_data(dashboard_test_org.id)
        
        # Should have revenue values
        assert 'revenue_mtd' in data
        assert 'revenue_ytd' in data
        
        # Should be formatted strings
        assert isinstance(data['revenue_mtd'], str)
        assert isinstance(data['revenue_ytd'], str)
        
        # Should be positive with our paid invoices
        mtd = Decimal(data['revenue_mtd'].replace(',', ''))
        assert mtd >= 0
    
    def test_compliance_alerts_structure(self, dashboard_test_org):
        """Test compliance alerts structure."""
        data = DashboardService.get_dashboard_data(dashboard_test_org.id)
        
        assert 'compliance_alerts' in data
        assert isinstance(data['compliance_alerts'], list)
        
        # Each alert should have required fields
        for alert in data['compliance_alerts']:
            assert 'id' in alert
            assert 'severity' in alert
            assert 'title' in alert
            assert 'message' in alert
            assert 'action_required' in alert
            assert alert['severity'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    def test_gst_period_info(self, dashboard_test_org, dashboard_fiscal_data):
        """Test GST period information."""
        data = DashboardService.get_dashboard_data(dashboard_test_org.id)
        
        period = data['current_gst_period']
        assert 'start_date' in period
        assert 'end_date' in period
        assert 'filing_due_date' in period
        assert 'days_remaining' in period
        
        # Days remaining should be integer
        assert isinstance(period['days_remaining'], int)
    
    def test_last_updated_timestamp(self, dashboard_test_org):
        """Test that last_updated is ISO timestamp."""
        data = DashboardService.get_dashboard_data(dashboard_test_org.id)
        
        assert 'last_updated' in data
        # Should be valid ISO format
        assert 'T' in data['last_updated']  # ISO 8601 format indicator
    
    def test_nonexistent_organisation(self):
        """Test handling of non-existent organisation."""
        fake_org_id = uuid.uuid4()
        
        with pytest.raises(Exception):
            DashboardService.get_dashboard_data(fake_org_id)
