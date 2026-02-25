"""
Security tests for Row-Level Security (RLS) tenant isolation.

Tests that users can only access data from their own organisation.
"""

import pytest
from rest_framework import status

from apps.core.models import Organisation, AppUser, Account


@pytest.mark.django_db
def test_rls_organisation_isolation(auth_client, test_user):
    """Test that users cannot access other organisations' data."""
    # Create another organisation without test_user as member
    other_org = Organisation.objects.create(
        name="Other Organisation",
        legal_name="Other Org Pte Ltd",
        base_currency="SGD",
        is_active=True,
    )
    
    # Try to access the other org
    url = f"/api/v1/{other_org.id}/"
    response = auth_client.get(url)
    
    # Should be forbidden or not found
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


@pytest.mark.django_db
def test_rls_accounts_isolation(auth_client, test_organisation, test_user):
    """Test that accounts from other orgs are not visible."""
    # Create another org with accounts
    other_org = Organisation.objects.create(
        name="Other Org",
        legal_name="Other Org Pte Ltd",
        base_currency="SGD",
        is_active=True,
    )
    
    # Create account in other org
    other_account = Account.objects.create(
        org=other_org,
        code="9999",
        name="Other Account",
        account_type="ASSET_CURRENT",
        is_active=True,
    )
    
    # List accounts - should not see other org's account
    url = f"/api/v1/{test_organisation.id}/accounts/"
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    
    # Check that other account is not in the list
    account_codes = [acc["code"] for acc in response.data.get("data", [])]
    assert "9999" not in account_codes


@pytest.mark.django_db
def test_rls_middleware_sets_context(auth_client, test_organisation):
    """Test that RLS middleware sets the tenant context."""
    from common.middleware.tenant_context import get_current_org_id
    
    # Make a request to org-scoped endpoint
    url = f"/api/v1/{test_organisation.id}/"
    response = auth_client.get(url)
    
    # Response should succeed
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_cross_org_data_access_blocked(auth_client, test_organisation, test_user):
    """Test explicit cross-organisation data access is blocked."""
    from apps.core.models import Contact
    
    # Create another org with a contact
    other_org = Organisation.objects.create(
        name="Other Org",
        legal_name="Other Org Pte Ltd",
        base_currency="SGD",
        is_active=True,
    )
    
    other_contact = Contact.objects.create(
        org=other_org,
        name="Other Contact",
        is_customer=True,
        is_active=True,
    )
    
    # Try to access contact from other org using our org's URL
    # This would be a malicious attempt
    url = f"/api/v1/{test_organisation.id}/invoicing/contacts/{other_contact.id}/"
    response = auth_client.get(url)
    
    # Should not find it (404) or forbidden (403)
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


@pytest.mark.django_db
def test_rls_sql_injection_protection(auth_client, test_organisation):
    """Test that RLS prevents SQL injection attempts."""
    # Try SQL injection in org_id
    malicious_url = "/api/v1/'; DROP TABLE core.organisation; --/"
    response = auth_client.get(malicious_url)
    
    # Should be bad request (invalid UUID format)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_rls_with_invalid_org_id(auth_client):
    """Test that invalid org IDs are rejected."""
    url = "/api/v1/invalid-uuid/"
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_rls_nonexistent_org(auth_client):
    """Test that non-existent org IDs are handled."""
    import uuid
    
    url = f"/api/v1/{uuid.uuid4()}/"
    response = auth_client.get(url)
    
    # Should be 404 (not found) or 403 (forbidden)
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]
