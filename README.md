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

### Frontend (Complete) ✅

**LedgerSG Frontend v0.1.0** is production-ready with comprehensive testing, security hardening, and documentation.

| Metric | Value |
|--------|-------|
| Static Pages | 18 |
| Unit Tests | **114** |
| GST Test Coverage | 100% |
| Security Headers | 7 configured |
| Build Status | ✅ Passing |

### Backend (Production Ready) ✅

**LedgerSG Backend v0.3.1** — Core business modules implemented with **57 API endpoints**, including regulatory document generation and delivery services.

| Component | Status | Details |
|-----------|--------|---------|
| Integration | ✅ Phase 4 | 100% API coverage, FE/BE aligned |
| Hardening | ✅ Milestone | Models restored, Schema Alignment |
| Services | ✅ Milestone | PDF Generation & Email Delivery live |
| **Total** | **57 Endpoints** | **65+ files, ~11,200 lines, 158+ tests** |

---

## 🧪 Testing

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
```

---

<div align="center">

**LedgerSG** — Built with ❤️ for Singapore SMBs

[Report Bug](https://github.com/ledgersg/ledgersg/issues) · [Request Feature](https://github.com/ledgersg/ledgersg/issues) · [Documentation](https://docs.ledgersg.sg)

</div>
