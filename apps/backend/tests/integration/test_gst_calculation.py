"""
Integration tests for GST Calculation.

Tests IRAS-compliant GST calculations including BCRS exemption.
"""

import pytest
from decimal import Decimal
from rest_framework import status


@pytest.mark.django_db
def test_gst_standard_rated_calculation(auth_client, test_organisation, test_tax_codes):
    """Test standard-rated (9%) GST calculation."""
    url = "/api/v1/gst/calculate/"
    
    response = auth_client.post(url, {
        "org_id": str(test_organisation.id),
        "amount": "100.00",
        "rate": "0.09",
        "is_bcrs_deposit": False
    }, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["net_amount"] == "100.00"
    assert response.data["gst_amount"] == "9.00"  # 9% of 100
    assert response.data["total_amount"] == "109.00"
    assert response.data["is_bcrs_exempt"] is False


@pytest.mark.django_db
def test_gst_zero_rated_calculation(auth_client, test_organisation, test_tax_codes):
    """Test zero-rated (0%) GST calculation."""
    url = "/api/v1/gst/calculate/"
    
    response = auth_client.post(url, {
        "org_id": str(test_organisation.id),
        "amount": "1000.00",
        "rate": "0.00",
        "is_bcrs_deposit": False
    }, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["net_amount"] == "1000.00"
    assert response.data["gst_amount"] == "0.00"
    assert response.data["total_amount"] == "1000.00"


@pytest.mark.django_db
def test_gst_bcrs_exemption(auth_client, test_organisation, test_tax_codes):
    """Test BCRS deposit GST exemption (Singapore-specific)."""
    url = "/api/v1/gst/calculate/"
    
    # Even with 9% rate, BCRS should have 0 GST
    response = auth_client.post(url, {
        "org_id": str(test_organisation.id),
        "amount": "0.10",  # BCRS deposit amount
        "rate": "0.09",
        "is_bcrs_deposit": True
    }, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["net_amount"] == "0.10"
    assert response.data["gst_amount"] == "0.00"  # No GST on BCRS
    assert response.data["is_bcrs_exempt"] is True


@pytest.mark.django_db
def test_gst_document_calculation(auth_client, test_organisation, test_tax_codes):
    """Test multi-line document GST calculation."""
    url = "/api/v1/gst/calculate/document/"
    
    response = auth_client.post(url, {
        "lines": [
            {
                "amount": "100.00",
                "rate": "0.09",
                "is_bcrs_deposit": False
            },
            {
                "amount": "50.00",
                "rate": "0.09",
                "is_bcrs_deposit": False
            },
            {
                "amount": "0.10",
                "rate": "0.09",
                "is_bcrs_deposit": True  # BCRS exempt
            }
        ],
        "default_rate": "0.09"
    }, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    
    # Verify summary
    summary = response.data["summary"]
    assert summary["total_net"] == "150.10"  # 100 + 50 + 0.10
    assert summary["total_gst"] == "13.50"   # (100 + 50) * 0.09
    assert summary["total_amount"] == "163.60"  # 150.10 + 13.50
    assert summary["bcrs_exempt_total"] == "0.10"
    assert summary["taxable_amount"] == "150.00"  # Excluding BCRS


@pytest.mark.django_db
def test_gst_precision_rounding(auth_client, test_organisation, test_tax_codes):
    """Test GST rounding to 2 decimal places (IRAS standard)."""
    url = "/api/v1/gst/calculate/"
    
    # Amount that produces fractional GST
    response = auth_client.post(url, {
        "org_id": str(test_organisation.id),
        "amount": "33.33",  # GST = 2.9997, should round to 3.00
        "rate": "0.09",
        "is_bcrs_deposit": False
    }, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    # Should round to 2 decimal places
    gst = Decimal(response.data["gst_amount"])
    assert gst == Decimal("3.00")


@pytest.mark.django_db
def test_gst_tax_code_info(auth_client):
    """Test getting IRAS tax code information."""
    url = "/api/v1/gst/tax-codes/iras-info/"
    
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.data
    
    # Should have SR code info
    codes = response.data["data"]
    assert "SR" in codes
    assert codes["SR"]["rate"] == "0.09"
    assert codes["SR"]["box_mapping"] == "box1"


@pytest.mark.django_db
def test_gst_iras_compliance_validation(auth_client, test_organisation):
    """Test IRAS compliance validation."""
    from apps.gst.services import GSTCalculationService
    
    # Test IRAS example calculations
    test_cases = [
        # (amount, rate, expected_gst)
        (Decimal("100.00"), Decimal("0.09"), Decimal("9.00")),
        (Decimal("50.00"), Decimal("0.09"), Decimal("4.50")),
        (Decimal("10.00"), Decimal("0.09"), Decimal("0.90")),
    ]
    
    for amount, rate, expected_gst in test_cases:
        result = GSTCalculationService.calculate_line_gst(
            amount=amount,
            rate=rate,
            is_bcrs_deposit=False
        )
        
        assert result["gst_amount"] == expected_gst, \
            f"GST for {amount} @ {rate} should be {expected_gst}, got {result['gst_amount']}"


@pytest.mark.django_db
def test_gst_f5_generation(auth_client, test_organisation, test_fiscal_period, test_accounts, test_tax_codes):
    """Test F5 form generation."""
    from apps.core.models import GSTReturn
    from apps.gst.services import GSTReturnService
    
    # Create a GST return period
    gst_return = GSTReturn.objects.create(
        org=test_organisation,
        fiscal_period=test_fiscal_period,
        period_start=test_fiscal_period.start_date,
        period_end=test_fiscal_period.end_date,
        due_date=test_fiscal_period.end_date,
        filing_frequency="MONTHLY",
        label="Jan 2024",
        status="DRAFT",
    )
    
    # Generate F5
    url = f"/api/v1/{test_organisation.id}/gst/returns/{gst_return.id}/"
    response = auth_client.post(url, {}, format="json")
    
    # Should succeed (even if empty, no invoices yet)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]


@pytest.mark.django_db
def test_gst_create_return_periods(auth_client, test_organisation):
    """Test creating GST return periods."""
    url = f"/api/v1/{test_organisation.id}/gst/returns/"
    
    response = auth_client.post(url, {
        "filing_frequency": "MONTHLY",
        "start_date": "2024-01-01",
        "periods": 3
    }, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["count"] == 3


@pytest.mark.django_db
def test_gst_deadlines(auth_client, test_organisation, test_fiscal_period):
    """Test upcoming GST filing deadlines."""
    from apps.core.models import GSTReturn
    
    # Create a return with upcoming deadline
    GSTReturn.objects.create(
        org=test_organisation,
        fiscal_period=test_fiscal_period,
        period_start=test_fiscal_period.start_date,
        period_end=test_fiscal_period.end_date,
        due_date=test_fiscal_period.end_date,
        filing_frequency="MONTHLY",
        label="Jan 2024",
        status="DRAFT",
    )
    
    url = f"/api/v1/{test_organisation.id}/gst/returns/deadlines/"
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.data
