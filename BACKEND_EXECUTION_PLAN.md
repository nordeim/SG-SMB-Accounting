# LedgerSG Backend — Execution Plan

## Executive Summary

This document outlines the comprehensive execution plan for building the LedgerSG Django backend API. The backend follows the **MASTER_EXECUTION_PLAN.md** specifications and integrates with the **patched v1.0.1 database schema**.

**Status**: Planning Complete — Ready for Phase 0 Implementation  
**Estimated Duration**: 3-4 weeks  
**Target Python**: 3.13+ (current: 3.12.3)  
**Django Version**: 5.2 LTS  
**Database**: PostgreSQL 16+  

---

## Architecture Overview

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Unmanaged Models** | Django models use `managed = False` — schema is DDL-managed via SQL |
| **Service Layer** | Business logic isolated in `services/` modules, views are thin controllers |
| **RLS Security** | Row-Level Security via PostgreSQL session variables (`app.current_org_id`) |
| **Decimal Precision** | All monetary values use `NUMERIC(10,4)` with `ROUND_HALF_UP` |
| **Atomic Requests** | Every view runs in a single transaction for RLS consistency |
| **JWT Auth** | Access tokens (15min) + HttpOnly refresh cookies (7 days) |

### Module Dependency Graph

```
Phase 0: Foundation
    │   (settings, middleware, decimal utils)
    ▼
Phase 1: Core ──────────────────────────────────────┐
    │   (org, users, auth, roles, fiscal)            │
    ├──────────────┬────────────────┐                │
    ▼              ▼                │                │
Phase 2:      Phase 3:             │                │
COA Module    GST Module           │                │
    │         (tax codes)          │                │
    │              │               │                │
    └──────┬───────┘               │                │
           ▼                       │                │
       Phase 4:                    │                │
       Journal Module              │                │
           │                       │                │
           ▼                       │                │
       Phase 5:                    │                │
       Invoicing Module ◄──────────┘                │
           │                                        │
           ├───────────────┐                        │
           ▼               ▼                        │
       Phase 6:        Phase 7:                     │
       Banking         Peppol                       │
           │               │                        │
           └──────┬────────┘                        │
                  ▼                                 │
              Phase 8:                              │
              Reporting ◄───────────────────────────┘
                  │
                  ▼
              Phase 9:
              Integration & Testing
```

---

## Phase 0: Project Foundation

### Objective
Establish Django project skeleton, configuration, shared utilities, middleware pipeline, and Decimal safety infrastructure.

**Success Criteria**: `python manage.py check` passes, middleware functional, utilities tested.

### Deliverables

| File/Directory | Purpose |
|----------------|---------|
| `pyproject.toml` | Dependencies, tool configuration (PEP 621) |
| `config/settings/base.py` | Shared settings, JWT config, database |
| `config/settings/development.py` | Dev overrides (debug, CORS) |
| `config/settings/production.py` | Production hardening |
| `config/settings/testing.py` | Test optimizations |
| `common/models.py` | Base model classes (BaseModel, TenantModel) |
| `common/decimal_utils.py` | Money precision utilities |
| `common/middleware/tenant_context.py` | **Critical**: RLS session variable injection |
| `common/middleware/audit_context.py` | Request metadata capture |
| `common/db/backend/base.py` | Custom PostgreSQL backend |
| `common/exceptions.py` | Custom exception hierarchy |
| `common/renderers.py` | Decimal-safe JSON renderer |
| `docker-compose.yml` | PostgreSQL 16 + Redis |

### Key Technical Decisions

```python
# Critical: ATOMIC_REQUESTS required for RLS
DATABASES = {
    'default': {
        'ENGINE': 'common.db.backend.base',
        'ATOMIC_REQUESTS': True,  # Required for RLS SET LOCAL
        'OPTIONS': {
            'options': '-c search_path=core,coa,gst,journal,invoicing,banking,audit,public'
        }
    }
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}
```

### Phase 0 Checklist

- [ ] `pyproject.toml` with all dependencies
- [ ] Django boots: `python manage.py check` passes
- [ ] Custom DB backend with search_path
- [ ] Tenant middleware sets `SET LOCAL app.current_org_id`
- [ ] Decimal utilities reject float input
- [ ] Docker Compose: PostgreSQL 16 + Redis
- [ ] pytest-django configured

---

## Phase 1: Core Module

### Objective
Implement tenant root: organisation CRUD, JWT authentication, RBAC, fiscal management.

**Success Criteria**: User can register, create org, log in, receive JWT tokens.

### Deliverables

| Component | Files |
|-----------|-------|
| **Models** | `organisation.py`, `app_user.py`, `role.py`, `user_organisation.py`, `fiscal_year.py`, `fiscal_period.py` |
| **Services** | `auth_service.py`, `organisation_service.py`, `fiscal_service.py`, `sequence_service.py` |
| **Views** | `auth.py`, `organisation.py`, `user.py`, `fiscal.py` |
| **Permissions** | `permissions.py` (IsOrgMember, HasOrgPermission) |
| **Tests** | `test_auth.py`, `test_organisation.py`, `test_permissions.py` |

### Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register/` | Create user account |
| POST | `/api/v1/auth/login/` | Authenticate, return JWT |
| POST | `/api/v1/auth/refresh/` | Refresh access token |
| GET | `/api/v1/auth/me/` | Current user profile |
| GET | `/api/v1/organisations/` | List user's orgs |
| POST | `/api/v1/organisations/` | Create org (seeds CoA) |
| GET | `/api/v1/{org_id}/` | Org detail |

### Critical Implementation Notes

1. **Organisation Creation** calls PostgreSQL function:
   ```python
   cursor.execute("SELECT core.seed_default_chart_of_accounts(%s, %s)", 
                  [org.id, org.gst_registered])
   ```

2. **Document Numbers** use stored procedure:
   ```python
   cursor.execute("SELECT core.next_document_number(%s, %s)",
                  [org_id, document_type])
   ```

3. **Permission Classes** check role flags:
   ```python
   class CanApproveInvoices(HasOrgPermission):
       permission_field = 'can_approve_invoices'
   ```

### Phase 1 Checklist

- [ ] User registration with password hashing
- [ ] JWT login with access + refresh tokens
- [ ] Organisation CRUD with CoA seeding
- [ ] Role-based permissions (Owner, Admin, Accountant, Viewer)
- [ ] Fiscal year/period management
- [ ] Document sequence service
- [ ] All tests passing

---

## Phase 2: Chart of Accounts (COA)

### Objective
Chart of Accounts management with SFRS for Small Entities alignment.

### Deliverables

| Component | Files |
|-----------|-------|
| **Models** | `account.py`, `account_type.py` |
| **Services** | `account_service.py`, `coa_template_service.py` |
| **Views** | `account.py` |
| **Tests** | `test_account.py`, `test_coa_template.py` |

### Key Features

- Account hierarchy (parent-child relationships)
- Account types: Asset, Liability, Equity, Revenue, Expense
- SFRS for Small Entities template
- GST account auto-creation on GST registration
- Account activation/deactivation

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/{org_id}/accounts/` | List accounts |
| POST | `/api/v1/{org_id}/accounts/` | Create account |
| GET | `/api/v1/{org_id}/accounts/{id}/` | Account detail |
| PATCH | `/api/v1/{org_id}/accounts/{id}/` | Update account |

---

## Phase 3: GST Module

### Objective
GST tax code management and calculation service.

### Deliverables

| Component | Files |
|-----------|-------|
| **Models** | `tax_code.py`, `tax_rate.py` |
| **Services** | `gst_calculator_service.py`, `gst_return_service.py` |
| **Views** | `tax_code.py`, `gst_return.py` |
| **Tests** | `test_gst_calculator.py`, `test_gst_return.py` |

### Tax Codes (IRAS Compliant)

| Code | Description | Rate |
|------|-------------|------|
| SR | Standard-rated | 9% |
| ZR | Zero-rated | 0% |
| ES | Exempt | 0% |
| OS | Out-of-scope | 0% |
| TX | Taxable purchase | 9% |
| BL | Blocked input tax | 9% |
| RS | Reverse charge | 9% |

### GST Calculation Service

```python
def calculate_line_gst(net_amount: Decimal, tax_code: str, 
                       is_bcrs_deposit: bool = False) -> GSTResult:
    """
    Calculate GST for a single line item.
    BCRS deposits are excluded from GST per IRAS regulation.
    """
    if is_bcrs_deposit or tax_code in ('ZR', 'ES', 'OS'):
        return GSTResult(gst_amount=Decimal('0'), net_amount=net_amount)
    
    rate = get_tax_rate(tax_code)
    gst = (net_amount * rate).quantize(MONEY_PLACES)
    return GSTResult(gst_amount=gst, net_amount=net_amount)
```

---

## Phase 4: Journal Module

### Objective
Double-entry general ledger with immutable entries.

### Deliverables

| Component | Files |
|-----------|-------|
| **Models** | `journal_entry.py`, `journal_line.py` |
| **Services** | `journal_service.py`, `posting_service.py` |
| **Views** | `journal_entry.py` |
| **Tests** | `test_journal.py`, `test_posting.py` |

### Key Design Decisions

1. **Immutable Entries**: Journal entries cannot be modified after creation
2. **Balance Enforcement**: Database trigger ensures debits = credits
3. **Period Validation**: Posting only to open fiscal periods

### Journal Entry Workflow

```
Draft → Posted → (Immutable)
   │       │
   │       └─ Creates journal_lines (debits/credits)
   │       └─ Updates account balances
   │
   └─ Can be deleted (only in draft)
```

---

## Phase 5: Invoicing Module

### Objective
Sales and purchase document management with GST integration.

### Deliverables

| Component | Files |
|-----------|-------|
| **Models** | `contact.py`, `document.py`, `document_line.py` |
| **Services** | `invoice_service.py`, `document_workflow_service.py` |
| **Views** | `contact.py`, `document.py` |
| **Tests** | `test_invoice.py`, `test_workflow.py` |

### Document Types

| Type | Description |
|------|-------------|
| INVOICE | Sales invoice |
| CREDIT_NOTE | Credit note |
| DEBIT_NOTE | Debit note |
| PURCHASE_ORDER | Purchase order |
| QUOTE | Quote/estimate |

### Document Workflow

```
DRAFT → APPROVED → SENT → PAID
   │         │        │      │
   │         │        │      └─ Full payment received
   │         │        └─ Email/Peppol sent
   │         └─ Journal entry created
   └─ Can edit, delete
```

### Critical Features

- Line-level GST calculation with BCRS support
- Document numbering via sequence service
- Amount due is GENERATED column (auto-calculated)
- Approval creates journal entries
- Voiding creates reversal entries

---

## Phase 6: Banking Module

### Objective
Bank accounts, payments, and reconciliation.

### Deliverables

| Component | Files |
|-----------|-------|
| **Models** | `bank_account.py`, `payment.py`, `reconciliation.py` |
| **Services** | `payment_service.py`, `reconciliation_service.py` |
| **Views** | `bank_account.py`, `payment.py` |
| **Tests** | `test_payment.py`, `test_reconciliation.py` |

### Features

- Multiple bank accounts per organisation
- Payment recording (receive/make payments)
- Bank reconciliation
- Foreign currency handling with FX gain/loss

---

## Phase 7: Peppol/InvoiceNow Module

### Objective
InvoiceNow (Peppol) e-invoicing integration.

### Deliverables

| Component | Files |
|-----------|-------|
| **Models** | `peppol_transmission_log.py` |
| **Services** | `peppol_service.py`, `xml_generator_service.py` |
| **Views** | `peppol.py` |
| **Tasks** | `peppol_tasks.py` (Celery) |
| **Tests** | `test_peppol.py`, `test_xml_generator.py` |

### Features

- PINT-SG XML generation
- Peppol Access Point integration
- Transmission status tracking
- Retry mechanism with exponential backoff
- Audit logging

---

## Phase 8: Reporting Module

### Objective
Financial reports: P&L, Balance Sheet, Trial Balance, GST F5.

### Deliverables

| Component | Files |
|-----------|-------|
| **Services** | `report_service.py`, `gst_f5_service.py` |
| **Views** | `reports.py` |
| **Tests** | `test_reports.py`, `test_gst_f5.py` |

### Reports

| Report | Description |
|--------|-------------|
| Profit & Loss | Revenue - Expenses |
| Balance Sheet | Assets = Liabilities + Equity |
| Trial Balance | All account balances |
| GST F5 | IRAS GST return (all 15 boxes) |

### GST F5 Integration

Uses PostgreSQL stored procedure:
```python
cursor.execute("SELECT * FROM gst.generate_f5_return(%s, %s, %s)",
               [org_id, period_start, period_end])
```

---

## Phase 9: Integration & Testing

### Objective
End-to-end testing, security hardening, performance optimization.

### Deliverables

| Component | Description |
|-----------|-------------|
| **Integration Tests** | Frontend-backend API contract tests |
| **Security Audit** | OWASP Top 10 check |
| **Performance** | Query optimization, indexing |
| **Documentation** | API docs (OpenAPI/Swagger) |

### Testing Strategy

| Test Type | Tools | Coverage |
|-----------|-------|----------|
| Unit Tests | pytest | 90%+ |
| Integration Tests | pytest-django | API endpoints |
| E2E Tests | Playwright | Critical flows |

---

## Implementation Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0 | 2-3 days | None |
| Phase 1 | 4-5 days | Phase 0 |
| Phase 2 | 2-3 days | Phase 1 |
| Phase 3 | 2-3 days | Phase 1 |
| Phase 4 | 3-4 days | Phase 2, 3 |
| Phase 5 | 5-6 days | Phase 1, 3, 4 |
| Phase 6 | 3-4 days | Phase 1, 4 |
| Phase 7 | 4-5 days | Phase 5 |
| Phase 8 | 3-4 days | Phase 4, 5 |
| Phase 9 | 3-4 days | All phases |
| **Total** | **31-41 days** | |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RLS complexity | Medium | High | Extensive testing, middleware review |
| Decimal precision | Low | Critical | Test-driven development, audit trails |
| GST calculation | Medium | High | 100% test coverage, IRAS examples |
| Peppol integration | Medium | Medium | Mock services, retry logic |

---

## Next Steps

1. **Begin Phase 0**: Create project foundation
2. **Set up PostgreSQL**: Run database_schema.sql v1.0.1
3. **Verify environment**: Python 3.13+, Docker, Redis

**Ready to proceed with Phase 0?**
