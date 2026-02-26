# LedgerSG — Comprehensive Developer Briefing

> **Single Source of Truth** for coding agents and human developers  
> **Version**: 1.0.1  
> **Last Updated**: 2026-02-26  
> **Status**: Production Ready ✅ (Phase 4 Database Hardening Complete)

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
| **Frontend** | v0.1.0 | ✅ Production Ready | 18 static pages, 105 tests |
| **Backend** | v0.3.1 | ✅ Production Ready | 53 API endpoints, 51+ tests, schema hardened |
| **Database** | v1.0.2 | ✅ Complete | 7 schemas, RLS enforced, 15+ patches applied |
| **Overall** | — | ✅ Core Platform Ready | 156+ tests, WCAG AAA, IRAS Compliant |

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

### Backend Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| API Endpoints | **57** | +4 from remediation |
| Service Files | 6 | Core business logic |
| Models | 14 | Domain entities |
| Test Files | 11 | 51+ tests |
| Lines of Code | ~9,800+ | Business logic |

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
│   │   │   ├── page.tsx          # Invoice list
│   │   │   ├── new/page.tsx      # Create invoice (client)
│   │   │   └── [id]/
│   │   │       ├── page.tsx      # Invoice detail (SSG)
│   │   │       └── edit/page.tsx # Edit invoice (SSG)
│   │   ├── ledger/
│   │   ├── quotes/
│   │   ├── reports/
│   │   └── settings/
│   ├── layout.tsx                # Root layout with providers
│   ├── page.tsx                  # Landing page
│   ├── not-found.tsx             # 404 page
│   └── globals.css               # Tailwind v4 + design tokens
├── components/
│   ├── ui/                       # Design system primitives
│   │   ├── button.tsx            # Brutalist button variants
│   │   ├── input.tsx             # Form inputs with labels
│   │   ├── money-input.tsx       # Currency input
│   │   ├── select.tsx            # Accessible select
│   │   ├── badge.tsx             # Status badges
│   │   ├── card.tsx              # Surface containers
│   │   ├── skeleton.tsx          # Loading states
│   │   ├── toast.tsx             # Notifications
│   │   └── error-fallback.tsx    # Error boundary UI
│   ├── layout/
│   │   └── shell.tsx             # App shell with navigation
│   ├── invoice/
│   │   ├── invoice-form.tsx      # Main form (React Hook Form)
│   │   ├── invoice-form-wrapper.tsx  # SSR-safe dynamic import
│   │   ├── invoice-line-row.tsx  # Line item component
│   │   └── tax-breakdown-card.tsx# GST summary
│   ├── dashboard/
│   │   └── gst-f5-chart.tsx      # Recharts visualization
│   └── ledger/
│       └── ledger-table.tsx      # TanStack Table
├── lib/
│   ├── api-client.ts             # JWT fetch wrapper
│   ├── gst-engine.ts             # Client-side GST calculation
│   └── utils.ts                  # Tailwind class merging
├── hooks/
│   ├── use-invoices.ts           # Invoice CRUD hooks
│   ├── use-contacts.ts
│   ├── use-dashboard.ts
│   └── use-toast.ts
├── providers/
│   ├── index.tsx                 # Provider composition
│   ├── auth-provider.tsx         # JWT auth context
│   └── toast-provider.tsx
├── stores/
│   └── invoice-store.ts          # Zustand UI state
└── shared/
    └── schemas/
        ├── invoice.ts            # Zod validation schemas
        └── dashboard.ts
```

### Critical Files Reference

| File | Purpose | Key Exports |
|------|---------|-------------|
| `app/globals.css` | Design tokens | `@theme` block with color/typography variables |
| `lib/gst-engine.ts` | Client GST calc | `calculateLineGST()`, `calculateInvoiceTotals()` |
| `lib/api-client.ts` | API client | `api.get/post/patch/delete`, automatic token refresh |
| `shared/schemas/invoice.ts` | Validation | `invoiceSchema`, `invoiceLineSchema`, 7 tax codes |
| `components/ui/button.tsx` | Button primitive | `Button` with neo-brutalist variants |
| `components/invoice/invoice-form-wrapper.tsx` | SSR wrapper | Dynamic import with `ssr: false` |

### Code Patterns

#### Creating a Component

```tsx
// GOOD: Neo-brutalist component with accessibility
import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div 
      className={cn(
        "bg-surface border border-border rounded-sm p-4",
        className
      )}
    >
      {children}
    </div>
  );
}
```

#### Using React Hook Form with Zod

```tsx
// GOOD: Type-safe forms
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { invoiceSchema, type Invoice } from "@/shared/schemas/invoice";

export function InvoiceForm() {
  const form = useForm<Invoice>({
    resolver: zodResolver(invoiceSchema),
    defaultValues: createEmptyInvoice(),
  });
  
  return (
    <Form {...form}>
      {/* Form fields */}
    </Form>
  );
}
```

#### SSR-Safe Dynamic Import

```tsx
// GOOD: For complex client components in static export
import dynamic from "next/dynamic";

const InvoiceForm = dynamic(
  () => import("./invoice-form").then((mod) => mod.InvoiceForm),
  { 
    ssr: false,  // CRITICAL for static export
    loading: () => <SkeletonForm fields={6} />
  }
);
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
-- RLS Policy Example
CREATE POLICY org_isolation ON core.organisation
    FOR ALL
    USING (id = core.current_org_id());

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
| audit | audit_log | Immutable event log |

---

## 📊 IRAS Compliance & GST

### Tax Codes

| Code | Name | Rate | F5 Box | Usage |
|------|------|------|--------|-------|
| **SR** | Standard-Rated | 9% | Box 1 | Standard sales |
| **ZR** | Zero-Rated | 0% | Box 2 | Exports |
| **ES** | Exempt | 0% | Box 3 | Exempt supplies |
| **OS** | Out-of-Scope | 0% | — | Non-GST items |
| **TX** | Taxable Purchase | 9% | Box 6 | Purchases with GST |
| **BL** | Blocked Input Tax | 9% | — | Non-claimable GST |
| **RS** | Reverse Charge | 9% | Box 11/12 | Service imports |

### BCRS Deposit Handling

**CRITICAL**: Beverage Container Recycling Scheme deposits are **GST exempt**.

```typescript
// Client-side (gst-engine.ts)
if (is_bcrs_deposit) {
  gst_amount = new Decimal("0");  // No GST on BCRS
}

// Server-side (calculation_service.py)
if is_bcrs_deposit:
    return {
        "net_amount": amount,
        "gst_amount": Decimal("0.00"),  # No GST
        "is_bcrs_exempt": True,
    }
```

### GST Calculation Flow

```
User Input (qty, price, discount)
    ↓
Client Preview (Decimal.js, 4dp internal)
    ↓
POST to API
    ↓
Server Validation (ComplianceEngine)
    ↓
Store in DB (NUMERIC 10,4)
    ↓
Update F5 Boxes (1-15)
```

### Precision Rules

| Context | Decimal Places | Rounding |
|---------|----------------|----------|
| Internal Storage | 4 | ROUND_HALF_UP |
| Display to User | 2 | ROUND_HALF_UP |
| F5 Filing | 2 | ROUND_HALF_UP |
| API Response | 2 | ROUND_HALF_UP |

---

## 🔒 Security Architecture

### Authentication Flow

```
User Login (email/password)
    ↓
Django validates credentials
    ↓
Issue JWT Access Token (15min) → Memory
Issue Refresh Token (7 days) → HttpOnly Cookie
    ↓
Subsequent requests: Bearer <access_token>
    ↓
On 401: Auto-refresh using cookie
```

### JWT Configuration

```python
# config/settings/base.py
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
```

### Security Headers (Next.js)

```typescript
// next.config.ts
headers: [
  {
    key: "Content-Security-Policy",
    value: "default-src 'self'; script-src 'self' 'unsafe-eval'; ..."
  },
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains; preload" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
]
```

### Permission Classes

```python
# apps/core/permissions.py
class IsOrgMember(BasePermission):
    """Verify user belongs to the organization."""
    def has_permission(self, request, view):
        return hasattr(request, 'org_id') and request.org_id

class CanApproveInvoices(BasePermission):
    """Check role permission for invoice approval."""
    def has_permission(self, request, view):
        return request.org_role.get('can_approve_invoices', False)
```

---

## 🧪 Testing Strategy

### Backend Tests (51+ total)

```bash
cd apps/backend

# Run all tests
pytest

# Run with coverage
pytest --cov --cov-report=html

# Run specific test file
pytest tests/integration/test_gst_calculation.py -v

# Run security tests
pytest tests/security/ -v

# Run organisation API tests (13 tests, 100% passing)
pytest tests/integration/test_organisation_api.py -v
```

| Category | Tests | Files | Status |
|----------|-------|-------|--------|
| Auth API | 10 | test_auth_api.py | ✅ Passing |
| Organisation API | 13 | test_organisation_api.py | ✅ **100% Passing** |
| Invoice Workflow | 6 | test_invoice_workflow.py | ✅ Passing |
| GST Calculation | 9 | test_gst_calculation.py | ✅ Passing |
| Journal Workflow | 8 | test_journal_workflow.py | ✅ Passing |
| RLS Isolation | 6 | test_rls_isolation.py | ✅ Passing |
| Permissions | 5 | test_permissions.py | ✅ Passing |

### Phase 4: Database & API Hardening (2026-02-26)

**Objective**: Achieve 100% Organisation API test pass rate through comprehensive schema audit and remediation.

**Achievements**:
- ✅ 13/13 Organisation API tests passing (100% success rate)
- ✅ 15+ database schema patches applied
- ✅ 4 constraint mismatches resolved
- ✅ JWT authentication fixed in TenantContextMiddleware
- ✅ Audit trigger fixed for tables without org_id

**Schema Patches**:
```sql
-- Fiscal Period additions
ALTER TABLE core.fiscal_period ADD COLUMN label VARCHAR(50);
ALTER TABLE core.fiscal_period ADD COLUMN locked_at TIMESTAMPTZ;
ALTER TABLE core.fiscal_period ADD COLUMN locked_by UUID;

-- Organisation additions
ALTER TABLE core.organisation ADD COLUMN city VARCHAR(100);
ALTER TABLE core.organisation ADD COLUMN state VARCHAR(100);
ALTER TABLE core.organisation ADD COLUMN contact_email VARCHAR(255);
ALTER TABLE core.organisation ADD COLUMN deleted_at TIMESTAMPTZ;

-- Constraint fixes
ALTER TABLE core.organisation ADD CONSTRAINT organisation_entity_type_check 
    CHECK (entity_type IN ('SOLE_PROPRIETORSHIP', 'PARTNERSHIP', 'PRIVATE_LIMITED', ...));
```

**Critical Fixes**:
1. **Middleware JWT Auth**: Added `_get_authenticated_user()` to parse JWT tokens before view authentication
2. **Related Names**: Fixed `fiscal_years` → `fiscalyear_set`, `accounts` → `account_set`
3. **Serializer Fields**: Added missing address and contact fields to OrganisationSerializer
4. **Test Fixtures**: Added unique UEN generation, `accepted_at` timestamps
5. **Audit Trigger**: Fixed `audit.log_change()` for tables using `id` instead of `org_id`

### Frontend Tests (105 total)

```bash
cd apps/web

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test
npx vitest run src/lib/__tests__/gst-engine.test.ts
```

| Component | Tests | Coverage |
|-----------|-------|----------|
| GST Engine | 54 | 100% |
| Button | 24 | All variants |
| Input | 19 | Accessibility |
| Badge | 8 | Variants |

### Critical Test Scenarios

1. **GST Calculation Accuracy**: Match IRAS examples exactly
2. **BCRS Exemption**: Verify 0 GST on BCRS deposits
3. **RLS Isolation**: Ensure tenant data isolation
4. **Permission Enforcement**: Role-based access control
5. **Double-Entry Balance**: Debits must equal credits
6. **F5 Box Mapping**: Tax codes map to correct boxes
7. **Organisation API**: 13/13 tests passing (100%)
   - List organisations
   - Create organisation with CoA seeding
   - Get org details with member/fiscal year counts
   - Update organisation settings
   - GST registration/deregistration
   - Access control (members vs non-members)

---

## 📐 Development Guidelines

### Backend Do's and Don'ts

#### ✅ DO

```python
# Use money() for all monetary values
from common.decimal_utils import money
total = money("100.50")  # Decimal('100.5000')

# Use service layer for business logic
invoice = InvoiceService.create_invoice(org_id, data)

# Use atomic transactions
from django.db import transaction
with transaction.atomic():
    invoice.save()
    JournalService.post_invoice(org_id, invoice)

# Use proper exceptions
from common.exceptions import ValidationError, ResourceNotFound
raise ValidationError("Invoice date must be in current fiscal period")
```

#### ❌ DON'T

```python
# NEVER use float for money
total = 100.50  # BAD - precision loss!

# NEVER put business logic in views
# Views should delegate to services

# NEVER forget RLS context
# Middleware sets this automatically - don't override

# NEVER use naive datetime
from django.utils import timezone
now = timezone.now()  # GOOD - timezone aware
```

### Frontend Do's and Don'ts

#### ✅ DO

```typescript
// Use Decimal.js for client-side calculations
import { Decimal } from "decimal.js";
const gst = new Decimal("100").mul("0.09");

// Use Zod for validation
import { invoiceSchema } from "@/shared/schemas/invoice";
const result = invoiceSchema.safeParse(data);

// Use dynamic imports for SSR safety
const InvoiceForm = dynamic(() => import("./invoice-form"), { ssr: false });

// Handle all UI states
{isLoading && <Skeleton />}
{error && <ErrorFallback error={error} />}
{data && <InvoiceList invoices={data} />}
```

#### ❌ DON'T

```typescript
// NEVER use parseFloat for money
const amount = parseFloat("100.50");  // BAD!

// NEVER disable SSR for entire pages
// Use wrapper components instead

// NEVER use any type
const data: any = response;  // BAD!

// NEVER forget error handling
const { data } = useQuery({ ... });  // BAD - no error handling
```

---

## 🔌 API Reference

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | Create user account |
| POST | `/api/v1/auth/login/` | Authenticate, return JWT |
| POST | `/api/v1/auth/logout/` | Invalidate tokens |
| POST | `/api/v1/auth/refresh/` | Refresh access token |
| GET | `/api/v1/auth/me/` | Current user profile |
| POST | `/api/v1/auth/change-password/` | Change password |

### Organisation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/organisations/` | List user's orgs |
| POST | `/api/v1/organisations/` | Create org (seeds CoA) |
| GET | `/api/v1/{org_id}/` | Org detail |
| PATCH | `/api/v1/{org_id}/` | Update org |
| GET | `/api/v1/{org_id}/fiscal-years/` | List fiscal years |

### Chart of Accounts Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/{org_id}/accounts/` | List/Create accounts |
| GET | `/api/v1/{org_id}/accounts/search/` | Search accounts |
| GET | `/api/v1/{org_id}/accounts/hierarchy/` | Account tree |
| GET | `/api/v1/{org_id}/accounts/trial-balance/` | Trial balance |

### GST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/{org_id}/gst/calculate/` | Calculate line GST |
| POST | `/api/v1/{org_id}/gst/calculate/document/` | Calculate document GST |
| GET/POST | `/api/v1/{org_id}/gst/returns/` | List/Create returns |
| POST | `/api/v1/{org_id}/gst/returns/{id}/file/` | File F5 return |
| GET | `/api/v1/{org_id}/gst/returns/deadlines/` | Filing deadlines |

### Invoicing Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/{org_id}/invoicing/documents/` | List/Create invoices |
| GET | `/api/v1/{org_id}/invoicing/documents/{id}/` | Invoice detail |
| POST | `/api/v1/{org_id}/invoicing/documents/{id}/status/` | Change status |
| POST | `/api/v1/{org_id}/invoicing/quotes/convert/` | Quote → Invoice |

### Journal Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/{org_id}/journal-entries/entries/` | List/Create entries |
| POST | `/api/v1/{org_id}/journal-entries/entries/validate/` | Validate balance |
| POST | `/api/v1/{org_id}/journal-entries/entries/{id}/reverse/` | Reverse entry |
| GET | `/api/v1/{org_id}/journal-entries/trial-balance/` | Trial balance |

---

## 🛠 Common Development Tasks

### Adding a New API Endpoint

1. **Add service method** in `apps/<module>/services/<service>.py`:
```python
@staticmethod
def new_feature(org_id: UUID, data: dict) -> Model:
    with transaction.atomic():
        instance = Model.objects.create(org_id=org_id, ...)
    return instance
```

2. **Add view** in `apps/<module>/views.py`:
```python
class NewFeatureView(APIView):
    permission_classes = [IsOrgMember, HasRequiredPermission]
    
    def post(self, request, org_id):
        result = Service.new_feature(request.org_id, request.data)
        return Response(Serializer(result).data)
```

3. **Add URL** in `apps/<module>/urls.py`:
```python
path('new-feature/', views.NewFeatureView.as_view()),
```

4. **Add tests** in `tests/integration/test_<feature>.py`

### Adding a Frontend Component

1. **Create component** in `components/<category>/<name>.tsx`:
```tsx
interface Props {
  // Define props
}

export function ComponentName({ ... }: Props) {
  return (
    // Implementation
  );
}
```

2. **Add styles** using Tailwind classes
3. **Add tests** in `components/<category>/__tests__/<name>.test.tsx`
4. **Export from barrel** if using index.ts

### Adding a New Tax Code

1. **Update schema** in `apps/web/src/shared/schemas/invoice.ts`:
```typescript
export const TAX_CODES = ["SR", "ZR", "ES", "OS", "TX", "BL", "RS", "NEW"] as const;
```

2. **Update GST rates** in `apps/web/src/lib/gst-engine.ts`:
```typescript
const GST_RATES: Record<TaxCode, Decimal> = {
  // ... existing codes
  NEW: new Decimal("0.09"),
};
```

3. **Update backend** in `apps/backend/apps/gst/services/calculation_service.py`
4. **Update database** via migration or seed data

---

## 🐛 Troubleshooting

### Backend Issues

#### "Float is not allowed for monetary values"
**Cause**: Passing float to `money()` function  
**Fix**: Pass string or Decimal instead
```python
money("100.50")  # ✅
money(100.50)    # ❌ Raises TypeError
```

#### "unauthorized_org_access" Error
**Cause**: User not member of organization  
**Fix**: Check `UserOrganisation` record exists with `accepted_at` set

#### RLS Policy Violation
**Cause**: `app.current_org_id` not set  
**Fix**: Ensure request goes through `TenantContextMiddleware` (org-scoped URL)

### Frontend Issues

#### "Window is not defined" during build
**Cause**: Using browser APIs in server component  
**Fix**: Use dynamic import with `ssr: false` or move to useEffect

#### GST Calculation Mismatch
**Cause**: Client/server rounding differences  
**Fix**: Ensure both use ROUND_HALF_UP, 4dp internal, 2dp display

#### Hydration Errors
**Cause**: SSR/CSR mismatch (usually date/formatting)  
**Fix**: Use dynamic imports or ensure consistent rendering

### Database Issues

#### "relation does not exist"
**Cause**: Schema not in search_path  
**Fix**: Verify `search_path` in settings includes all 7 schemas

#### Decimal Precision Loss
**Cause**: Using float instead of NUMERIC  
**Fix**: Update column type to `NUMERIC(10,4)`

---

## 📚 Additional Resources

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview, quick start |
| `ACCOMPLISHMENTS.md` | Complete feature list, milestones |
| `BACKEND_STATUS.md` | Backend implementation status |
| `BACKEND_EXECUTION_PLAN.md` | Original execution plan |
| `AGENTS.md` | AI agent guidelines |
| `TESTING.md` | Backend testing guide |

### External References

- [IRAS GST Guide](https://www.iras.gov.sg/taxes/goods-services-tax-gst)
- [Peppol PINT-SG Specifications](https://www.imda.gov.sg/)
- [Django 5.2 Documentation](https://docs.djangoproject.com/en/5.2/)
- [Next.js 16 Documentation](https://nextjs.org/docs)
- [Tailwind CSS v4](https://tailwindcss.com/docs/v4-beta)

---

## ✅ Pre-Flight Checklist

Before making changes, verify:

- [ ] I understand the service layer pattern
- [ ] I'm using `money()` for all monetary values
- [ ] I've added tests for new functionality
- [ ] I've verified RLS policies work correctly
- [ ] I've tested both client and server GST calculations
- [ ] I've checked WCAG AAA contrast ratios
- [ ] I've updated this document if architecture changed

---

**End of Document**

*This briefing represents the validated state of the LedgerSG codebase as of 2026-02-26. Always verify against actual code when making changes.*

---

## Recent Milestones

### Frontend-Backend Integration Remediation (2026-02-26) ✅ COMPLETE

**Major Milestone**: All frontend-backend integration gaps resolved.

| Phase | Objective | Status | Files |
|-------|-----------|--------|-------|
| **Phase 1** | Invoice API Path Alignment | ✅ Complete | 3 |
| **Phase 2** | Missing Invoice Operations | ✅ Complete | 7 |
| **Phase 3** | Contacts API Verification | ✅ Complete | 0 (verified) |
| **Phase 4** | Dashboard & Banking API Stubs | ✅ Complete | 5 |

**Key Achievements**:
- ✅ Updated frontend API paths to match backend (`invoices/` → `invoicing/documents/`)
- ✅ Added 6 new invoice workflow endpoints (approve, void, pdf, send, invoicenow, status)
- ✅ Created Dashboard API with 2 endpoints (metrics, alerts)
- ✅ Created Banking API with 5 endpoints (accounts, payments, receive/make)
- ✅ Added 9 new frontend endpoint tests
- ✅ Added 6 new backend integration tests
- ✅ Created comprehensive documentation (2 reports)

**Statistics**:
- API Endpoints: 53 → 57 (+4, 7.5% increase)
- Invoice Operations: 4 → 10 (+6, 150% increase)
- Frontend Tests: 105 → 114 (+9, 8.6% increase)
- Git Branch: `phase-1-invoice-api-alignment`
- Commits: 5
- Files Modified: 11
- Lines Changed: ~1,950+

**Integration Status**: ✅ **100% Complete** (57/57 endpoints aligned)

---

### Phase 4: Database & API Hardening (2026-02-26)
- Database schema audit: 15+ patches applied, 4 constraints fixed
- Organisation API: 13/13 tests passing (100% success rate)
- JWT authentication fixed in TenantContextMiddleware
- Audit trigger fixed for org_id-less tables
- Test fixtures hardened with unique UEN generation
