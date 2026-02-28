# LedgerSG

<div align="center">

[![Build Status](https://img.shields.io/github/actions/workflow/status/ledgersg/ledgersg/ci.yml?branch=main)](https://github.com/ledgersg/ledgersg/actions)
[![Coverage](https://img.shields.io/codecov/c/github/ledgersg/ledgersg)](https://codecov.io/gh/ledgersg/ledgersg)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-20-green)](https://nodejs.org/)
[![Django](https://img.shields.io/badge/django-6.0-green)](https://www.djangoproject.com/)
[![Next.js](https://img.shields.io/badge/next.js-16-black)](https://nextjs.org/)
[![WCAG](https://img.shields.io/badge/WCAG-AAA-success)](https://www.w3.org/WAI/WCAG21/quickref/)
[![IRAS](https://img.shields.io/badge/IRAS-2026%20Compliant-red)](https://www.iras.gov.sg/)

**Enterprise-Grade Accounting Platform for Singapore SMBs**

*IRAS-Compliant • InvoiceNow Ready • GST-Native • WCAG AAA*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [File Structure](#-file-structure)
- [Development Milestones](#-development-milestones)
- [User Interaction Flow](#-user-interaction-flow)
- [Application Logic](#-application-logic)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Database Management](#-database-management)
- [Recommendations & Roadmap](#-recommendations--roadmap)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Backend Service Control](#-backend-service-control)
- [Compliance](#-compliance)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📚 Documentation

LedgerSG provides comprehensive documentation for different audiences:

| Document | Purpose | Audience |
|----------|---------|----------|
| [**Project_Architecture_Document.md**](Project_Architecture_Document.md) | Complete architecture reference, file hierarchy, Mermaid diagrams, database schema | New developers, architects, coding agents |
| [**API_CLI_Usage_Guide.md**](API_CLI_Usage_Guide.md) | Direct API interaction via CLI, curl examples, error handling, limitations | AI agents, backend developers, DevOps |
| [**CLAUDE.md**](CLAUDE.md) | Developer briefing, code patterns, critical files | Developers working on features |
| [**AGENT_BRIEF.md**](AGENT_BRIEF.md) | Agent guidelines, architecture details | Coding agents, AI assistants |
| [**ACCOMPLISHMENTS.md**](ACCOMPLISHMENTS.md) | Feature completion log, milestones, changelog | Project managers, stakeholders |
| [**GEMINI.md**](GEMINI.md) | Project instructional context for AI agents | AI assistants, developers |

**Recommendation**: Start with the [Project Architecture Document](Project_Architecture_Document.md) for a complete understanding of the system.

## 🎯 Overview

**LedgerSG** is a production-grade, double-entry accounting platform purpose-built for Singapore small to medium-sized businesses (SMBs), sole proprietorships, and partnerships. It transforms IRAS compliance from a burden into a seamless, automated experience while delivering a distinctive, anti-generic user interface.

### Core Mission

> Transform IRAS compliance from a burden into a seamless, automated experience while delivering a distinctive, anti-generic user interface that makes financial data approachable yet authoritative.

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
| GST threshold monitoring | ❌ | ✅ (critical) | ✅ Complete |
| InvoiceNow/Peppol transmission | ✅ (mandatory) | Optional | ✅ Complete |
| BCRS deposit handling | ✅ | ✅ | ✅ Complete |
| Transfer Pricing monitoring | ✅ | ✅ | ✅ Complete |
| 5-year document retention | ✅ | ✅ | ✅ Complete |

### Technical Features

- **Double-Entry Integrity**: Every transaction produces balanced debits/credits enforced at database level
- **DECIMAL(10,4) Precision**: No floating-point arithmetic; all amounts stored as NUMERIC in PostgreSQL
- **Real-Time GST Calculation**: Client-side preview with Decimal.js, server-side authoritative calculation
- **Immutable Audit Trail**: All financial mutations logged with before/after values, user, timestamp, IP
- **PDF Document Generation**: IRAS-compliant tax invoices via WeasyPrint
- **Email Delivery Service**: Asynchronous invoice distribution with attachments
- **WCAG AAA Accessibility**: Screen reader support, keyboard navigation, reduced motion respect

---

## ✅ Project Status

**Last Updated**: 2026-02-28  
**Latest Milestone**: Dashboard API & Real Data Integration (TDD) — 22 tests passing, live data from backend

### Frontend (Complete) ✅

**LedgerSG Frontend v0.1.0** is production-ready with comprehensive testing, security hardening, and documentation.

| Metric | Value |
|--------|-------|
| Static Pages | 18 |
| Unit Tests | **114** |
| GST Test Coverage | 100% |
| Security Headers | 7 configured |
| Build Status | ✅ Passing |
| API Integration | ✅ Live (Docker + Standalone) |
| SSR/Hydration | ✅ Fixed (2026-02-28) |
| Standalone Build | ✅ Auto-copies static files |

### Backend (Production Ready) ✅

**LedgerSG Backend v0.3.2** — Core business modules implemented with **58 API endpoints**, including Dashboard API with TDD implementation.

| Component | Status | Details |
|-----------|--------|---------|
| Integration | ✅ Phase 4 | 100% API coverage, FE/BE aligned |
| Hardening | ✅ Milestone | Models restored, Schema Alignment |
| Services | ✅ Milestone | PDF Generation & Email Delivery live |
| Dashboard | ✅ TDD Complete | 22 tests, real data aggregation |
| Models | ✅ 22 Aligned | TaxCode, InvoiceDocument, Organisation fixed |
| Tests | ✅ 74 Passing | SQL constraint compliance verified |
| **Total** | **58 Endpoints** | **67+ files, ~11,600 lines, 180+ tests** |

### Docker Environment (Live) ✅

**Multi-service container** with live frontend-backend integration.

| Service | Port | Status |
|---------|------|--------|
| PostgreSQL | 5432 | ✅ Running |
| Redis | 6379 | ✅ Running |
| Django Backend | 8000 | ✅ 57 endpoints active |
| Next.js Frontend | 3000 | ✅ Standalone server mode |

---

## 🧪 Testing

### Test Status

| Test Suite | Status | Count | Coverage |
|------------|--------|-------|----------|
| Backend Unit | ✅ Passing | 74+ | Core models, services, Dashboard API (TDD) |
| Frontend Unit | ✅ Passing | 114 | GST Engine 100% |
| Integration | ✅ Verified | PDF/Email | Binary stream verified |
| Dashboard | ✅ TDD | 22 | 100% test coverage via TDD |

### TDD Workflow

LedgerSG uses Test-Driven Development for critical business logic:

```bash
# Dashboard API was built with TDD:
# 1. Write tests (Red phase)
# 2. Implement code (Green phase)
# 3. Refactor (Clean code)

# Run dashboard tests
pytest apps/core/tests/test_dashboard_service.py apps/core/tests/test_dashboard_view.py -v
# → 22 passed
```

### Test Commands

```bash
# Backend unit tests (Unmanaged Database Workflow)
# Standard Django runners fail on unmanaged models.
# Manual setup required:
export PGPASSWORD=ledgersg_secret_to_change
dropdb -h localhost -U ledgersg test_ledgersg_dev || true
createdb -h localhost -U ledgersg test_ledgersg_dev
psql -h localhost -U ledgersg -d test_ledgersg_dev -f database_schema.sql
pytest --reuse-db --no-migrations

# Frontend unit tests (Vitest)
cd apps/web && npm test

# Frontend with coverage
cd apps/web && npm run test:coverage
```

### Docker Quick Start

```bash
# Build and run the complete stack
docker build -f docker/Dockerfile -t ledgersg:latest docker/
docker run -p 3000:3000 -p 8000:8000 -p 5432:5432 -p 6379:6379 ledgersg:latest

# Access the services:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/v1/
# Health Check: http://localhost:8000/api/v1/health/
```

---

## 🚀 Backend Service Control

LedgerSG includes a comprehensive **Backend API Service Management Script** for production-ready deployment and development workflows.

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
| **`start [HOST] [PORT] [WORKERS]`** | Start API service | `./backend_api_service.sh start 0.0.0.0 8000 4` |
| **`stop`** | Stop API service gracefully | `./backend_api_service.sh stop` |
| **`restart [HOST] [PORT] [WORKERS]`** | Restart service | `./backend_api_service.sh restart 127.0.0.1 8000 2` |
| **`status`** | Show detailed service status | `./backend_api_service.sh status` |
| **`logs [LINES]`** | View service logs | `./backend_api_service.sh logs 50` |
| **`help`** | Show usage documentation | `./backend_api_service.sh help` |

### Deployment Modes

#### Development Mode (Single Worker)
```bash
./backend_api_service.sh start 127.0.0.1 8000 1
```
- Uses Django development server
- Auto-reload on code changes
- Debug logging enabled
- Ideal for local development

#### Production Mode (Multiple Workers)
```bash
./backend_api_service.sh start 0.0.0.0 8000 4
```
- Uses Gunicorn WSGI server
- Multiple worker processes
- Production-optimized settings
- Suitable for staging/production

#### External Access Mode
```bash
./backend_api_service.sh start 0.0.0.0 8000 2
```
- Binds to all network interfaces
- Accessible from other machines
- Useful for Docker/network deployment

### Service Status Information

The status command provides comprehensive service information:

```bash
$ ./backend_api_service.sh status

============================================
LEDGERSG API SERVICE STATUS
============================================
● Service is running
  PID: 1250655
  Command: gunicorn
  Started: Fri Feb 27 14:39:07 2026
  PID File: /home/user/.ledgersg/ledgersg-api.pid
  Log Directory: /home/user/.ledgersg/logs

[INFO] Service Details:
  Project: LedgerSG API
  Framework: Django 6.0.2
  Database: PostgreSQL

[SUCCESS] Health check: ✅ PASS

Configuration:
  Service Name: ledgersg-api
  Default Host: 127.0.0.1
  Default Port: 8000
  Backend Directory: /home/project/Ledger-SG/apps/backend
  Virtual Environment: /opt/venv
```

### Health Monitoring

The service includes automatic health monitoring:

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

### Log Management

View real-time and historical logs:

```bash
# Show last 50 lines
./backend_api_service.sh logs

# Show last 100 lines
./backend_api_service.sh logs 100

# View live logs (manual)
tail -f ~/.ledgersg/logs/api_service.log

# View Gunicorn logs (production mode)
tail -f ~/.ledgersg/logs/error.log
```

### Configuration Files

The script uses specialized settings for service mode:

- **`config/settings/service.py`** - Service-optimized Django settings
- **`~/.ledgersg/`** - Runtime directory (PID files, logs)
- **`/opt/venv`** - Virtual environment (configurable)

### Prerequisites & Requirements

**System Requirements:**
- Python 3.12+ with virtual environment
- PostgreSQL database running
- LedgerSG backend code installed

**Environment Setup:**
```bash
# Virtual environment (if not exists)
python3 -m venv /opt/venv
source /opt/venv/bin/activate
pip install -e apps/backend/[dev]

# Database setup
psql -h localhost -U ledgersg -d ledgersg_dev -f database_schema.sql
```

### Production Deployment

For production deployment:

```bash
# 1. Create production environment
python3 -m venv /opt/ledgersg-venv
source /opt/ledgersg-venv/bin/activate
pip install -e apps/backend/[prod]

# 2. Configure environment variables
cp apps/backend/.env.example apps/backend/.env
# Edit .env with production settings

# 3. Start production service
./backend_api_service.sh start 0.0.0.0 8000 8

# 4. Verify service health
curl https://your-domain.com/api/v1/health/
```

### Troubleshooting

**Dashboard API returns 403:**
```bash
# Check UserOrganisation.accepted_at is set
# This is required by TenantContextMiddleware
```

**Dashboard shows mock data:**
```bash
# DashboardPage must be async Server Component
# Must call fetchDashboardData() instead of createMockDashboardMetrics()
```

**Service won't start:**
```bash
# Check database connection
./backend_api_service.sh status

# View error logs
./backend_api_service.sh logs 20

# Check port availability
netstat -tulpn | grep :8000
```

**Service not responding:**
```bash
# Check health endpoint
curl -v http://localhost:8000/api/v1/health/

# Restart service
./backend_api_service.sh restart
```

**Permission issues:**
```bash
# Ensure script is executable
chmod +x backend_api_service.sh

# Check log directory permissions
ls -la ~/.ledgersg/
```

### Frontend Troubleshooting

**"Loading..." stuck on dashboard:**
```bash
# Check static files exist in standalone build
ls apps/web/.next/standalone/.next/static/chunks/ | head -5

# Rebuild with static file auto-copy (now automatic)
cd apps/web && npm run clean && npm run build:server

# Check for hydration errors in browser console (F12)
```

**404 errors for JS/CSS chunks:**
```bash
# Manual fix if build script fails
cp -r apps/web/.next/static apps/web/.next/standalone/.next/

# Verify files are accessible
curl -I http://localhost:3000/_next/static/chunks/main.js
```

**Hydration mismatch errors:**
```bash
# Usually caused by Client Components rendering differently on server vs client
# Solutions:
# 1. Convert to Server Component (remove "use client")
# 2. Ensure identical initial render (no conditional rendering based on useEffect)
```

### Advanced Usage

**Custom Configuration:**
```bash
# Edit script configuration
vim backend_api_service.sh

# Key variables to modify:
# - VENV_PATH="/opt/venv"
# - DEFAULT_HOST="127.0.0.1"
# - DEFAULT_PORT="8000"
# - DEFAULT_WORKERS="4"
```

**Process Management:**
```bash
# Find service process
ps aux | grep ledgersg-api

# Manual cleanup (if needed)
pkill -f ledgersg-api
rm -f ~/.ledgersg/ledgersg-api.pid
```

---

<div align="center">

**LedgerSG** — Built with ❤️ for Singapore SMBs

[Report Bug](https://github.com/ledgersg/ledgersg/issues) · [Request Feature](https://github.com/ledgersg/ledgersg/issues) · [Documentation](https://docs.ledgersg.sg)

</div>
