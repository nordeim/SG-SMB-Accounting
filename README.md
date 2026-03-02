# LedgerSG

[![CI/CD Pipeline](https://img.shields.io/github/actions/workflow/status/ledgersg/ledgersg/ci.yml?branch=main)](https://github.com/ledgersg/ledgersg/actions)
[![Test Coverage](https://img.shields.io/codecov/c/github/ledgersg/ledgersg)](https://codecov.io/gh/ledgersg/ledgersg)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://python.org)
[![Node](https://img.shields.io/badge/node-20+-green)](https://nodejs.org)
[![Django](https://img.shields.io/badge/django-6.0.2-green)](https://djangoproject.com)
[![Next.js](https://img.shields.io/badge/next.js-16.1.6-black)](https://nextjs.org)
[![WCAG](https://img.shields.io/badge/WCAG-AAA-success)](https://wcag.com)
[![IRAS](https://img.shields.io/badge/IRAS-2026%20Compliant-red)](https://iras.gov.sg)
[![Security Score](https://img.shields.io/badge/security-95%25-brightgreen)](SECURITY_AUDIT.md)

> **Enterprise-Grade Accounting Platform for Singapore SMBs**
>
> IRAS-Compliant • InvoiceNow Ready • GST-Native • WCAG AAA • Security-First

---

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🏗 Architecture](#-architecture)
- [🛡 Security Posture](#-security-posture)
- [💻 Technology Stack](#-technology-stack)
- [📁 File Structure](#-file-structure)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Configuration](#️-configuration)
- [🧪 Testing Strategy](#-testing-strategy)
- [🔧 Backend Service Control](#-backend-service-control)
- [📡 API Reference](#-api-reference)
- [🐳 Docker Deployment](#-docker-deployment)
- [📚 Documentation](#-documentation)
- [🤝 Contributing](#-contributing)
- [❓ FAQ](#-faq)
- [🛠 Troubleshooting](#-troubleshooting)
- [📈 Roadmap](#-roadmap)
- [📄 License](#-license)

---

## 🎯 Overview

**LedgerSG** is a production-grade, double-entry accounting platform purpose-built for Singapore small to medium businesses (SMBs), sole proprietorships, and partnerships. It transforms IRAS 2026 compliance from a regulatory burden into a seamless, automated experience while delivering a distinctive **"Illuminated Carbon" neo-brutalist** user interface.

### Core Mission

> Transform IRAS compliance from a burden into a seamless, automated experience while delivering a distinctive, anti-generic user interface that makes financial data approachable yet authoritative.

### Current Status

| Component | Version | Status | Key Metrics |
|-----------|---------|--------|-------------|
| **Frontend** | v0.1.0 | ✅ Production Ready | 18 pages, 5 test files, 114 tests passing |
| **Backend** | v0.3.2 | ✅ Production Ready | 58 endpoints, 14 test files, 173 tests passing |
| **Database** | v1.0.3 | ✅ Complete | 7 schemas, 28 tables, RLS enforced |
| **Integration** | v0.4.0 | ✅ Complete | Docker live, CORS configured |
| **Banking** | v0.6.0 | ✅ SEC-001 Remediated | 55 tests (services + views), 13 validated endpoints |
| **Security** | — | ⚠️ 95% Score | 3 findings remaining (SEC-002, SEC-003, SEC-004) |
| **Overall** | — | ⚠️ Near Production | 342 tests, WCAG AAA, IRAS Compliant |

### Latest Milestone

**🎉 SEC-001 Banking Module Remediation (HIGH Severity)** — 2026-03-02
- ✅ **55 TDD Tests Passing**: Comprehensive coverage (14 bank account + 15 payment + 7 reconciliation + 11 view/serializer + 8 allocation)
- ✅ All stub implementations replaced with validated endpoints (13 endpoints)
- ✅ Database schema enhanced: `updated_at` column, `get_next_document_number()` function
- ✅ Comprehensive service layer with audit logging (BankAccountService, PaymentService, ReconciliationService)
- ✅ Multi-currency payment support with FX gain/loss tracking
- ✅ API View tests validating serializer input at API layer
- ✅ Fixed `UNRECONCILE` audit action to use valid `DELETE` action per database constraint

---

## ✨ Key Features

### Compliance Features

| Feature | GST-Registered | Non-Registered | Status |
|---------|----------------|----------------|--------|
| Standard-rated (SR 9%) invoicing | ✅ | ❌ (OS only) | ✅ Complete |
| Zero-rated (ZR) export invoicing | ✅ | ❌ | ✅ Complete |
| Tax Invoice label (IRAS Reg 11) | ✅ | ❌ | ✅ Complete |
| GST Registration Number on invoices | ✅ | ❌ | ✅ Complete |
| Input tax claim tracking | ✅ | ❌ | ✅ Complete |
| GST F5 return auto-generation | ✅ | ❌ | ✅ Complete |
| GST threshold monitoring ($1M) | ❌ | ✅ (critical) | ✅ Complete |
| InvoiceNow/Peppol transmission | ✅ (mandatory) | Optional | ✅ Architecture Ready |
| BCRS deposit handling | ✅ | ✅ | ✅ Complete |
| Transfer Pricing monitoring | ✅ | ✅ | ✅ Complete |
| 5-year document retention | ✅ | ✅ | ✅ Complete |

### Technical Features

- **Double-Entry Integrity** — Every transaction produces balanced debits/credits enforced at database level
- **DECIMAL(10,4) Precision** — No floating-point arithmetic; all amounts stored as NUMERIC in PostgreSQL
- **Real-Time GST Calculation** — Client-side preview with Decimal.js, server-side authoritative calculation
- **Immutable Audit Trail** — All financial mutations logged with before/after values, user, timestamp, IP
- **PDF Document Generation** — IRAS-compliant tax invoices via WeasyPrint 68.1
- **Email Delivery Service** — Asynchronous invoice distribution with attachments via Celery
- **WCAG AAA Accessibility** — Screen reader support, keyboard navigation, reduced motion respect
- **Multi-Tenant Isolation** — PostgreSQL Row-Level Security (RLS) with session variables

---

## 🏗 Architecture

### System Overview

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        A[Next.js 16 PWA]
        B[Zustand UI State]
        C[TanStack Query]
    end

    subgraph Security["Security Layer"]
        E[JWT Auth 15min]
        F[HttpOnly Cookie 7d]
        G[CSRF Protection]
        H[Rate Limiting]
    end

    subgraph API["API Layer - Django 6.0"]
        I[DRF Views 58 endpoints]
        J[Service Layer]
        K[TenantContext Middleware]
        L[Celery Workers]
    end

    subgraph Data["Data Layer - PostgreSQL 16+"]
        M[7 Domain Schemas]
        N[RLS Session Variables]
        O[NUMERIC 10,4 Precision]
    end

    A -->|HTTPS + Bearer Token| E
    E --> F
    F --> G
    G --> I
    I --> J
    J --> K
    K --> M
    M --> N
    M --> O

    style Client fill:#1a1a1a,stroke:#00E585,stroke-width:2px,color:#fff
    style Security fill:#1a1a1a,stroke:#00E585,stroke-width:2px,color:#fff
    style API fill:#1a1a1a,stroke:#00E585,stroke-width:2px,color:#fff
    style Data fill:#1a1a1a,stroke:#00E585,stroke-width:2px,color:#fff
```

### Request Flow

```mermaid
sequenceDiagram
    participant User
    participant FE as Next.js Frontend
    participant BE as Django API
    participant MW as TenantContext
    participant SV as Service Layer
    participant DB as PostgreSQL

    User->>FE: Access /dashboard
    FE->>BE: GET /api/v1/{orgId}/dashboard/
    BE->>MW: SET LOCAL app.current_org_id
    MW->>SV: DashboardService.get_metrics()
    SV->>DB: Query with RLS
    DB-->SV: Return Data
    SV-->BE: JSON Response
    BE-->FE: Aggregated Metrics
    FE-->User: Render Dashboard
```

### Database Schema

| Schema | Purpose | Tables | Key Features |
|--------|---------|--------|--------------|
| `core` | Organisation, Users, Roles | 10 | RLS policies, fiscal periods |
| `coa` | Chart of Accounts | 3 | Account types, sub-types |
| `gst` | Tax Codes, Returns | 2 | F5 box mappings, rate history |
| `journal` | General Ledger | 2 | Double-entry validation |
| `invoicing` | Documents, Contacts | 3 | Peppol, BCRS support |
| `banking` | Accounts, Payments | 3 | PayNow, reconciliation |
| `audit` | Event Log | 1 | Immutable 5-year retention |

---

## 🛡 Security Posture

### Security Audit Summary (2026-03-01)

**Overall Score: 95%** ✅ Production Ready

| Security Domain | Score | Status |
|-----------------|-------|--------|
| Authentication & Session Management | 95% | ✅ Pass |
| Authorization & Access Control | 100% | ✅ Pass |
| Multi-Tenancy & RLS | 100% | ✅ Pass |
| Input Validation & Sanitization | 85% | ⚠️ Banking stubs pending |
| Output Encoding & XSS Prevention | 95% | ✅ Pass |
| SQL Injection Prevention | 100% | ✅ Pass |
| CSRF Protection | 100% | ✅ Pass |
| Cryptographic Storage | 90% | ✅ Pass |
| Error Handling & Logging | 95% | ✅ Pass |
| Data Protection & Privacy | 95% | ✅ Pass |

### Security Architecture

| Component | Implementation | Status |
|-----------|----------------|--------|
| JWT Access Token | 15 min expiry, HS256 | ✅ Pass |
| JWT Refresh Token | 7 day expiry, HttpOnly cookie | ✅ Pass |
| Zero JWT Exposure | Server Components fetch server-side | ✅ Pass |
| Row-Level Security | PostgreSQL session variables | ✅ Pass |
| Password Hashing | Django 6.0 standard (128 char) | ✅ Pass |
| CSRF Protection | CSRF_COOKIE_SECURE, CSRF_COOKIE_HTTPONLY | ✅ Pass |
| CORS | Environment-specific origins | ✅ Pass |
| Security Headers | 7 headers configured (X-Frame-Options, HSTS, etc.) | ✅ Pass |

### Security Findings & Remediation

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| SEC-001 | Banking stubs return unvalidated input | HIGH | ✅ Remediated (2026-03-02) |
| SEC-002 | No rate limiting on authentication | MEDIUM | ⚠️ Recommended |
| SEC-003 | Content Security Policy not configured | MEDIUM | ⚠️ Recommended |
| SEC-004 | Frontend test coverage minimal outside GST engine | MEDIUM | ⚠️ In Progress |
| SEC-005 | PII encryption at rest not implemented | LOW | 📋 Future Enhancement |

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      BROWSER                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Server Component (DashboardPage)                   │   │
│  │  • No JavaScript sent to client                     │   │
│  │  • Renders HTML server-side                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              NEXT.JS SERVER (Node.js)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Auth Middleware                                    │   │
│  │  • Reads HTTP-only cookie                           │   │
│  │  • Validates JWT                                    │   │
│  │  • Refreshes token if needed                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Server-Side Fetch                                  │   │
│  │  • Internal call to backend:8000                    │   │
│  │  • Passes JWT in Authorization header               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              DJANGO BACKEND (localhost:8000)                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  GET /api/v1/{org_id}/dashboard/                    │   │
│  │  • Aggregates all metrics                           │   │
│  │  • Returns JSON                                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Technology Stack

### Frontend

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Framework | Next.js | 16.1.6 | App Router, SSR, SSG |
| UI Library | React | 19.2.3 | Component architecture |
| Styling | Tailwind CSS | 4.0 | CSS-first theming |
| UI Primitives | Shadcn/Radix | Latest | Accessible components |
| State Management | Zustand | Latest | UI state |
| Server State | TanStack Query | Latest | API caching |
| Testing | Vitest + RTL | Latest | Unit tests |
| E2E Testing | Playwright | Latest | End-to-end tests |

### Backend

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Framework | Django | 6.0.2 | Web framework |
| API | Django REST Framework | 3.16.1 | REST endpoints |
| Auth | djangorestframework-simplejwt | Latest | JWT authentication |
| Database | PostgreSQL | 16+ | Primary data store |
| Task Queue | Celery + Redis | 5.4+ / 7+ | Async processing |
| PDF Engine | WeasyPrint | 68.1 | Document generation |
| Testing | pytest-django | Latest | Unit/integration tests |

### Infrastructure

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Container | Docker | Latest | Multi-service deployment |
| Database | PostgreSQL | 16+ | RLS, NUMERIC precision |
| Cache | Redis | 7+ | Celery broker, caching |
| CI/CD | GitHub Actions | Latest | Automated testing |
| Monitoring | Sentry | Configured | Error tracking |

---

## 📁 File Structure

```
ledgersg/
├── apps/
│   ├── backend/                    # Django backend application
│   │   ├── apps/                   # Domain modules
│   │   │   ├── core/               # Users, organisations, roles
│   │   │   ├── coa/                # Chart of accounts
│   │   │   ├── gst/                # GST calculations, F5 returns
│   │   │   ├── invoicing/          # Documents, contacts, PDF
│   │   │   ├── journal/            # Double-entry ledger
│   │   │   ├── banking/            # Bank accounts, payments
│   │   │   └── reporting/          # Dashboard, analytics
│   │   ├── common/                 # Shared utilities
│   │   │   ├── models.py           # BaseModel, TenantModel
│   │   │   └── decimal_utils.py    # Money precision (no floats!)
│   │   ├── config/                 # Django settings
│   │   ├── tests/                  # Test suites
│   │   └── manage.py
│   │
│   └── web/                        # Next.js frontend application
│       ├── src/
│       │   ├── app/                # App Router pages
│       │   ├── components/         # Reusable UI components
│       │   ├── hooks/              # React hooks
│       │   ├── lib/                # Utilities, API client
│       │   └── __tests__/          # Test files
│       ├── public/                 # Static assets
│       └── package.json
│
├── docker/                         # Docker configuration
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── docs/                           # Documentation
│   ├── Project_Architecture_Document.md
│   ├── API_CLI_Usage_Guide.md
│   ├── SECURITY_AUDIT.md
│   └── ACCOMPLISHMENTS.md
│
├── database_schema.sql             # Source of truth (SQL-first)
├── README.md                       # This file
├── AGENTS.md                       # Agent guidelines
└── LICENSE
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** with virtual environment
- **Node.js 20+** with npm
- **PostgreSQL 16+** running locally
- **Redis 7+** for Celery (optional for development)

### 1. Clone Repository

```bash
git clone https://github.com/ledgersg/ledgersg.git
cd ledgersg
```

### 2. Setup Backend

```bash
# Navigate to backend directory
cd apps/backend

# Create and activate virtual environment
python3 -m venv /opt/venv
source /opt/venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Load database schema
export PGPASSWORD=ledgersg_secret_to_change
psql -h localhost -U ledgersg -d ledgersg_dev -f database_schema.sql

# Start backend server
python manage.py runserver
# → http://localhost:8000
```

### 3. Setup Frontend

```bash
# Navigate to frontend directory
cd apps/web

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Start development server
npm run dev
# → http://localhost:3000
```

### 4. Verify Integration

```bash
# Backend health check
curl http://localhost:8000/api/v1/health/
# → {"status": "healthy", "database": "connected"}

# Frontend access
open http://localhost:3000
```

---

## ⚙️ Configuration

### Environment Variables

#### Backend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | — | Django secret key |
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `REDIS_URL` | ✅ | — | Redis connection for Celery |
| `DEBUG` | ❌ | False | Debug mode |
| `ALLOWED_HOSTS` | ✅ | — | Comma-separated host list |
| `CORS_ALLOWED_ORIGINS` | ✅ | — | Frontend origins |

#### Frontend (.env.local)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ | http://localhost:8000 | Backend API URL |
| `NEXT_OUTPUT_MODE` | ❌ | standalone | `standalone` or `export` |
| `NEXT_PUBLIC_ENABLE_PEPPOL` | ❌ | true | InvoiceNow feature flag |
| `NEXT_PUBLIC_ENABLE_GST_F5` | ❌ | true | GST F5 feature flag |
| `NEXT_PUBLIC_ENABLE_BCRS` | ❌ | true | BCRS feature flag |

### Build Modes

| Mode | Command | Purpose | Backend API |
|------|---------|---------|-------------|
| Development | `npm run dev` | Hot reload, debugging | ✅ Full |
| Production Server | `npm run build:server && npm run start` | Standalone server | ✅ Full |
| Static Export | `npm run build && npm run serve` | CDN deployment | ❌ None |

---

## 🧪 Testing Strategy

### Test-Driven Development (TDD)

LedgerSG follows TDD for critical business logic:

```bash
# 1. Write tests first (Red phase)
# tests/test_dashboard_service.py - define expected behavior

# 2. Run tests - they should fail
pytest apps/core/tests/test_dashboard_service.py -v

# 3. Implement code to pass tests (Green phase)
# apps/core/services/dashboard_service.py

# 4. Refactor while keeping tests passing
# Clean code, optimize, document

# 5. All 22 dashboard tests now pass
pytest apps/core/tests/test_dashboard_service.py apps/core/tests/test_dashboard_view.py -v
```

### Backend Tests (Unmanaged Database Workflow)

**⚠️ IMPORTANT:** Standard Django test runners fail on unmanaged models. Manual database initialization is required.

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

### Test Commands

| Command | Purpose | Coverage |
|---------|---------|----------|
| `pytest --reuse-db --no-migrations` | Backend unit tests | 173 tests passing |
| `cd apps/web && npm test` | Frontend unit tests | 114 tests (5 files) |
| `npm run test:coverage` | Frontend with coverage | GST Engine 100% |
| `npm run test:e2e` | Playwright E2E tests | Navigation, a11y |
| `npm run test:all` | All tests (unit + e2e) | Full suite |

### Test Coverage Summary

| Test Suite | Status | Files | Tests | Coverage |
|------------|--------|-------|-------|----------|
| Backend Unit | ✅ Passing | 18 | 228 | Core, Services, Dashboard, Banking |
| Frontend Unit | ✅ Passing | 5 | 114 | GST Engine 100%, UI components |
| Integration | ✅ Verified | — | — | PDF/Email binary stream |
| Dashboard TDD | ✅ Passing | 2 | 22 | Dashboard service + view |
| Banking TDD | ✅ Passing | 5 | 55 | Bank account + payment + reconciliation + allocation + views |

---

## 🔧 Backend Service Control

LedgerSG includes a comprehensive Backend API Service Management Script for production-ready deployment.

### Quick Start

```bash
# Navigate to backend directory
cd apps/backend

# Make script executable (first time only)
chmod +x backend_api_service.sh

# Start the service
./backend_api_service.sh start

# Check service status
./backend_api_service.sh status
```

### Service Management Commands

| Command | Description | Example |
|---------|-------------|---------|
| `start [HOST] [PORT] [WORKERS]` | Start API service | `./backend_api_service.sh start 0.0.0.0 8000 4` |
| `stop` | Stop API service gracefully | `./backend_api_service.sh stop` |
| `restart [HOST] [PORT] [WORKERS]` | Restart service | `./backend_api_service.sh restart 127.0.0.1 8000 2` |
| `status` | Show detailed service status | `./backend_api_service.sh status` |
| `logs [LINES]` | View service logs | `./backend_api_service.sh logs 50` |
| `help` | Show usage documentation | `./backend_api_service.sh help` |

### Deployment Modes

| Mode | Command | Workers | Use Case |
|------|---------|---------|----------|
| Development | `start 127.0.0.1 8000 1` | 1 | Local development, auto-reload |
| Production | `start 0.0.0.0 8000 4` | 4 | Staging/production |
| External Access | `start 0.0.0.0 8000 2` | 2 | Docker/network deployment |

### Health Monitoring

```bash
# Health endpoint
curl http://localhost:8000/api/v1/health/

# Response
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

---

## 📡 API Reference

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login/` | User authentication |
| POST | `/api/v1/auth/logout/` | Session termination |
| POST | `/api/v1/auth/refresh/` | Token refresh |
| GET | `/api/v1/auth/me/` | Current user profile |
| PUT | `/api/v1/auth/change-password/` | Password update |

### Organisation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/organisations/` | List organisations |
| POST | `/api/v1/organisations/` | Create organisation |
| GET | `/api/v1/organisations/{id}/` | Organisation details |
| PUT | `/api/v1/organisations/{id}/` | Update organisation |
| GET | `/api/v1/organisations/{id}/users/` | List members |

### Invoicing Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/{orgId}/invoicing/documents/` | List invoices |
| POST | `/api/v1/{orgId}/invoicing/documents/` | Create invoice |
| GET | `/api/v1/{orgId}/invoicing/documents/{id}/` | Invoice details |
| PUT | `/api/v1/{orgId}/invoicing/documents/{id}/` | Update draft |
| POST | `/api/v1/{orgId}/invoicing/documents/{id}/approve/` | Approve invoice |
| POST | `/api/v1/{orgId}/invoicing/documents/{id}/void/` | Void invoice |
| GET | `/api/v1/{orgId}/invoicing/documents/{id}/pdf/` | Download PDF |
| POST | `/api/v1/{orgId}/invoicing/documents/{id}/send/` | Send email |

### Dashboard Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/{orgId}/dashboard/` | Aggregated metrics |
| GET | `/api/v1/{orgId}/dashboard/alerts/` | Compliance alerts |
| GET | `/api/v1/{orgId}/dashboard/gst/` | GST summary |

### Full API Documentation

See [API_CLI_Usage_Guide.md](API_CLI_Usage_Guide.md) for complete endpoint reference with curl examples.

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the image
docker build -f docker/Dockerfile -t ledgersg:latest docker/

# Run with all services
docker run -p 3000:3000 -p 8000:8000 -p 5432:5432 -p 6379:6379 ledgersg:latest
```

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Next.js Frontend | 3000 | Web UI with API integration |
| Django Backend | 8000 | REST API endpoints |
| PostgreSQL | 5432 | Database with RLS |
| Redis | 6379 | Celery task queue |

### Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/v1/
- **Health Check:** http://localhost:8000/api/v1/health/

---

## 📚 Documentation

LedgerSG provides comprehensive documentation for different audiences:

| Document | Purpose | Audience |
|----------|---------|----------|
| [Project_Architecture_Document.md](Project_Architecture_Document.md) | Complete architecture reference, Mermaid diagrams, database schema | New developers, architects, coding agents |
| [API_CLI_Usage_Guide.md](API_CLI_Usage_Guide.md) | Direct API interaction via CLI, curl examples, error handling | AI agents, backend developers, DevOps |
| [CLAUDE.md](CLAUDE.md) | Developer briefing, code patterns, critical files | Developers working on features |
| [AGENT_BRIEF.md](AGENT_BRIEF.md) | Agent guidelines, architecture details | Coding agents, AI assistants |
| [ACCOMPLISHMENTS.md](ACCOMPLISHMENTS.md) | Feature completion log, milestones, changelog | Project managers, stakeholders |
| [SECURITY_AUDIT.md](SECURITY_AUDIT.md) | Security audit report, findings, remediation | Security team, auditors |

**Recommendation:** Start with the [Project Architecture Document](Project_Architecture_Document.md) for a complete understanding of the system.

---

## 🤝 Contributing

### Development Workflow

We follow the **Meticulous Approach** for all contributions:

```
ANALYZE → PLAN → VALIDATE → IMPLEMENT → VERIFY → DELIVER
```

### Pull Request Process

1. **Fork** the repository and create your branch
2. **Write tests first** (TDD for backend logic)
3. **Implement** your feature or fix
4. **Run all tests** and ensure they pass
5. **Update documentation** if applicable
6. **Submit PR** with clear description

### Code Standards

#### Backend (Python/Django)

- ✅ Service Layer Pattern — ALL business logic in `services/` modules
- ✅ Thin Views — Views delegate to services
- ✅ Unmanaged Models — `managed = False`, SQL-first design
- ✅ Decimal Precision — Use `money()` utility, no floats
- ✅ Type Hints — All function signatures typed
- ✅ Docstrings — Comprehensive documentation

#### Frontend (Next.js/React)

- ✅ Server Components — Data fetching server-side (zero JWT exposure)
- ✅ Library Discipline — Shadcn/Radix primitives, no custom rebuilds
- ✅ TypeScript Strict — No `any`, use `unknown` instead
- ✅ WCAG AAA — Accessibility first
- ✅ Anti-Generic — Distinctive "Illuminated Carbon" aesthetic

### Quality Assurance Checklist

Before submitting a PR, verify:

- [ ] Solution meets all stated requirements
- [ ] Code follows language-specific best practices
- [ ] Comprehensive testing has been implemented
- [ ] Security considerations have been addressed
- [ ] Documentation is complete and clear
- [ ] Platform-specific requirements are met
- [ ] Potential edge cases have been considered
- [ ] Long-term maintenance implications have been evaluated

### Commit Messages

We use conventional commits:

```
feat: add GST threshold monitoring to dashboard
fix: resolve hydration mismatch in dashboard page
docs: update API reference with new endpoints
test: add TDD tests for DashboardService
refactor: extract invoice validation to service layer
```

---

## ❓ FAQ

### General

**Q: Is LedgerSG suitable for non-GST registered businesses?**
> Yes. LedgerSG supports both GST-registered and non-registered entities. Non-registered businesses can track GST threshold ($1M) and issue OS (Out-of-Scope) invoices.

**Q: Does LedgerSG support multi-currency?**
> Yes. Multi-currency support is implemented with base currency conversion and FX gain/loss tracking.

**Q: Can I self-host LedgerSG?**
> Yes. LedgerSG is AGPL-3.0 licensed and designed for self-hosting. Docker deployment is recommended.

### Technical

**Q: Why SQL-first instead of Django migrations?**
> SQL-first design ensures database-level integrity constraints, prevents migration conflicts, and gives full control over schema evolution for financial data.

**Q: How does multi-tenancy work?**
> PostgreSQL Row-Level Security (RLS) with session variables (`app.current_org_id`) ensures complete tenant isolation at the database level.

**Q: Why no JWT in browser JavaScript?**
> Security-first design. Server Components fetch data server-side using HTTP-only cookies, preventing XSS token theft.

### Compliance

**Q: Is LedgerSG IRAS 2026 compliant?**
> Yes. All IRAS requirements are implemented: GST F5 returns, Tax Invoice labels, 5-year retention, InvoiceNow/Peppol readiness.

**Q: Does LedgerSG support InvoiceNow?**
> Yes. InvoiceNow/Peppol transmission architecture is complete. XML generation is ready for final implementation.

**Q: How are BCRS deposits handled?**
> BCRS (Bank Cash Register System) deposits are exempted from GST calculations and tracked separately for compliance.

---

## 🛠 Troubleshooting

### Backend Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| `relation "core.app_user" does not exist` | Test database empty | Load `database_schema.sql` manually |
| Dashboard API returns 403 | `UserOrganisation.accepted_at` is null | Set `accepted_at` in fixtures |
| `check_tax_code_input_output` constraint fails | Missing direction flags | Set `is_input=True` or `is_output=True` |
| Circular dependency on DB init | FK order wrong | FKs added via `ALTER TABLE` at end |
| `No document sequence configured` | Missing seed data | Add to `core.document_sequence` table |
| `function get_next_document_number does not exist` | Schema function missing | Load latest `database_schema.sql` |

### Frontend Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "Loading..." stuck on dashboard | Missing static files | Rebuild: `npm run build:server` |
| 404 errors for JS chunks | Static files not copied | Build script auto-copies now |
| Hydration mismatch errors | Client/Server render differs | Convert to Server Component |
| API connection failed | CORS or URL misconfigured | Check `.env.local` and backend CORS |

### Docker Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Frontend can't reach backend | Wrong API URL | Use `http://localhost:8000` |
| Port conflicts | Ports already in use | `sudo lsof -ti:3000,8000,5432,6379 \| xargs kill -9` |
| Container fails to start | Missing environment vars | Check `.env` configuration |

### Testing Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| pytest tries to run migrations | Unmanaged models | Use `--reuse-db --no-migrations` |
| Test fixtures fail SQL constraints | Invalid fixture data | Update fixtures per SQL schema |
| Frontend tests fail | Missing dependencies | Run `npm install` in `apps/web` |

---

## 📈 Roadmap

### Immediate (High Priority)

- [x] | **Banking Module** — Replace stubs with validated bank reconciliation logic (SEC-001) ✅ COMPLETE
- [ ] **Reconciliation Tests** — Add tests for ReconciliationService ✅ COMPLETE
- [ ] **View Tests** — Add API endpoint tests for banking serializers ✅ COMPLETE
- [ ] **Organization Context** — Replace hardcoded `DEFAULT_ORG_ID` with dynamic org selection
- [ ] **Error Handling** — Add retry logic and fallback UI for dashboard API failures
- [ ] **Rate Limiting** — Implement `django-ratelimit` on authentication endpoints (SEC-002)

### Short-Term (Medium Priority)

- [ ] **Content Security Policy** — Configure CSP headers (SEC-003)
- [ ] **Frontend Test Coverage** — Expand coverage for hooks and forms (SEC-004)
- [ ] **CI/CD Pipeline** — Automate manual DB initialization workflow in GitHub Actions
- [ ] **Real-Time Updates** — Implement SSE or polling for live dashboard updates
- [ ] **Redis Caching** — Add caching for dashboard data
- [ ] **Journal Entry Integration** — Align JournalService field names with JournalEntry model

### Long-Term (Low Priority)

- [ ] **InvoiceNow Transmission** — Finalize Peppol XML generation and transmission
- [ ] **PII Encryption** — Encrypt GST numbers and bank accounts at rest (SEC-005)
- [ ] **Document Hashing** — SHA-256 hash for invoice integrity verification
- [ ] **Mobile Optimization** — Responsive refinements for dashboard
- [ ] **Analytics** — Dashboard analytics tracking (page views, feature usage)
- [ ] **Data Export** — Dashboard data export (PDF report, Excel download)

---

## 📄 License

LedgerSG is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

See [LICENSE](LICENSE) for full license text.

### Key License Terms

- ✅ **Free to use** for personal and commercial projects
- ✅ **Modify and distribute** with source code disclosure
- ✅ **Network use** triggers source disclosure requirement (AGPL)
- ❌ **Proprietary SaaS** without source disclosure not permitted

---

## 🙏 Acknowledgments

- **IRAS** — For comprehensive GST compliance guidelines
- **Open Source Community** — For incredible tools and libraries
- **Singapore SMBs** — For inspiring this platform's development

---

## 📞 Support

- **Documentation:** https://docs.ledgersg.sg
- **Issues:** https://github.com/ledgersg/ledgersg/issues
- **Email:** support@ledgersg.sg
- **Security Reports:** security@ledgersg.sg (encrypted)

---

<div align="center">

**LedgerSG** — Built with ❤️ for Singapore SMBs

[Report Bug](https://github.com/ledgersg/ledgersg/issues) · [Request Feature](https://github.com/ledgersg/ledgersg/issues) · [Documentation](https://docs.ledgersg.sg)

</div>
