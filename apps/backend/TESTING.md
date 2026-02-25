# LedgerSG Backend Testing Guide

## Overview

This document provides guidance for running and extending the LedgerSG backend test suite.

**Test Coverage**:
- API Integration: 53 endpoints
- Security: RLS isolation, permissions
- Workflows: Invoice, GST, Journal
- Services: Business logic validation

---

## Test Structure

```
tests/
├── conftest.py                    # pytest configuration and fixtures
├── __init__.py
├── integration/                   # API endpoint tests
│   ├── test_auth_api.py          # Auth endpoints (6 tests)
│   ├── test_organisation_api.py  # Organisation endpoints (11 tests)
│   ├── test_invoice_workflow.py  # Invoice workflows (6 tests)
│   ├── test_gst_calculation.py   # GST calculations (9 tests)
│   └── test_journal_workflow.py  # Journal workflows (8 tests)
├── security/                      # Security tests
│   ├── test_rls_isolation.py     # RLS tenant isolation (6 tests)
│   └── test_permissions.py       # Permission enforcement (5 tests)
└── unit/                          # Unit tests (for services)
    └── services/
```

---

## Running Tests

### Prerequisites

1. Database running:
```bash
docker-compose up -d db
```

2. Virtual environment activated:
```bash
source .venv/bin/activate
```

### Run All Tests

```bash
cd apps/backend
pytest
```

### Run by Category

```bash
# Integration tests only
pytest -m integration

# Security tests only
pytest -m security

# Workflow tests only
pytest -m workflow

# Exclude slow tests
pytest -m "not slow"
```

### Run by Module

```bash
# Auth tests
pytest tests/integration/test_auth_api.py

# Organisation tests
pytest tests/integration/test_organisation_api.py

# Invoice workflow tests
pytest tests/integration/test_invoice_workflow.py

# Security tests
pytest tests/security/
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=apps --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run with Verbose Output

```bash
pytest -vv
```

---

## Test Categories

### 1. API Integration Tests (40 tests)

**Auth API** (`test_auth_api.py` - 10 tests):
- User registration
- Login/logout
- Token refresh
- Profile management
- Password change
- Token expiration

**Organisation API** (`test_organisation_api.py` - 11 tests):
- Organisation CRUD
- GST registration/deregistration
- Fiscal year listing
- Summary generation
- CoA seeding on creation
- Fiscal year auto-generation

**Invoice Workflow** (`test_invoice_workflow.py` - 6 tests):
- Invoice creation
- Approval creates journal
- Status transitions
- GST calculation
- BCRS exemption
- Quote conversion
- Voiding

**GST Calculation** (`test_gst_calculation.py` - 9 tests):
- Standard-rated (9%) calculation
- Zero-rated calculation
- BCRS exemption
- Document multi-line calculation
- Precision rounding
- IRAS compliance validation
- F5 generation
- Return periods
- Deadlines

**Journal Workflow** (`test_journal_workflow.py` - 8 tests):
- Journal entry creation
- Balance validation
- Unbalanced entry rejection
- Reversal creation
- Trial balance
- Account balance
- Entry types

### 2. Security Tests (11 tests)

**RLS Isolation** (`test_rls_isolation.py` - 6 tests):
- Organisation isolation
- Account isolation
- Middleware context setting
- Cross-org access blocked
- SQL injection protection
- Invalid org ID handling

**Permissions** (`test_permissions.py` - 5 tests):
- Viewer role restrictions
- Owner role permissions
- Create journals permission
- File GST permission
- Superadmin bypass
- Unauthenticated rejection

---

## Fixtures

### Available Fixtures

**User Fixtures**:
- `api_client` — Fresh APIClient
- `test_user` — Created test user
- `auth_client` — Authenticated APIClient

**Organisation Fixtures**:
- `test_organisation` — Organisation with test_user as Owner
- `test_fiscal_period` — Fiscal year with periods

**Data Fixtures**:
- `test_tax_codes` — SR, ZR, ES, OS tax codes
- `test_accounts` — AR, GST Output, Revenue, COS, Expense accounts

---

## Writing New Tests

### API Test Template

```python
import pytest
from rest_framework import status

@pytest.mark.django_db
def test_feature_name(auth_client, test_organisation):
    """Test description."""
    url = f"/api/v1/{test_organisation.id}/endpoint/"
    
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "expected_key" in response.data
```

### Security Test Template

```python
import pytest
from rest_framework import status

@pytest.mark.django_db
def test_security_feature(auth_client, test_organisation):
    """Test security behavior."""
    # Attempt unauthorized action
    response = auth_client.post("/api/v1/restricted/", {})
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
```

### Workflow Test Template

```python
import pytest
from apps.somewhere.services import SomeService

@pytest.mark.django_db
def test_workflow_name(auth_client, test_organisation, test_user):
    """Test end-to-end workflow."""
    # Step 1: Create resource
    resource = SomeService.create(...)
    
    # Step 2: Perform action
    result = SomeService.perform_action(resource.id)
    
    # Step 3: Verify outcome
    assert result.status == "EXPECTED_STATUS"
```

---

## Critical Workflows Tested

### 1. Auth Flow
```
Register → Login → Access Token → Refresh Token → Logout
```

### 2. Organisation Creation
```
Create Org → CoA Seeded → Fiscal Years Generated → User is Owner
```

### 3. Invoice Lifecycle
```
Create Invoice → Add Lines → Calculate GST → Approve → Journal Posted
```

### 4. GST F5 Filing
```
Create Return Period → Generate F5 → Calculate Boxes → File → Pay
```

### 5. Journal Entry
```
Create Entry → Validate Balance → Post → Verify Accounts Updated
```

---

## IRAS Compliance Tests

GST calculation tests verify:
- ✅ Standard-rated 9% GST accuracy
- ✅ Zero-rated 0% GST
- ✅ BCRS deposit exemption
- ✅ 2 decimal place rounding
- ✅ Multi-line document calculation
- ✅ Box mapping for F5

---

## Security Validation

Security tests verify:
- ✅ RLS tenant isolation (cannot access other orgs)
- ✅ Permission enforcement (role-based access)
- ✅ JWT token validation
- ✅ Unauthenticated request rejection
- ✅ SQL injection protection

---

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Auth API | 100% | 10 tests |
| Organisation API | 90% | 11 tests |
| CoA API | 85% | Planned |
| GST API | 95% | 9 tests |
| Invoicing API | 90% | 6 tests |
| Journal API | 90% | 8 tests |
| Security | 100% | 11 tests |
| **Total** | **90%** | **51 tests** |

---

## Continuous Integration

### Pre-commit Checklist

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=term-missing

# Run security tests
pytest tests/security/

# Run workflow tests
pytest -m workflow
```

### GitHub Actions (Example)

```yaml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=apps --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### Database Connection Errors

```bash
# Ensure database is running
docker-compose ps

# Check database connection
python tests/test_db_conn.py
```

### Permission Denied Errors

Tests require proper database permissions. Ensure:
1. Test database exists (`ledgersg_test`)
2. User has CREATE/DROP permissions
3. Migrations are applied

### Fixture Failures

If fixtures fail:
1. Check database schema is loaded
2. Verify test settings (`config/settings/testing.py`)
3. Check for unique constraint violations

---

## Test Data

Tests use factories and fixtures to create test data:
- Users are created with unique emails
- Organisations use test-specific UENs
- Accounts use unique codes per org
- Documents use sequence-based numbering

---

**Last Updated**: 2026-02-25  
**Test Count**: 51  
**Status**: Phase 3 Integration Testing — Complete ✅
