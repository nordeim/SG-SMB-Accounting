# LedgerSG — Comprehensive Developer Briefing

> **Single Source of Truth** for coding agents and human developers  
> **Version**: 1.1.0  
> **Last Updated**: 2026-02-27  
> **Status**: Production Ready ✅ (Database & Model Hardening Complete)

---

## 📋 Table of Contents

1. [Executive Summary](#-executive-summary)
2. [Project Architecture](#-project-architecture)
3. [Backend Deep Dive](#-backend-deep-dive)
4. [Frontend Deep Dive](#-frontend-deep-dive)
5. [Database Architecture](#-database-architecture)
6. [IRAS Compliance & GST](#-iras-compliance--gst)
7. [Security Architecture](#-security-architecture)
8. [Testing Strategy](#-testing-strategy)
9. [Development Guidelines](#-development-guidelines)
10. [API Reference](#-api-reference)
11. [Common Development Tasks](#-common-development-tasks)
12. [Troubleshooting](#-troubleshooting)

---

## 🎯 Executive Summary

**LedgerSG** is a production-grade, double-entry accounting platform purpose-built for Singapore SMBs. It transforms IRAS compliance from a burden into a seamless, automated experience while delivering a distinctive "Illuminated Carbon" neo-brutalist user interface.

### Current Status

| Component | Version | Status | Key Metrics |
|-----------|---------|--------|-------------|
| **Frontend** | v0.1.0 | ✅ Production Ready | 18 static pages, 114 tests |
| **Backend** | v0.3.1 | ✅ Production Ready | 57 API endpoints, schema hardened |
| **Database** | v1.0.2 | ✅ Complete | 7 schemas, RLS enforced, 28 tables |
| **Overall** | — | ✅ Platform Ready | 156+ tests, WCAG AAA, IRAS Compliant |

---

## 🏗 Project Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Next.js    │  │  Zustand     │  │  TanStack    │          │
│  │   16 PWA     │  │  (UI State)  │  │  Query       │          │
│  └──────┬───────┘  └──────────────┘  └──────────────┘          │
└─────────┼───────────────────────────────────────────────────────┘
          │ HTTPS + JWT Access Token (15min)
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SECURITY LAYER                             │
│  JWT Auth │ HttpOnly Refresh Cookie │ CSRF │ Rate Limiting      │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (Django)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  DRF Views   │  │   Services   │  │  Middleware  │          │
│  │  (Thin)      │  │ (Business)   │  │ (RLS/Auth)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER (PostgreSQL)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  7 Schemas   │  │     RLS      │  │  NUMERIC     │          │
│  │ (domain)     │  │ (session)    │  │ (10,4)       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Backend Deep Dive

### Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Framework | Django | 6.0.2 | Web framework |
| API | Django REST Framework | 3.16.1 | REST endpoints |
| Auth | djangorestframework-simplejwt | Latest | JWT authentication |
| Database | PostgreSQL | 16+ | Primary data store |
| Task Queue | Celery + Redis | 5.4+ / 7+ | Async processing |
| Testing | pytest-django | Latest | Unit/integration tests |

### Backend Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| API Endpoints | **57** | 100% Alignment |
| Service Files | 6 | Core business logic |
| Models | **17** | 14 core + 3 restored |
| Test Files | 11 | 156+ total tests |
| Lines of Code | **~10,500+** | Business logic |

### Design Principles

| Principle | Implementation | Critical Notes |
|-----------|----------------|----------------|
| **Unmanaged Models** | `managed = False` | Schema is DDL-managed via SQL. Models map to existing tables. |
| **Service Layer** | `services/` modules | Views are thin controllers. ALL business logic lives in services. |
| **RLS Security** | PostgreSQL session variables | `SET LOCAL app.current_org_id = 'uuid'` per transaction |
| **Decimal Precision** | `NUMERIC(10,4)` | NEVER use float for money. Use `common.decimal_utils.money()` |
| **Atomic Requests** | `ATOMIC_REQUESTS: True` | Every view runs in single transaction for RLS consistency |
| **JWT Auth** | Access 15min / Refresh 7d | HttpOnly cookies for refresh tokens |

### Directory Structure

```
apps/backend/
├── apps/
│   ├── core/              # Auth, Organisation, Users, Fiscal
│   │   ├── models/        # Restored: AppUser, Role, JournalEntry, InvoiceLine, etc.
│   │   ├── services/      # auth_service.py, organisation_service.py
│   │   ├── views/         # auth.py, organisations.py
│   │   └── serializers/   # auth.py, organisation.py
│   ├── coa/               # Chart of Accounts
│   ├── gst/               # GST Module
│   ├── invoicing/         # Invoicing
│   ├── journal/           # Journal Entry
│   ├── banking/           # Banking
│   └── reporting/         # Dashboard & Reports
├── common/                # Shared utilities
│   ├── decimal_utils.py   # CRITICAL: Money precision utilities
│   ├── models.py          # BaseModel, TenantModel, SequenceModel
│   ├── middleware/        # tenant_context.py (RLS), audit_context.py
├── config/                # Django configuration
└── tests/                 # Test suite
```

---

## 🎨 Frontend Deep Dive

### Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Framework | Next.js | 16.1.6 | App Router, SSG, Static Export |
| UI Library | React | 19.2.3 | Concurrent features |
| Styling | Tailwind CSS | 4.0 | CSS-first @theme configuration |
| Components | Radix UI + Shadcn | Latest | Headless primitives |
| State (Server) | TanStack Query | v5 | Server-state caching |
| State (Client) | Zustand | v5 | UI state |
| Decimal | decimal.js | v10.6 | Client-side GST preview |

### Directory Structure

```
apps/web/src/
├── app/                          # Next.js App Router
├── components/                   # UI Primitives & Domain components
├── lib/                          # api-client.ts, gst-engine.ts
├── hooks/                        # TanStack Query hooks (use-invoices.ts, etc.)
├── providers/                    # AuthProvider, ToastProvider
├── stores/                       # Zustand stores (invoice-store.ts)
└── shared/
    └── schemas/                  # Zod validation schemas
```

---

## 🗄 Database Architecture

### PostgreSQL Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| **Schemas** | 7 (core, coa, gst, journal, invoicing, banking, audit) | Domain separation |
| **Money Precision** | `NUMERIC(10,4)` | 4 decimal places for all amounts |
| **RLS** | Session variable `app.current_org_id` | Multi-tenant isolation |
| **Primary Keys** | UUID (`gen_random_uuid()`) | Distributed-safe |

---

## 🧪 Testing Strategy

### Backend Tests (156+ total across system)

```bash
# Manual test database setup for unmanaged models
export PGPASSWORD=ledgersg_secret_to_change
dropdb -h localhost -U ledgersg test_ledgersg_dev
createdb -h localhost -U ledgersg test_ledgersg_dev
psql -h localhost -U ledgersg -d test_ledgersg_dev -f database_schema.sql

# Run tests with reuse flags
source /opt/venv/bin/activate
cd apps/backend
pytest --reuse-db --no-migrations
```

### Frontend Tests (114 total)

```bash
cd apps/web
npm test
```

---

## 🔧 Troubleshooting

### Unmanaged Models & Testing
**Problem**: Tests fail with `relation "core.app_user" does not exist`.
**Cause**: `pytest-django` cannot run migrations on unmanaged models (`managed = False`).
**Solution**: Manually initialize the test database using `database_schema.sql` and run `pytest --reuse-db --no-migrations`.

### SQL Circular Dependencies
**Problem**: Database initialization fails on foreign keys.
**Cause**: Circular references (e.g., `organisation` <-> `app_user`).
**Solution**: Schema now uses `ALTER TABLE` statements at the end of the script to resolve circular dependencies.

### Import Errors
**Problem**: `ImportError: cannot import name 'JournalEntry'`.
**Solution**: Models have been restored to `apps/backend/apps/core/models/`. Ensure virtual environment is sourced.

---

## 🚀 Recent Milestones

### Database & Model Hardening (2026-02-27) ✅
- **Restored Models**: `InvoiceLine`, `JournalEntry`, `JournalLine`.
- **Django 6.0 Alignment**: `AppUser` updated with `password`, `is_staff`, `is_superuser`.
- **Schema Patches**: 11 versions of updates applied to `database_schema.sql`.
- **Circular Deps**: Resolved via `ALTER TABLE` statements.
- **Testing**: Workflow established for unmanaged model verification.

### Frontend-Backend Integration Remediation (2026-02-26) ✅
- **API Alignment**: 57 endpoints perfectly matched between FE and BE.
- **Workflow Endpoints**: Added `approve`, `void`, `pdf`, `send`, `send-invoicenow`.
- **Stubs**: Implemented Dashboard and Banking stubs.
