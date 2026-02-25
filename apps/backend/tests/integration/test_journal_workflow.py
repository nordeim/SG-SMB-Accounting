"""
Integration tests for Journal Entry Workflow.

Tests double-entry accounting including balance validation and reversals.
"""

import pytest
from decimal import Decimal
from datetime import date
from rest_framework import status

from apps.core.models import JournalEntry, JournalLine


@pytest.mark.django_db
def test_create_journal_entry_success(auth_client, test_organisation, test_accounts, test_fiscal_period):
    """Test creating a balanced journal entry."""
    url = f"/api/v1/{test_organisation.id}/journal-entries/entries/"
    
    ar_account = test_accounts["1200"]  # Accounts Receivable
    revenue_account = test_accounts["4000"]  # Sales Revenue
    
    response = auth_client.post(url, {
        "entry_date": "2024-01-15",
        "entry_type": "MANUAL",
        "description": "Test journal entry",
        "fiscal_period_id": str(test_fiscal_period.id),
        "lines": [
            {
                "account_id": str(ar_account.id),
                "description": "AR increase",
                "debit": "100.00",
                "credit": "0.00"
            },
            {
                "account_id": str(revenue_account.id),
                "description": "Revenue recognition",
                "debit": "0.00",
                "credit": "100.00"
            }
        ]
    }, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["entry_type"] == "MANUAL"
    assert response.data["is_posted"] is True


@pytest.mark.django_db
def test_journal_entry_unbalanced_rejected(auth_client, test_organisation, test_accounts, test_fiscal_period):
    """Test that unbalanced journal entries are rejected."""
    url = f"/api/v1/{test_organisation.id}/journal-entries/entries/"
    
    ar_account = test_accounts["1200"]
    
    response = auth_client.post(url, {
        "entry_date": "2024-01-15",
        "entry_type": "MANUAL",
        "description": "Unbalanced entry",
        "lines": [
            {
                "account_id": str(ar_account.id),
                "description": "Only debit",
                "debit": "100.00",
                "credit": "0.00"
            }
        ]
    }, format="json")
    
    # Should fail validation
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_journal_entry_validate_balance(auth_client, test_organisation, test_accounts):
    """Test the balance validation endpoint."""
    url = f"/api/v1/{test_organisation.id}/journal-entries/entries/validate/"
    
    ar_account = test_accounts["1200"]
    revenue_account = test_accounts["4000"]
    
    # Valid balanced entry
    response = auth_client.post(url, {
        "lines": [
            {
                "account_id": str(ar_account.id),
                "debit": "100.00",
                "credit": "0.00"
            },
            {
                "account_id": str(revenue_account.id),
                "debit": "0.00",
                "credit": "100.00"
            }
        ]
    }, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["valid"] is True
    assert response.data["total_debits"] == "100.00"
    assert response.data["total_credits"] == "100.00"
    assert response.data["difference"] == "0.00"


@pytest.mark.django_db
def test_journal_entry_validate_unbalanced(auth_client, test_organisation, test_accounts):
    """Test validation catches unbalanced entries."""
    url = f"/api/v1/{test_organisation.id}/journal-entries/entries/validate/"
    
    ar_account = test_accounts["1200"]
    
    # Unbalanced entry
    response = auth_client.post(url, {
        "lines": [
            {
                "account_id": str(ar_account.id),
                "debit": "100.00",
                "credit": "0.00"
            },
            {
                "account_id": str(ar_account.id),
                "debit": "50.00",
                "credit": "0.00"
            }
        ]
    }, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["valid"] is False
    assert response.data["difference"] == "50.00"


@pytest.mark.django_db
def test_journal_entry_reversal(auth_client, test_organisation, test_accounts, test_fiscal_period):
    """Test creating a reversal entry."""
    from apps.journal.services import JournalService
    
    ar_account = test_accounts["1200"]
    revenue_account = test_accounts["4000"]
    
    # Create original entry
    original = JournalService.create_entry(
        org_id=test_organisation.id,
        entry_date=date(2024, 1, 15),
        entry_type="MANUAL",
        description="Original entry",
        lines=[
            {"account_id": ar_account.id, "debit": Decimal("100.00"), "credit": Decimal("0.00"), "description": "AR"},
            {"account_id": revenue_account.id, "debit": Decimal("0.00"), "credit": Decimal("100.00"), "description": "Revenue"}
        ],
        fiscal_period_id=test_fiscal_period.id
    )
    
    # Create reversal
    url = f"/api/v1/{test_organisation.id}/journal-entries/entries/{original.id}/reverse/"
    response = auth_client.post(url, {
        "reversal_date": "2024-01-20",
        "reason": "Correction needed"
    }, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "reversal" in response.data
    
    # Verify reversal swaps debits and credits
    reversal = JournalEntry.objects.get(id=response.data["reversal"]["id"])
    lines = list(reversal.lines.all())
    
    # Original: AR debit 100, Revenue credit 100
    # Reversal: AR credit 100, Revenue debit 100
    ar_line = [l for l in lines if l.account_id == ar_account.id][0]
    revenue_line = [l for l in lines if l.account_id == revenue_account.id][0]
    
    assert ar_line.debit == Decimal("0.00")
    assert ar_line.credit == Decimal("100.00")
    assert revenue_line.debit == Decimal("100.00")
    assert revenue_line.credit == Decimal("0.00")


@pytest.mark.django_db
def test_trial_balance(auth_client, test_organisation, test_accounts, test_fiscal_period):
    """Test trial balance generation."""
    from apps.journal.services import JournalService
    
    ar_account = test_accounts["1200"]
    revenue_account = test_accounts["4000"]
    
    # Create a journal entry
    JournalService.create_entry(
        org_id=test_organisation.id,
        entry_date=date(2024, 1, 15),
        entry_type="MANUAL",
        description="Test entry",
        lines=[
            {"account_id": ar_account.id, "debit": Decimal("200.00"), "credit": Decimal("0.00"), "description": "AR"},
            {"account_id": revenue_account.id, "debit": Decimal("0.00"), "credit": Decimal("200.00"), "description": "Revenue"}
        ],
        fiscal_period_id=test_fiscal_period.id
    )
    
    url = f"/api/v1/{test_organisation.id}/journal-entries/trial-balance/"
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.data
    assert "totals" in response.data
    assert response.data["totals"]["balanced"] is True


@pytest.mark.django_db
def test_account_balance(auth_client, test_organisation, test_accounts, test_fiscal_period):
    """Test getting account running balance."""
    from apps.journal.services import JournalService
    
    ar_account = test_accounts["1200"]
    revenue_account = test_accounts["4000"]
    
    # Create entries
    JournalService.create_entry(
        org_id=test_organisation.id,
        entry_date=date(2024, 1, 15),
        entry_type="MANUAL",
        description="Entry 1",
        lines=[
            {"account_id": ar_account.id, "debit": Decimal("100.00"), "credit": Decimal("0.00"), "description": "AR"},
            {"account_id": revenue_account.id, "debit": Decimal("0.00"), "credit": Decimal("100.00"), "description": "Revenue"}
        ],
        fiscal_period_id=test_fiscal_period.id
    )
    
    # Get AR balance
    url = f"/api/v1/{test_organisation.id}/journal-entries/accounts/{ar_account.id}/balance/"
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["account_code"] == ar_account.code
    assert Decimal(response.data["balance"]) == Decimal("100.00")


@pytest.mark.django_db
def test_journal_entry_types(auth_client):
    """Test getting journal entry types."""
    url = "/api/v1/journal-entries/entries/types/"
    
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.data
    
    # Should have standard entry types
    types = [t["code"] for t in response.data["data"]]
    assert "MANUAL" in types
    assert "INVOICE" in types
    assert "ADJUSTMENT" in types
