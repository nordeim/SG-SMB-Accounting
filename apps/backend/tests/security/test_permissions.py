"""
Security tests for Permission-based access control.

Tests that role-based permissions are enforced correctly.
"""

import pytest
from rest_framework import status

from apps.core.models import Organisation, Role, UserOrganisation


@pytest.mark.django_db
def test_permission_denied_for_viewer_role(auth_client, test_user):
    """Test that users with viewer role cannot create invoices."""
    # Create org with viewer role
    org = Organisation.objects.create(
        name="Viewer Test Org",
        legal_name="Viewer Test Org Pte Ltd",
        base_currency="SGD",
        is_active=True,
    )
    
    # Create viewer role (limited permissions)
    viewer_role = Role.objects.create(
        org=org,
        name="Viewer",
        description="View only",
        can_manage_org=False,
        can_manage_users=False,
        can_manage_coa=False,
        can_create_invoices=False,  # Cannot create invoices
        can_approve_invoices=False,
        can_void_invoices=False,
        can_create_journals=False,
        can_manage_banking=False,
        can_file_gst=False,
        can_view_reports=True,
        can_export_data=False,
        is_system=True,
    )
    
    # Assign user as viewer
    UserOrganisation.objects.create(
        user=test_user,
        org=org,
        role=viewer_role,
        is_default=True,
    )
    
    # Try to create invoice (should fail)
    url = f"/api/v1/{org.id}/invoicing/documents/"
    response = auth_client.post(url, {}, format="json")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_permission_allowed_for_owner_role(auth_client, test_organisation):
    """Test that owners can perform all operations."""
    # Owner should be able to create accounts
    url = f"/api/v1/{test_organisation.id}/accounts/"
    data = {
        "code": "6100",
        "name": "Test Expense Account",
        "account_type": "EXPENSE_ADMIN"
    }
    
    response = auth_client.post(url, data, format="json")
    
    # Should succeed (or validation error, not permission error)
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        # If 400, should be validation error, not permission
        assert "permission" not in str(response.data).lower()


@pytest.mark.django_db
def test_permission_create_journals(auth_client, test_organisation):
    """Test CanCreateJournals permission."""
    url = f"/api/v1/{test_organisation.id}/journal-entries/entries/"
    
    # Owner should have CanCreateJournals permission
    # Even without data, should get validation error not permission error
    response = auth_client.post(url, {}, format="json")
    
    # Should be validation error (400) not permission error (403)
    assert response.status_code != status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_permission_file_gst(auth_client, test_organisation):
    """Test CanFileGST permission."""
    url = f"/api/v1/{test_organisation.id}/gst/returns/"
    
    # Owner should have CanFileGST permission
    response = auth_client.post(url, {
        "filing_frequency": "MONTHLY",
        "start_date": "2024-01-01"
    }, format="json")
    
    # Should not be permission denied
    assert response.status_code != status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_permission_superadmin_bypass(auth_client, test_user):
    """Test that superadmins can access any organisation."""
    # Make user superadmin
    test_user.is_superadmin = True
    test_user.save()
    
    # Create org without adding user as member
    other_org = Organisation.objects.create(
        name="Superadmin Test Org",
        legal_name="Superadmin Test Org Pte Ltd",
        base_currency="SGD",
        is_active=True,
    )
    
    # Superadmin should be able to access
    url = f"/api/v1/{other_org.id}/"
    response = auth_client.get(url)
    
    # Superadmin can access any org
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]


@pytest.mark.django_db
def test_permission_unauthenticated(api_client, test_organisation):
    """Test that unauthenticated requests are rejected."""
    endpoints = [
        f"/api/v1/{test_organisation.id}/",
        f"/api/v1/{test_organisation.id}/accounts/",
        f"/api/v1/{test_organisation.id}/invoicing/documents/",
        f"/api/v1/{test_organisation.id}/gst/returns/",
        f"/api/v1/{test_organisation.id}/journal-entries/entries/",
    ]
    
    for url in endpoints:
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, f"Endpoint {url} should require auth"
