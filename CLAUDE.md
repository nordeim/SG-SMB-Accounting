# LedgerSG — Comprehensive Developer Briefing

> **Single Source of Truth** for coding agents and human developers  
> **Version**: 1.2.0  
> **Last Updated**: 2026-02-27  
> **Status**: Production Ready ✅ (PDF & Email Services Live)

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
| **Overall** | — | ✅ Platform Ready | 158+ tests, WCAG AAA, IRAS Compliant |

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
| API Endpoints | **57** | 100% Path Alignment |
| Service Files | 6 | Core business logic |
| Models | **18** | Aligned with SQL schema |
| Test Files | 11 | 158+ total tests |
| Lines of Code | **~11,200+** | Logic & Templates |

### Directory Structure

```
apps/backend/
├── apps/
│   ├── core/              # Restored: AppUser, Role, JournalEntry, InvoiceLine, GSTReturn, etc.
│   ├── coa/               # Chart of Accounts
│   ├── gst/               # GST Module
│   ├── invoicing/         # Invoicing (PDF & Email Logic)
│   ├── journal/           # Journal Entry
│   ├── banking/           # Banking
│   └── reporting/         # Dashboard & Reports
├── common/                # BaseModel, TenantModel, decimal_utils
├── config/                # settings/base.py, celery.py
└── tests/                 # integration/, security/
```

---

## 🗄 Database Architecture

### PostgreSQL Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| **Schemas** | 7 (core, coa, gst, journal, invoicing, banking, audit) | Domain separation |
| **Money Precision** | `NUMERIC(10,4)` | 4 decimal places for all amounts |
| **RLS** | Session variable `app.current_org_id` | Multi-tenant isolation |
| **Integrity** | Circular Deps Resolved | ALTER TABLE FK strategy |

---

## 🧪 Testing Strategy

### Backend Tests (Unmanaged Database Workflow)

**MANDATORY Workflow:**
```bash
# 1. Manually initialize the test database
export PGPASSWORD=ledgersg_secret_to_change
dropdb -h localhost -U ledgersg test_ledgersg_dev
createdb -h localhost -U ledgersg test_ledgersg_dev
psql -h localhost -U ledgersg -d test_ledgersg_dev -f database_schema.sql

# 2. Run tests with reuse flags
source /opt/venv/bin/activate
cd apps/backend
pytest --reuse-db --no-migrations
```

---

## 🔧 Troubleshooting

### Database Issues
- **relation "core.app_user" does not exist**: The test database is empty. Load `database_schema.sql` manually.
- **TypeError: X() got unexpected keyword arguments**: Model and Schema out of sync. LedgerSG is **SQL-First**; update models to match DB columns.
- **circular dependency on DB init**: FKs must be added via `ALTER TABLE` at the end of the script.

### Import Errors
- **ImportError: cannot import name 'X' from 'apps.core.models'**: Check `apps/core/models/__init__.py`. New models must be explicitly exported.

---

## 🚀 Recent Milestones

### PDF & Email Services (2026-02-27) ✅
- **PDF Generation**: Live via WeasyPrint with IRAS-compliant templates.
- **Email Delivery**: Asynchronous Celery tasks with PDF attachments.
- **API Alignment**: `InvoicePDFView` returns `FileResponse` binary.

### Database & Model Hardening (2026-02-27) ✅
- **Restored Models**: `InvoiceLine`, `JournalEntry`, `JournalLine`, `GSTReturn`.
- **Django 6.0 Alignment**: `AppUser` hardened with `password`, `is_staff`, `is_superuser`.
- **Schema Patches**: 20+ columns added to align SQL with Python models.
