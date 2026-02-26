"""
Integration tests for Organisation API endpoints.

Tests organisation CRUD, GST registration, fiscal years, and summary.
"""

import pytest
from datetime import date
from rest_framework import status

from apps.core.models import Organisation, FiscalYear, FiscalPeriod, Account, Role


@pytest.mark.django_db
def test_list_organisations_success(auth_client, test_user, test_organisation):
    """Test listing user's organisations."""
    url = "/api/v1/organisations/"
    
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.data
    assert len(response.data["data"]) >= 1
    assert response.data["count"] >= 1
    
    # Check the test org is in the list
    org_ids = [org["id"] for org in response.data["data"]]
    assert str(test_organisation.id) in org_ids


@pytest.mark.django_db
def test_list_organisations_unauthenticated(api_client):
    """Test listing organisations without auth fails."""
    url = "/api/v1/organisations/"
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_create_organisation_success(auth_client, test_user):
    """Test creating a new organisation."""
    url = "/api/v1/organisations/"
    data = {
        "name": "New Test Organisation",
        "legal_name": "New Test Organisation Pte Ltd",
        "uen": "987654321B",
        "gst_registered": False,
        "fy_start_month": 4,
        "base_currency": "SGD"
    }
    
    response = auth_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "New Test Organisation"
    assert response.data["legal_name"] == "New Test Organisation Pte Ltd"
    
    # Verify org was created
    org_id = response.data["id"]
    org = Organisation.objects.get(id=org_id)
    assert org.name == "New Test Organisation"
    assert org.base_currency == "SGD"
    
    # Verify user is Owner
    membership = org.user_memberships.filter(user=test_user).first()
    assert membership is not None
    assert membership.role.name == "Owner"


@pytest.mark.django_db
def test_get_organisation_detail_success(auth_client, test_organisation):
    """Test getting organisation details."""
    url = f"/api/v1/{test_organisation.id}/"
    
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(test_organisation.id)
    assert response.data["name"] == test_organisation.name
    assert response.data["legal_name"] == test_organisation.legal_name


@pytest.mark.django_db
def test_get_organisation_detail_not_member(auth_client):
    """Test getting org details when not a member fails."""
    # Create org without adding user
    import uuid
    from apps.core.models import Organisation
    other_org = Organisation.objects.create(
        name="Other Org",
        legal_name="Other Org Pte Ltd",
        base_currency="SGD",
        uen=f"UEN{uuid.uuid4().hex[:8]}".upper()
    )
    
    url = f"/api/v1/{other_org.id}/"
    response = auth_client.get(url)
    
    # Should be forbidden or not found
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


@pytest.mark.django_db
def test_update_organisation_success(auth_client, test_organisation):
    """Test updating organisation settings."""
    url = f"/api/v1/{test_organisation.id}/"
    data = {
        "name": "Updated Organisation Name",
        "contact_email": "new@example.com"
    }
    
    response = auth_client.patch(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Updated Organisation Name"
    assert response.data["contact_email"] == "new@example.com"
    
    # Verify in database
    test_organisation.refresh_from_db()
    assert test_organisation.name == "Updated Organisation Name"


@pytest.mark.django_db
def test_deactivate_organisation_success(auth_client, test_organisation):
    """Test deactivating an organisation."""
    url = f"/api/v1/{test_organisation.id}/"
    
    response = auth_client.delete(url)
    
    # Should be 204 No Content or 200 OK
    assert response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK]
    
    # Verify deactivated
    test_organisation.refresh_from_db()
    assert test_organisation.is_active is False


@pytest.mark.django_db
def test_gst_registration_success(auth_client, test_organisation):
    """Test registering organisation for GST."""
    # First, create org without GST
    test_organisation.gst_registered = False
    test_organisation.gst_reg_number = ""
    test_organisation.save()
    
    url = f"/api/v1/{test_organisation.id}/gst/"
    data = {
        "gst_reg_number": "M87654321",
        "gst_reg_date": "2024-06-01"
    }
    
    response = auth_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["gst_registered"] is True
    assert response.data["gst_reg_number"] == "M87654321"
    
    # Verify in database
    test_organisation.refresh_from_db()
    assert test_organisation.gst_registered is True


@pytest.mark.django_db
def test_gst_deregistration_success(auth_client, test_organisation):
    """Test deregistering from GST."""
    url = f"/api/v1/{test_organisation.id}/gst/"
    
    response = auth_client.delete(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["gst_registered"] is False
    assert response.data["gst_reg_number"] == ""


@pytest.mark.django_db
def test_list_fiscal_years_success(auth_client, test_organisation, test_fiscal_period):
    """Test listing fiscal years for organisation."""
    url = f"/api/v1/{test_organisation.id}/fiscal-years/"
    
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.data
    assert len(response.data["data"]) >= 1


@pytest.mark.django_db
def test_get_organisation_summary_success(auth_client, test_organisation, test_fiscal_period):
    """Test getting organisation summary."""
    url = f"/api/v1/{test_organisation.id}/summary/"
    
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "organisation" in response.data
    assert "current_fiscal_year" in response.data
    assert "member_count" in response.data
    assert response.data["organisation"]["id"] == str(test_organisation.id)


@pytest.mark.django_db
def test_organisation_creation_seeds_coa(auth_client, test_user):
    """Test that organisation creation seeds Chart of Accounts."""
    url = "/api/v1/organisations/"
    data = {
        "name": "Org With CoA",
        "legal_name": "Org With CoA Pte Ltd",
        "gst_registered": True,
        "gst_reg_number": "M11111111",
        "gst_reg_date": "2024-01-01",
        "base_currency": "SGD"
    }
    
    response = auth_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    org_id = response.data["id"]
    
    # Verify accounts were created
    accounts = Account.objects.filter(org_id=org_id)
    assert accounts.count() > 0
    
    # Should have system accounts
    system_accounts = accounts.filter(is_system=True)
    assert system_accounts.count() > 0


@pytest.mark.django_db
def test_organisation_creation_creates_fiscal_year(auth_client, test_user):
    """Test that organisation creation creates fiscal year."""
    url = "/api/v1/organisations/"
    data = {
        "name": "Org With Fiscal",
        "legal_name": "Org With Fiscal Pte Ltd",
        "fy_start_month": 1,
        "base_currency": "SGD"
    }
    
    response = auth_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    org_id = response.data["id"]
    
    # Verify fiscal year was created
    fiscal_years = FiscalYear.objects.filter(org_id=org_id)
    assert fiscal_years.count() >= 1
    
    # Verify periods were created
    fy = fiscal_years.first()
    periods = FiscalPeriod.objects.filter(fiscal_year=fy)
    assert periods.count() == 12  # Should have 12 months
