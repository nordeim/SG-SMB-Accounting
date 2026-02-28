# LedgerSG — Agent & Developer Briefing

> **Single Source of Truth** for coding agents and human developers  
> **Version**: 1.3.0  
> **Last Updated**: 2026-02-28  
> **Status**: Production Ready ✅ (SSR & Hydration Fixed)

---

## 📋 Table of Contents

1. [Executive Summary](#-executive-summary)
2. [Project Architecture](#-project-architecture)
3. [Backend Deep Dive](#-backend-deep-dive)
4. [Frontend Deep Dive](#-frontend-deep-dive)
5. [Database Architecture](#-database-architecture)
6. [IRAS Compliance \& GST](#-iras-compliance--gst)
7. [Security Architecture](#-security-architecture)
8. [Testing Strategy](#-testing-strategy)
9. [Development Guidelines](#-development-guidelines)
10. [Common Development Tasks](#-common-development-tasks)
11. [Troubleshooting](#-troubleshooting)

---

## 🎯 Executive Summary

**LedgerSG** is a production-grade, double-entry accounting platform purpose-built for Singapore SMBs. It transforms IRAS compliance from a burden into a seamless, automated experience while delivering a distinctive "Illuminated Carbon" neo-brutalist user interface.

### Current Status

| Component | Version | Status | Key Metrics |
|-----------|---------|--------|-------------|
| **Frontend** | v0.1.0 | ✅ Production Ready | 18 static pages, 114 tests |
| **Backend** | v0.3.1 | ✅ Production Ready | **57 API endpoints**, 22 models aligned |
| **Database** | v1.0.2 | ✅ Complete | 7 schemas, RLS enforced, 28 tables |
| **Integration** | v0.4.0 | ✅ Complete | All API paths aligned, Docker live |
| **Testing** | — | ✅ 52+ Passing | Backend tests SQL-compliant |
| **Overall** | — | ✅ **Platform Ready** | **158+ tests**, WCAG AAA, IRAS Compliant |

### Recent Milestone: Django Model Remediation ✅
**Date**: 2026-02-27  
**Status**: 22 models aligned with SQL schema

| Fix | Impact |
|-----|--------|
| **TaxCode Model** | Removed invalid fields (`name`, `is_gst_charged`, `box_mapping`), added IRAS F5 box mappings |
| **InvoiceDocument** | Added 28 fields (`sequence_number`, `contact_snapshot`, `created_by`, base currency fields) |
| **Organisation** | GST scheme alignment with SQL schema |
| **Test Fixtures** | Updated `conftest.py` for SQL constraint compliance |

### Recent Milestone: Backend Test Fixes ✅
**Date**: 2026-02-27  
**Status**: 52+ tests passing

| Fix | Impact |
|-----|--------|
| **conftest.py** | Fixed `tax_code_data` with `description`, `is_input`, `is_output`, `is_claimable` |
| **Contact Fixture** | Added required `contact_type` field |
| **GSTReturn Fixture** | Aligned with model field structure |
| **SQL Compliance** | All fixtures comply with database constraints |

### Recent Milestone: Frontend Startup & Docker ✅
**Date**: 2026-02-27  
**Status**: Live frontend-backend integration

| Fix | Impact |
|-----|--------|
| **next.config.ts** | Dual-mode config (static export + standalone server) |
| **package.json** | Added `start:server` script for standalone mode |
| **.env.local** | API URL configuration for development |
| **Dockerfile** | Multi-service container with live integration |
| **CORS** | Configured for localhost:3000 ↔ localhost:8000 |

### Recent Milestone: Frontend SSR & Hydration Fix ✅
**Date**: 2026-02-28  
**Status**: Production Ready - "Loading..." stuck state resolved

| Fix | Impact |
|-----|--------|
| **Dashboard Server Component** | Converted from Client to Server Component for immediate render |
| **Static Files Auto-Copy** | Build script now copies `.next/static` to standalone folder |
| **Hydration Mismatch Fix** | Removed "Loading..." early return from shell.tsx |
| **New Files** | `dashboard-actions.tsx`, `gst-chart-wrapper.tsx` for client interactivity |

**Key Insight**: Next.js standalone build requires manual static file copy. Build script now handles this automatically.

### Recent Milestone: PDF & Email Services ✅
**Date**: 2026-02-27  
**Status**: Document generation and delivery live

| Service | Implementation |
|---------|----------------|
| **PDF Generation** | WeasyPrint with IRAS-compliant templates |
| **Email Delivery** | Asynchronous Celery tasks with PDF attachments |
| **Verification** | Integration tests verified binary stream and task dispatch |

### Milestone: Database & Model Hardening ✅
**Date**: 2026-02-27  
**Status**: Models restored, Schema Aligned

| Fix | Impact |
|-----|--------|
| **Missing Models** | `InvoiceLine`, `JournalEntry`, `JournalLine`, `GSTReturn` restored |
| **Auth Alignment** | `AppUser` aligned with Django 6.0 standard fields |
| **Circular Deps** | Resolved circular foreign keys in SQL via `ALTER TABLE` |
| **Testing** | Workflow established for unmanaged model verification |

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

### Design Principles

| Principle | Implementation | Critical Notes |
|-----------|----------------|----------------|
| **Unmanaged Models** | `managed = False` | Schema is DDL-managed via SQL. Models map to existing tables. |
| **Service Layer** | `services/` modules | Views are thin controllers. ALL business logic lives in services. |
| **RLS Security** | PostgreSQL session variables | `SET LOCAL app.current_org_id = 'uuid'` per transaction |
| **Decimal Precision** | `NUMERIC(10,4)` | NEVER use float for money. Use `common.decimal_utils.money()` |
| **Atomic Requests** | `ATOMIC_REQUESTS: True` | Every view runs in single transaction for RLS consistency |

---

## 🧪 Testing Strategy

### Backend Tests (Unmanaged Database Workflow)

Since LedgerSG uses unmanaged models, standard Django test runners will fail to create the schema. Follow this established workflow:

```bash
# 1. Manually initialize the test database
export PGPASSWORD=ledgersg_secret_to_change
dropdb -h localhost -U ledgersg test_ledgersg_dev || true
createdb -h localhost -U ledgersg test_ledgersg_dev
psql -h localhost -U ledgersg -d test_ledgersg_dev -f database_schema.sql

# 2. Run tests with reuse flags
source /opt/venv/bin/activate
cd apps/backend
pytest --reuse-db --no-migrations
```

---

## 🔧 Troubleshooting

### Unmanaged Models & Testing
**Problem**: Tests fail with `relation "core.app_user" does not exist`.  
**Cause**: `pytest-django` skips migrations for unmanaged models, resulting in an empty test database.  
**Solution**: See the manual test database initialization workflow in [Testing Strategy](#-testing-strategy).

### Database Schema Mismatches
**Problem**: `ProgrammingError: column "updated_at" of relation "role" does not exist`.  
**Cause**: The SQL schema and Django models have drifted.  
**Solution**: Update `database_schema.sql` to include the missing fields and re-initialize both `ledgersg_dev` and `test_ledgersg_dev`.

### SQL Circular Dependencies
**Problem**: Database initialization fails when creating tables with foreign keys to each other.  
**Solution**: Decouple creation order. Create tables with simple columns first, then use `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY` at the end of the script for circular references (e.g., `organisation` <-> `app_user`).

### TaxCode Constraint Violations
**Problem**: `check_tax_code_input_output` constraint fails during fixture creation.  
**Cause**: SQL requires `is_input=TRUE OR is_output=TRUE OR code='NA'`.  
**Solution**: Ensure all TaxCode fixtures set at least one of `is_input` or `is_output` to `True` (except for code='NA').

### Frontend API Connection
**Problem**: Frontend shows "API Error" or cannot fetch data.  
**Cause**: CORS not configured or `NEXT_PUBLIC_API_URL` incorrect.  
**Solution**: Verify `.env.local` has correct API URL and backend CORS allows frontend origin.

### Docker Frontend Standalone
**Problem**: Frontend in Docker serves static files instead of Next.js app.  
**Cause**: `output: 'export'` mode doesn't support API routes.  
**Solution**: Use `NEXT_OUTPUT_MODE=standalone` and run `node .next/standalone/server.js`.

### Frontend "Loading..." Stuck State
**Problem**: Dashboard shows "Loading..." indefinitely.  
**Cause**: Missing static JS files in standalone build OR hydration mismatch.  
**Solution**:
1. Verify static files: `ls .next/standalone/.next/static/chunks/`
2. Rebuild: `npm run build:server` (now auto-copies static files)
3. Check browser console for hydration errors

### 404 Errors for JS/CSS Chunks
**Problem**: Browser shows 404 for `/_next/static/chunks/*.js`.  
**Cause**: Static files not copied to standalone folder.  
**Solution**: Build script updated to auto-copy. Manual fix: `cp -r .next/static .next/standalone/.next/`

### Hydration Mismatch Errors
**Problem**: Console shows "Text content does not match server-rendered HTML".  
**Cause**: Component renders differently on server vs client (e.g., `useEffect` with early return).  
**Solution**: Convert to Server Component or ensure identical initial render on both environments.

---

### Recent Milestone: Frontend SSR & Hydration Fix ✅
**Date**: 2026-02-28  
**Status**: Production Ready - Dashboard renders immediately without "Loading..." stuck state

| Fix | Impact |
|-----|--------|
| **Dashboard Server Component** | Converted from Client to Server Component for immediate render |
| **Static Files Auto-Copy** | Build script now copies `.next/static` to standalone folder automatically |
| **Hydration Mismatch Fix** | Removed "Loading..." early return from shell.tsx |
| **Loading.tsx Disabled** | Moved to loading.tsx.bak to prevent skeleton flash |
| **ClientOnly Component** | Now renders children immediately without skeleton fallback |

---

## 🚀 Recommended Next Steps

### Immediate (High Priority)
1. **Testing**: Verify all 18 pages render correctly without hydration errors
2. **Dashboard Real Data**: Replace mock data with actual API calls to backend
3. **Error Tracking**: Add Sentry or similar for client-side error monitoring

### Short-term (Medium Priority)
4. **Banking Module**: Replace placeholder views in `banking/views.py` with actual bank reconciliation logic
5. **CI/CD Pipeline**: Automate the manual database initialization workflow in GitHub Actions
6. **Performance**: Implement code splitting for heavy components

### Long-term (Low Priority)
7. **Compliance**: Finalize InvoiceNow/Peppol transmission logic (XML generation is architecture-ready)
8. **Documentation**: Create component usage guidelines (Server vs Client Components)
