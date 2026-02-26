# LedgerSG — Agent & Developer Briefing

> **Single Source of Truth** for coding agents and human developers  
> **Version**: 1.0.2  
> **Last Updated**: 2026-02-26  
> **Status**: Production Ready ✅ (Architecture Validated)

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
| **Frontend** | v0.1.0 | ✅ Production Ready | 18 static pages, 105 tests |
| **Backend** | v0.3.1 | ✅ Production Ready | 53 API endpoints, schema hardened |
| **Database** | v1.0.2 | ✅ Complete | 7 schemas, RLS enforced, 28 tables |
| **Overall** | — | ✅ Core Platform Ready | WCAG AAA, IRAS Compliant |

### Regulatory Foundation

| Regulation | Implementation |
|------------|----------------|
| **InvoiceNow (Peppol)** | PINT-SG XML generation ready |
| **GST 9% Rate** | Configurable tax engine |
| **GST F5 Returns** | Auto-computed from journal data |
| **BCRS Deposit** | GST-exempt liability accounting |
| **5-Year Retention** | Immutable audit logs |

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

### Module Dependency Graph

```
core (Organisation, Users, Auth)
    ├── coa (Chart of Accounts)
    ├── gst (Tax Codes, F5 Returns)
    ├── invoicing (Documents, Contacts)
    │       └── peppol (InvoiceNow) [Architecture Ready]
    └── journal (General Ledger)
            └── reporting (P&L, BS, TB) [Architecture Ready]
```

---

## 🔧 Backend Deep Dive

### Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Framework | Django | 5.2 LTS | Web framework |
| API | Django REST Framework | 3.15+ | REST endpoints |
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
| **JWT Auth** | Access 15min / Refresh 7d | HttpOnly cookies for refresh tokens |

### Directory Structure

```
apps/backend/
├── apps/
│   ├── core/              # Auth, Organisation, Users, Fiscal
│   │   ├── models/        # Organisation, AppUser, Role, etc.
│   │   ├── services/      # auth_service.py, organisation_service.py
│   │   ├── views/         # auth.py, organisations.py
│   │   └── serializers/   # auth.py, organisation.py
│   ├── coa/               # Chart of Accounts (8 endpoints)
│   │   ├── services.py    # AccountService (500 lines)
│   │   ├── views.py       # 8 API endpoints
│   │   └── serializers.py
│   ├── gst/               # GST Module (11 endpoints)
│   │   ├── services/      # calculation_service.py, return_service.py
│   │   ├── views.py
│   │   └── serializers.py
│   ├── invoicing/         # Invoicing (12 endpoints)
│   │   ├── services/      # contact_service.py, document_service.py
│   │   ├── views.py
│   │   └── serializers.py
│   ├── journal/           # Journal Entry (8 endpoints)
│   │   ├── services/      # journal_service.py (591 lines)
│   │   ├── views.py
│   │   └── serializers.py
│   ├── banking/           # [Architecture Ready - Stubs Only]
│   └── peppol/            # [Architecture Ready - Stubs Only]
├── common/                # Shared utilities
│   ├── decimal_utils.py   # CRITICAL: Money precision utilities
│   ├── models.py          # BaseModel, TenantModel
│   ├── middleware/        # tenant_context.py (RLS), audit_context.py
│   ├── exceptions.py      # Custom exception hierarchy
│   └── db/                # Custom PostgreSQL backend
├── config/                # Django configuration
│   ├── settings/          # base.py, development.py, production.py
│   ├── urls.py            # URL routing
│   └── celery.py          # Celery configuration
└── tests/                 # Test suite
    ├── integration/       # 40 API tests
    └── security/          # 11 security tests
```

### Critical Files Reference

| File | Purpose | Key Functions/Classes |
|------|---------|----------------------|
| `common/decimal_utils.py` | Money precision | `money()`, `sum_money()`, `Money` class - REJECTS floats |
| `common/middleware/tenant_context.py` | RLS enforcement | `TenantContextMiddleware` - Sets `app.current_org_id` |
| `config/settings/base.py` | Core settings | `ATOMIC_REQUESTS`, JWT config, schema search_path |
| `apps/core/models/organisation.py` | Tenant root | `Organisation` model - GST settings, fiscal config |
| `apps/gst/services/calculation_service.py` | GST engine | `GSTCalculationService.calculate_line_gst()` |
| `apps/journal/services/journal_service.py` | Double-entry | `JournalService.create_entry()`, `post_invoice()` |

### Code Patterns

#### Creating a Service Method

```python
# GOOD: Business logic in service
from common.decimal_utils import money, sum_money
from common.exceptions import ValidationError, ResourceNotFound

class InvoiceService:
    @staticmethod
    def create_invoice(org_id: UUID, data: dict) -> InvoiceDocument:
        """Create invoice with validation and GST calculation."""
        # Validate using money() - rejects floats
        total = money(data['total'])  # Decimal('100.0000')
        
        # Atomic transaction ensures RLS consistency
        with transaction.atomic():
            invoice = InvoiceDocument.objects.create(
                org_id=org_id,
                total=total,
                # ...
            )
        return invoice
```

#### Creating an API Endpoint

```python
# GOOD: Thin view delegating to service
from rest_framework.views import APIView
from apps.invoicing.services import InvoiceService

class InvoiceCreateView(APIView):
    permission_classes = [IsOrgMember, CanCreateInvoices]
    
    def post(self, request, org_id):
        # org_id injected by TenantContextMiddleware
        invoice = InvoiceService.create_invoice(
            org_id=request.org_id,
            data=request.data
        )
        return Response(InvoiceSerializer(invoice).data)
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
| Forms | React Hook Form + Zod | v7 + v4 | Type-safe validation |
| Decimal | decimal.js | v10.6 | Client-side GST preview |
| Charts | Recharts | v3.7 | GST F5 visualization |
| Tables | TanStack Table | v8.21 | Ledger table |

### Design System: "Illuminated Carbon"

#### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-void` | `#050505` | Deep black canvas (background) |
| `--color-carbon` | `#121212` | Elevated surfaces |
| `--color-surface` | `#1A1A1A` | Cards, panels |
| `--color-border` | `#2A2A2A` | Subtle borders |
| `--color-accent-primary` | `#00E585` | Electric green (actions, money) |
| `--color-accent-secondary` | `#D4A373` | Warm bronze (alerts, warnings) |
| `--color-alert` | `#FF3333` | Error states |
| `--color-text-primary` | `#FFFFFF` | Primary text |
| `--color-text-secondary` | `#A0A0A0` | Secondary text |

#### Typography

| Font | Usage |
|------|-------|
| **Space Grotesk** | Display headings |
| **Inter** | Body text |
| **JetBrains Mono** | Financial data (tabular-nums, slashed-zero) |

#### Design Principles

1. **Brutalist Forms**: Square corners (`rounded-sm`), 1px borders
2. **Intentional Asymmetry**: Reject generic grid layouts
3. **High Contrast**: WCAG AAA compliant (7:1 ratio minimum)
4. **Financial Data Integrity**: Monospace, tabular numbers, slashed zeros

### Directory Structure

```
apps/web/src/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Authentication route group
│   │   └── login/
│   ├── (dashboard)/              # Main app route group
│   │   ├── dashboard/
│   │   ├── invoices/
│   │   ├── ledger/
│   │   ├── quotes/
│   │   ├── reports/
│   │   └── settings/
│   ├── layout.tsx                # Root layout with providers
│   ├── page.tsx                  # Landing page
│   └── globals.css               # Tailwind v4 + design tokens
├── components/
│   ├── ui/                       # Design system primitives
│   ├── invoice/                  # Invoice domain components
│   └── dashboard/                # Dashboard components
├── lib/
│   ├── api-client.ts             # JWT fetch wrapper
│   ├── gst-engine.ts             # Client-side GST calculation
│   └── utils.ts                  # Tailwind class merging
├── hooks/                        # TanStack Query hooks
├── providers/                    # React context providers
├── stores/                       # Zustand stores
└── shared/
    └── schemas/                  # Zod validation schemas
```

---

## 🗄 Database Architecture

### PostgreSQL 16 Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| **Schemas** | 7 (core, coa, gst, journal, invoicing, banking, audit) | Domain separation |
| **Money Precision** | `NUMERIC(10,4)` | 4 decimal places for all amounts |
| **RLS** | Session variable `app.current_org_id` | Multi-tenant isolation |
| **Primary Keys** | UUID (`gen_random_uuid()`) | Distributed-safe |
| **Extensions** | `pg_trgm`, `btree_gist`, `pgcrypto` | Search, constraints, crypto |

### Schema Overview

```sql
-- Core: Organisation, Users, Roles, Fiscal Periods
CREATE SCHEMA core;

-- COA: Chart of Accounts
CREATE SCHEMA coa;

-- GST: Tax codes, rates, F5 returns
CREATE SCHEMA gst;

-- Journal: Immutable double-entry ledger
CREATE SCHEMA journal;

-- Invoicing: Contacts, documents, lines
CREATE SCHEMA invoicing;

-- Banking: Bank accounts, payments
CREATE SCHEMA banking;

-- Audit: Immutable event log
CREATE SCHEMA audit;
```

### Row-Level Security (RLS)

**CRITICAL**: All queries must include org_id filter or rely on RLS session variable.

```sql
-- Django middleware sets this per request:
SET LOCAL app.current_org_id = 'org-uuid-here';
```

### Key Tables

| Schema | Table | Purpose |
|--------|-------|---------|
| core | organisation | Tenant root |
| core | app_user | Custom user (email-based) |
| core | role | RBAC role definitions |
| core | fiscal_year | Fiscal year management |
| core | fiscal_period | Monthly periods |
| coa | account | Chart of accounts |
| gst | tax_code | GST tax codes (SR, ZR, ES, etc.) |
| gst | gst_return | F5 filing tracking |
| journal | journal_entry | Double-entry headers |
| journal | journal_line | Debit/credit lines |
| invoicing | contact | Customers/suppliers |
| invoicing | invoice_document | Invoices, quotes, notes |
| invoicing | invoice_line | Line items |
| audit | event_log | Immutable event log |

---

## 📊 IRAS Compliance & GST

### Tax Codes

| Code | Name | Rate | F5 Box | Usage |
|------|------|------|--------|-------|
| **SR** | Standard-Rated | 9% | Box 1 | Standard sales |
| **ZR** | Zero-Rated | 0% | Box 2 | Exports |
| **ES** | Exempt | 0% | Box 3 | Exempt supplies |
| **OS** | Out-of-Scope | 0% | — | Non-Singapore supplies |
| **TX** | Taxable Purchase | 9% | Box 6 | Purchases with GST |
| **BL** | BCRS Deposit | 0% | — | Beverage container deposits |
| **RS** | Reverse Charge | 9% | Box 7 | Reverse charge supplies |

### Key Features

- **9% Standard Rate**: Singapore's current GST rate
- **BCRS Exemption**: Deposits on pre-packaged drinks are GST-exempt
- **GST Fraction**: 9/109 for extracting GST from inclusive amounts
- **4dp Internal, 2dp Display**: Precision per IRAS requirements
- **ROUND_HALF_UP**: Rounding mode for all GST calculations

---

## 🔒 Security Architecture

| Layer | Implementation | Status |
|-------|----------------|--------|
| JWT Authentication | Access token (15min) + HttpOnly refresh cookie (7d) | ✅ |
| RLS (Row-Level Security) | PostgreSQL session variables | ✅ |
| CSRF Protection | Django CSRF middleware | ✅ |
| Password Hashing | Django's Argon2 default | ✅ |
| Rate Limiting | 20/min anon, 100/min user | ✅ |
| Input Validation | Serializer-based | ✅ |

---

## 🧪 Testing Strategy

### Backend Tests

```bash
cd apps/backend

# Run all API tests
pytest tests/test_api_endpoints.py -v

# Run specific test class
pytest tests/test_api_endpoints.py::TestAuthenticationAPI -v

# Run with coverage
pytest tests/test_api_endpoints.py --cov=apps --cov-report=html
```

### Frontend Tests

```bash
cd apps/web

# Run all tests
npm test

# Run GST engine tests
npm test -- gst-engine

# Run with coverage
npm test -- --coverage
```

### Test Structure

| Category | Files | Purpose |
|----------|-------|---------|
| API Integration | 40+ tests | Endpoint validation |
| Security | 11 tests | RLS, permissions |
| GST Calculations | 54 tests | IRAS compliance |
| Component Tests | 51 tests | UI validation |

---

## ⚙️ Development Guidelines

### Prerequisites

1. **PostgreSQL 16+** with the schema loaded from `database_schema.sql`
2. **Python 3.12+** with virtual environment
3. **Node.js 20+** for frontend

### Setup

```bash
# Backend
cd apps/backend
python -m venv venv
source venv/bin/activate  # or . venv/bin/activate.fish
pip install -r requirements.txt

# Load database schema (one-time)
psql -h localhost -U ledgersg -d ledgersg_dev -f database_schema.sql

# Frontend
cd apps/web
npm install
```

### Running the Application

```bash
# Backend (development)
cd apps/backend
python manage.py runserver

# Frontend (development)
cd apps/web
npm run dev
```

### Code Standards

- **Decimal Safety**: NEVER use float for money. Use `common.decimal_utils.money()`
- **Service Layer**: ALL business logic in services/, NOT in views
- **Unmanaged Models**: Don't run migrations - schema is SQL-managed
- **Thin Views**: Views handle HTTP only; delegate to services

---

## 🔧 Troubleshooting

### Database Issues

**Problem**: Tests fail with `relation does not exist`

**Solution**: Load the schema first:
```bash
psql -h localhost -U ledgersg -d ledgersg_dev -f database_schema.sql
```

### Import Errors

**Problem**: `ModuleNotFoundError`

**Solution**: Ensure virtual environment is activated:
```bash
source venv/bin/activate
```

### JWT Issues

**Problem**: 401 Unauthorized

**Solution**: 
1. Check token expiration (15min access)
2. Verify `Authorization: Bearer <token>` header
3. Ensure refresh cookie is HttpOnly

### RLS Issues

**Problem**: 403 Forbidden on org-scoped endpoints

**Solution**: 
1. Ensure TenantContextMiddleware is in MIDDLEWARE
2. Verify org_id is in URL path: `/api/v1/{org_id}/...`
3. Check user belongs to organisation

---

## 📚 Key References

- **CLAUDE.md**: Comprehensive developer briefing
- **README.md**: Project overview and quick start
- **ACCOMPLISHMENTS.md**: Development milestones
- **database-schema-design.md**: Full SQL schema documentation
- **BACKEND_REMEDIATION_PLAN.md**: Known issues and fixes

---

*This briefing is the single source of truth for all developers and coding agents working on LedgerSG.*