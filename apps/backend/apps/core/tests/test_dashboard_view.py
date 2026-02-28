"""
DashboardView API Tests (TDD)

Tests for the dashboard API endpoint.
Run with: pytest apps/core/tests/test_dashboard_view.py -v
"""

import pytest
import uuid
from datetime import date
from django.contrib.auth.hashers import make_password

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import (
    AppUser,
    Organisation,
    Role,
    UserOrganisation,
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
def dashboard_api_org(test_user):
    """Create organisation for dashboard API testing."""
    org_id = uuid.uuid4()
    org = Organisation.objects.create(
        id=org_id,
        name="Dashboard API Test Org",
        legal_name="Dashboard API Test Org Pte Ltd",
        uen="DASHAPI001",
        entity_type="PRIVATE_LIMITED",
        gst_registered=True,
        gst_reg_number="M12345678",
        gst_reg_date=date(2024, 1, 1),
        fy_start_month=1,
        base_currency="SGD",
        is_active=True,
    )
    
    # Create Owner role with view_reports permission
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
        can_view_reports=True,  # Required for dashboard access
        can_export_data=True,
        is_system=True,
    )
    
    # Assign user as Owner (with accepted_at set)
    from datetime import datetime
    UserOrganisation.objects.create(
        user=test_user,
        org=org,
        role=owner_role,
        is_default=True,
        accepted_at=datetime.now(),
    )
    
    return org


@pytest.fixture
def dashboard_auth_client(api_client, test_user):
    """Return an authenticated APIClient for dashboard tests."""
    from rest_framework_simplejwt.tokens import RefreshToken
    
    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client


@pytest.mark.django_db
class TestDashboardView:
    """Test suite for Dashboard API endpoint."""
    
    def test_dashboard_endpoint_exists(self, dashboard_auth_client, dashboard_api_org):
        """Test that dashboard endpoint returns 200 for authenticated user."""
        url = f"/api/v1/{dashboard_api_org.id}/dashboard/"
        response = dashboard_auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_dashboard_requires_authentication(self, api_client, dashboard_api_org):
        """Test that dashboard endpoint requires authentication."""
        url = f"/api/v1/{dashboard_api_org.id}/dashboard/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_dashboard_requires_org_membership(self, dashboard_auth_client):
        """Test that user must be member of organisation."""
        # Create org that test_user is NOT a member of
        fake_org_id = uuid.uuid4()
        Organisation.objects.create(
            id=fake_org_id,
            name="Other Org",
            legal_name="Other Org Pte Ltd",
            uen="OTHER001",
            entity_type="PRIVATE_LIMITED",
            base_currency="SGD",
            is_active=True,
        )
        
        url = f"/api/v1/{fake_org_id}/dashboard/"
        response = dashboard_auth_client.get(url)
        
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_dashboard_requires_view_reports_permission(self, test_user):
        """Test that user needs can_view_reports permission."""
        # Create org with role that lacks can_view_reports
        org_id = uuid.uuid4()
        org = Organisation.objects.create(
            id=org_id,
            name="No Reports Org",
            legal_name="No Reports Org Pte Ltd",
            uen="NOREPORTS1",
            entity_type="PRIVATE_LIMITED",
            base_currency="SGD",
            is_active=True,
        )
        
        limited_role = Role.objects.create(
            org=org,
            name="Limited User",
            description="Limited access",
            can_manage_org=False,
            can_manage_users=False,
            can_manage_coa=False,
            can_create_invoices=True,
            can_approve_invoices=False,
            can_void_invoices=False,
            can_create_journals=False,
            can_manage_banking=False,
            can_file_gst=False,
            can_view_reports=False,  # NO permission
            can_export_data=False,
            is_system=False,
        )
        
        UserOrganisation.objects.create(
            user=test_user,
            org=org,
            role=limited_role,
            is_default=True,
        )
        
        # Authenticate
        client = APIClient()
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(test_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        url = f"/api/v1/{org_id}/dashboard/"
        response = client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_dashboard_response_structure(self, dashboard_auth_client, dashboard_api_org):
        """Test that dashboard response has correct structure."""
        url = f"/api/v1/{dashboard_api_org.id}/dashboard/"
        response = dashboard_auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
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
    
    def test_dashboard_response_types(self, dashboard_auth_client, dashboard_api_org):
        """Test that dashboard response has correct data types."""
        url = f"/api/v1/{dashboard_api_org.id}/dashboard/"
        response = dashboard_auth_client.get(url)
        
        data = response.json()
        
        # String fields (formatted currency)
        assert isinstance(data['gst_payable'], str)
        assert isinstance(data['gst_payable_display'], str)
        assert isinstance(data['outstanding_receivables'], str)
        assert isinstance(data['cash_on_hand'], str)
        
        # Integer fields
        assert isinstance(data['invoices_pending'], int)
        assert isinstance(data['invoices_overdue'], int)
        assert isinstance(data['gst_threshold_utilization'], int)
        
        # Array fields
        assert isinstance(data['compliance_alerts'], list)
        
        # Object fields
        assert isinstance(data['current_gst_period'], dict)
    
    def test_dashboard_gst_threshold_status_values(self, dashboard_auth_client, dashboard_api_org):
        """Test that GST threshold status is valid enum value."""
        url = f"/api/v1/{dashboard_api_org.id}/dashboard/"
        response = dashboard_auth_client.get(url)
        
        data = response.json()
        
        valid_statuses = ['SAFE', 'WARNING', 'CRITICAL', 'EXCEEDED']
        assert data['gst_threshold_status'] in valid_statuses
    
    def test_dashboard_compliance_alerts_structure(self, dashboard_auth_client, dashboard_api_org):
        """Test compliance alerts have correct structure."""
        url = f"/api/v1/{dashboard_api_org.id}/dashboard/"
        response = dashboard_auth_client.get(url)
        
        data = response.json()
        alerts = data['compliance_alerts']
        
        for alert in alerts:
            assert 'id' in alert
            assert 'severity' in alert
            assert 'title' in alert
            assert 'message' in alert
            assert 'action_required' in alert
            assert alert['severity'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    def test_dashboard_only_get_allowed(self, dashboard_auth_client, dashboard_api_org):
        """Test that only GET method is allowed."""
        url = f"/api/v1/{dashboard_api_org.id}/dashboard/"
        
        # POST should not be allowed
        response = dashboard_auth_client.post(url, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # PUT should not be allowed
        response = dashboard_auth_client.put(url, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # DELETE should not be allowed
        response = dashboard_auth_client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_dashboard_includes_organisation_context(self, dashboard_auth_client, dashboard_api_org):
        """Test that dashboard data respects organisation context (RLS)."""
        url = f"/api/v1/{dashboard_api_org.id}/dashboard/"
        response = dashboard_auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Data should be specific to this organisation
        assert 'gst_payable' in data
        # The actual values depend on the org's data, but structure should be consistent
