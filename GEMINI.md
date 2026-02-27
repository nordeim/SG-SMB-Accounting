# LedgerSG — Project Instructional Context

This document serves as the foundational instructional context for AI agents and developers interacting with the LedgerSG codebase. It summarizes the project's architecture, technologies, and development standards established as of February 2026.

## 🎯 Project Overview
**LedgerSG** is a production-grade, double-entry accounting platform purpose-built for Singapore Small and Medium Businesses (SMBs). Its core mission is to automate IRAS compliance (GST, InvoiceNow, BCRS) while delivering a neo-brutalist "Illuminated Carbon" user interface.

- **Frontend**: Next.js 16 (App Router) + Tailwind CSS 4.0 + Shadcn/Radix UI.
- **Backend**: Django 6.0.2 + Django REST Framework 3.16.1.
- **Database**: PostgreSQL 16 with 7 domain-specific schemas.
- **Compliance**: IRAS 2026 Ready (9% GST, BCRS deposits, PINT-SG XML, 5-year retention).

## 🏗 System Architecture

### 1. Data Layer (PostgreSQL)
- **SQL-First Schema**: All tables are defined in `database_schema.sql`. Models are unmanaged (`managed = False`).
- **Domain Separation**: 7 schemas (`core`, `coa`, `gst`, `journal`, `invoicing`, `banking`, `audit`).
- **Precision**: All monetary values use `NUMERIC(10,4)` storage and `ROUND_HALF_UP` rounding.
- **Multi-tenancy**: Row-Level Security (RLS) enforced via PostgreSQL session variables (`app.current_org_id`).

### 2. Backend Layer (Django)
- **Service Layer Pattern**: ALL business logic resides in `services/` modules using `@staticmethod`. Views are thin controllers.
- **Asynchronous Services**: PDF generation (WeasyPrint) and Email delivery (Celery) are live and verified.
- **Authentication**: JWT (Access 15m / Refresh 7d) with HttpOnly refresh cookies.
- **Models**: Inherit from `BaseModel`, `TenantModel`, or `ImmutableModel`.

### 3. Frontend Layer (Next.js)
- **UI Aesthetic**: "Illuminated Carbon" — Dark-first, high-contrast, typographically driven (WCAG AAA).
- **State Management**: TanStack Query (server state) and Zustand (UI state).
- **Logic**: Client-side GST preview logic (`gst-engine.ts`) must mirror backend `ComplianceEngine`.

## 🚀 Building and Running

### Prerequisites
- **Python**: 3.12+ (managed via virtual environment).
- **Node.js**: 20+ (npm).
- **PostgreSQL**: 16+ (with schemas initialized).

### Backend Setup
```bash
source /opt/venv/bin/activate
cd apps/backend
pip install -e ".[dev]"
# Initialize DB (Critical for unmanaged models)
export PGPASSWORD=ledgersg_secret_to_change
psql -h localhost -U ledgersg -d ledgersg_dev -f database_schema.sql
python manage.py runserver
```

### Frontend Setup
```bash
cd apps/web
npm install
npm run dev
```

### Testing Strategy
**Standard Django test runners fail on unmanaged models.** Use the manual workflow:
```bash
# Backend
export PGPASSWORD=ledgersg_secret_to_change
dropdb -h localhost -U ledgersg test_ledgersg_dev || true
createdb -h localhost -U ledgersg test_ledgersg_dev
psql -h localhost -U ledgersg -d test_ledgersg_dev -f database_schema.sql
pytest --reuse-db --no-migrations

# Frontend
cd apps/web && npm test
```

## 📐 Development Conventions

### 1. Monetary Precision
- **NEVER** use `float` or `parseFloat`.
- **Python**: Use `common.decimal_utils.money()` utility.
- **TypeScript**: Use `Decimal.js`.

### 2. Database Alignment
- LedgerSG is **SQL-First**. When updating models, you **MUST** update `database_schema.sql` manually. Django migrations are not used for unmanaged models.

---
*Last Hardened: 2026-02-27 — Version 1.2.0 — ~11,200 lines verified*
