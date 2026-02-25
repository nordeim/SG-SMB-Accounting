# LedgerSG Backend — Current Status

## Overview

The LedgerSG backend is currently in the **planning phase**. All design documents are complete, and the database schema v1.0.1 is ready for implementation.

| Component | Status | Notes |
|-----------|--------|-------|
| **MASTER_EXECUTION_PLAN.md** | ✅ Complete | 102KB comprehensive implementation plan |
| **database_schema.sql** | ✅ Complete | v1.0.1 with 8 critical patches applied |
| **Django Project** | 🚧 Not Started | Phase 0 pending |
| **Core Module** | 🚧 Not Started | Phase 1 pending |
| **COA Module** | 🚧 Not Started | Phase 2 pending |
| **GST Module** | 🚧 Not Started | Phase 3 pending |
| **Journal Module** | 🚧 Not Started | Phase 4 pending |
| **Invoicing Module** | 🚧 Not Started | Phase 5 pending |
| **Banking Module** | 🚧 Not Started | Phase 6 pending |
| **Peppol Module** | 🚧 Not Started | Phase 7 pending |
| **Reporting Module** | 🚧 Not Started | Phase 8 pending |
| **Integration Tests** | 🚧 Not Started | Phase 9 pending |

---

## Database Schema v1.0.1

### Schema Structure

| Schema | Purpose | Tables |
|--------|---------|--------|
| `core` | Organisation, users, roles, fiscal | 15+ tables |
| `coa` | Chart of Accounts | 3 tables |
| `gst` | Tax codes, rates, F5 returns | 5+ tables |
| `journal` | General Ledger | 4 tables |
| `invoicing` | Contacts, documents, lines | 6 tables |
| `banking` | Bank accounts, payments | 4 tables |
| `audit` | Immutable audit trail | 2 tables |

### Critical Patches Applied

1. ✅ **GST Function Volatility**: IMMUTABLE → STABLE
2. ✅ **BCRS Deposit Flag**: `is_bcrs_deposit` column added
3. ✅ **Journal Balance Trigger**: Deferrable constraint trigger
4. ✅ **GST F5 All 15 Boxes**: Complete IRAS compliance
5. ✅ **amount_due Generated Column**: Auto-calculated
6. ✅ **Audit Org-Scoped View**: `audit.org_event_log`
7. ✅ **Peppol Transmission Log**: Retry tracking
8. ✅ **Fiscal Period Audit Trail**: locked_by, closed_by

---

## Implementation Plan

### Phase Breakdown

```
Phase 0: Foundation (2-3 days)
├── pyproject.toml
├── config/settings/
├── common/ (middleware, utils)
└── docker-compose.yml

Phase 1: Core Module (4-5 days)
├── Auth (JWT, registration, login)
├── Organisation CRUD
├── RBAC (roles, permissions)
└── Fiscal management

Phase 2-8: Business Modules (20-25 days)
├── COA, GST, Journal
├── Invoicing, Banking
├── Peppol, Reporting

Phase 9: Integration (3-4 days)
├── API testing
├── Security audit
└── Performance optimization
```

---

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.13+ |
| Framework | Django | 5.2 LTS |
| API | Django REST Framework | 3.15+ |
| Auth | djangorestframework-simplejwt | 5.3+ |
| Database | PostgreSQL | 16+ |
| Cache/Broker | Redis | 7+ |
| Tasks | Celery | 5.4+ |
| Testing | pytest-django | 4.8+ |

---

## Key Architectural Decisions

1. **Unmanaged Models**: Schema is DDL-managed, Django models use `managed = False`
2. **RLS Security**: Multi-tenancy via PostgreSQL Row-Level Security
3. **Service Layer**: Business logic in services/, thin views
4. **Decimal Precision**: All money as `NUMERIC(10,4)` with `ROUND_HALF_UP`
5. **Atomic Requests**: Every view in single transaction for RLS

---

## Next Actions

1. Create `pyproject.toml` with dependencies
2. Initialize Django project structure
3. Configure custom database backend
4. Implement tenant context middleware
5. Create base model classes
6. Set up Docker Compose (PostgreSQL + Redis)
7. Run database schema
8. Begin Core Module development

---

**Status**: Ready for Phase 0 Implementation
**Updated**: 2026-02-24
