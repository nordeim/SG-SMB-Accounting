# LedgerSG Autonomous Agent Briefing Document

**Version:** 1.4.0  
**Classification:** CONFIDENTIAL — Internal Development Use  
**Date:** 2026-03-01  
**Subject:** Comprehensive Project Architecture, Standards, and Operational Directives  

---

## 1. Executive Summary

**LedgerSG** is a production-grade, double-entry accounting platform purpose-built for Singapore Small and Medium Businesses (SMBs). Its primary mission is to transform IRAS 2026 compliance from a regulatory burden into a seamless, automated experience. The platform combines enterprise-grade financial integrity with a distinctive "Illuminated Carbon" neo-brutalist user interface.

**Current Status:** ✅ **Production Ready**  
- **Frontend:** v0.1.0 (Next.js 16.1.6, 18 pages, 114 tests)  
- **Backend:** v0.3.2 (Django 6.0.2, 58 API endpoints, 22 TDD tests)  
- **Database:** v1.0.2 (PostgreSQL 16+, 7 schemas, 28 tables, RLS enforced)  
- **Security Score:** 95% (Audit Verified)  

As an autonomous coding agent, your objective is to maintain this high standard of architectural maturity while executing Pull Requests (PRs). You must operate under the **Meticulous Approach**: Analyze → Plan → Validate → Implement → Verify → Deliver. Surface-level assumptions are prohibited; every change must be grounded in deep technical reasoning.

---

## 2. System Architecture & Technology Stack

The project utilizes a decoupled, service-oriented architecture designed for security, scalability, and regulatory compliance.

### 2.1 Frontend Architecture
- **Framework:** Next.js 16.1.6 (App Router) with React 19.2.
- **Styling:** Tailwind CSS 4.0 + Shadcn/Radix UI primitives.
- **State Management:** Zustand (UI State) + TanStack Query (Server State).
- **Rendering Strategy:** Hybrid. Critical data paths use **Server Components** to ensure zero JWT exposure to client-side JavaScript. Interactive elements (charts, forms) are isolated Client Components.
- **Build Modes:** 
  - `standalone`: For production API integration (`npm run build:server`).
  - `export`: For static CDN deployment (`npm run build`).
- **Design Philosophy:** "Illuminated Carbon" Neo-Brutalist. Reject generic templates. Use whitespace as a structural element. Ensure WCAG AAA compliance.

### 2.2 Backend Architecture
- **Framework:** Django 6.0.2 with Django REST Framework (DRF) 3.16.1.
- **Pattern:** **Service Layer Pattern**. Views are thin controllers; ALL business logic resides in `services/` modules.
- **Task Queue:** Celery 5.4+ with Redis 7+ for async tasks (PDF generation, Email delivery).
- **PDF Engine:** WeasyPrint 68.1 for IRAS-compliant document generation.
- **Directory Structure:**
  ```text
  apps/backend/
  ├── apps/ (core, coa, gst, journal, invoicing, banking, reporting)
  ├── common/ (BaseModel, TenantModel, decimal_utils)
  ├── config/ (settings, celery, urls)
  └── tests/ (integration, security, TDD)
  ```

### 2.3 Database Architecture (SQL-First)
- **Engine:** PostgreSQL 16+.
- **Schema:** 7 Domain-Specific Schemas (`core`, `coa`, `gst`, `journal`, `invoicing`, `banking`, `audit`).
- **Precision:** `NUMERIC(10,4)` for all monetary values. **Floats are strictly prohibited.**
- **Multi-Tenancy:** **Row-Level Security (RLS)** enforced via session variables (`app.current_org_id`).
- **Model Strategy:** **Unmanaged Models** (`managed = False`). The SQL schema (`database_schema.sql`) is the source of truth. Django models map to existing tables; Django migrations are disabled.

---

## 3. Core Development Principles

### 3.1 SQL-First Design
The database schema is the single source of truth. Django models must strictly align with DDL-defined columns.
- **Constraint:** Never run `python manage.py makemigrations`. Schema changes require manual SQL patches followed by model alignment.
- **Testing:** Standard Django test runners fail because they attempt to create tables. You must manually initialize the test database using `database_schema.sql` before running pytest.
- **Alignment:** All 22 Django models are currently aligned with SQL v1.0.2. Any new field requires a SQL patch first.

### 3.2 Security-First Authentication
- **JWT Strategy:** 15-minute Access Token + 7-day Refresh Token.
- **Storage:** Refresh tokens stored in **HttpOnly Cookies**. Access tokens held in server memory during SSR.
- **Exposure:** **Zero JWT exposure** to browser JavaScript. Server Components fetch data server-side using cookies.
- **Middleware:** `TenantContextMiddleware` sets PostgreSQL session variables (`app.current_org_id`) per request to enforce RLS.

### 3.3 Financial Integrity
- **Decimal Precision:** Use `common.decimal_utils.money()` for all currency operations. This utility rejects floats and quantizes to 4 decimal places.
- **Double-Entry:** Enforced via database constraints and `JournalService`. Debits must equal credits.
- **Immutability:** Posted journal entries (`JournalEntry`) are immutable. Corrections require reversing entries, not updates.
- **Audit Trail:** `audit.event_log` table captures immutable before/after values for all critical changes (5-year retention).

### 3.4 Anti-Generic UI Design
- **Library Discipline:** Use Shadcn/Radix primitives. Do not rebuild modals or dropdowns from scratch.
- **Aesthetic:** Reject "safe" defaults (Inter/Roboto). Use bespoke typography and asymmetry where intentional.
- **States:** Handle loading, error, empty, and success states explicitly. Show loading indicators ONLY when no data exists.

---

## 4. Testing Strategy & Quality Assurance

LedgerSG employs Test-Driven Development (TDD) for critical business logic.

### 4.1 Backend Testing Workflow
Standard Django test workflows are incompatible due to unmanaged models.
**Mandatory Workflow:**
1.  **Initialize DB:**
    ```bash
    export PGPASSWORD=ledgersg_secret_to_change
    dropdb -h localhost -U ledgersg test_ledgersg_dev || true
    createdb -h localhost -U ledgersg test_ledgersg_dev
    psql -h localhost -U ledgersg -d test_ledgersg_dev -f database_schema.sql
    ```
2.  **Run Tests:**
    ```bash
    source /opt/venv/bin/activate
    cd apps/backend
    pytest --reuse-db --no-migrations
    ```
- **Coverage:** 52+ passing tests. Focus on Service Layer logic and API endpoint contracts.
- **Fixtures:** Must comply with SQL constraints (e.g., `TaxCode` requires `is_input=TRUE` or `is_output=TRUE`).

### 4.2 Frontend Testing Workflow
- **Runner:** Vitest + React Testing Library.
- **Command:** `npm test` (runs in `apps/web`).
- **Coverage:** 114 tests passing. GST Engine has 100% coverage (critical for IRAS compliance).
- **E2E:** Playwright used for navigation and accessibility scans.

### 4.3 Quality Assurance Checklist
Before submitting any PR, verify:
- [ ] Solution meets all stated requirements.
- [ ] Code follows language-specific best practices (TypeScript strict mode, Django service layer).
- [ ] Comprehensive testing implemented (TDD for backend logic).
- [ ] Security considerations addressed (RLS, Input Validation, No Floats).
- [ ] Documentation updated (README, CLAUDE.md, AGENT_BRIEF.md).
- [ ] Platform-specific requirements met (Docker, Env vars).
- [ ] Edge cases considered (Empty states, Network failures).
- [ ] Long-term maintenance evaluated.

---

## 5. Security & Compliance Posture

### 5.1 IRAS 2026 Compliance
- **GST:** Standard-rated (9%), Zero-rated, Exempt, and Out-of-Scope codes implemented.
- **F5 Returns:** Auto-generation logic ready (`gst.compute_f5_return`).
- **InvoiceNow:** Peppol transmission architecture ready (XML generation pending final logic).
- **BCRS:** Bank Cash Register System deposits exempted from GST calculations.

### 5.2 Vulnerability Management
Recent Security Audit (2026-03-01) scored 95%. Address remaining findings:
- **SEC-001 (HIGH):** Banking module stubs (`apps/backend/apps/banking/views.py`) return unvalidated input. **Action:** Implement proper DRF serializers and validation.
- **SEC-002 (MEDIUM):** No rate limiting on authentication. **Action:** Install `django-ratelimit`.
- **SEC-003 (MEDIUM):** Content Security Policy (CSP) not configured. **Action:** Add CSP headers in middleware.
- **SEC-004 (MEDIUM):** Frontend test coverage minimal outside GST engine. **Action:** Expand tests for hooks and forms.

### 5.3 Data Protection
- **Passwords:** Django hashing (128 char).
- **PII:** GST numbers and bank accounts currently unencrypted at rest. **Recommendation:** Implement field-level encryption for sensitive PII.
- **SQL Injection:** Protected via parameterized queries and ORM. No string concatenation in SQL.

---

## 6. Operational Guidelines

### 6.1 Environment Configuration
- **Backend:** Requires `.env` with `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`.
- **Frontend:** Requires `.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000` and `NEXT_OUTPUT_MODE=standalone`.
- **Docker:** Multi-service container available (`docker/Dockerfile`). Exposes ports 3000 (FE), 8000 (BE), 5432 (DB), 6379 (Redis).

### 6.2 Common Troubleshooting
- **Dashboard "Loading..." Stuck:** Caused by missing static files in standalone build. **Fix:** Run `npm run build:server` (auto-copies static files).
- **403 Forbidden on API:** Check `UserOrganisation.accepted_at` is set (Middleware requirement).
- **Model Schema Mismatch:** `ProgrammingError: column X does not exist`. **Fix:** Align Django model fields with `database_schema.sql`.
- **Circular Dependencies:** SQL FKs must be added via `ALTER TABLE` at the end of the schema script.

### 6.3 Deployment Modes
- **Development:** `npm run dev` (Frontend) + `python manage.py runserver` (Backend).
- **Production:** `npm run build:server` + `npm run start` (Frontend) + Gunicorn (Backend).
- **Static:** `npm run build` + `npm run serve` (No API integration).

---

## 7. Autonomous Agent Directives

As an autonomous agent working on PRs, you must adhere to the following operational protocols:

### 7.1 Request Analysis & Planning
- **Deep Understanding:** Do not accept surface-level requirements. Identify implicit needs (e.g., if asked to add a field, consider RLS, Audit Log, and Serializer implications).
- **Solution Exploration:** Validate assumptions against the `AGENTS.md` knowledge base. If a pattern contradicts the SQL-First architecture, reject it.
- **Risk Assessment:** Identify impacts on Multi-tenancy (RLS) and Financial Integrity (Decimal Precision).

### 7.2 Implementation Standards
- **Backend:** 
  - Logic goes in `services/`, not views.
  - Use `transaction.atomic()` for write operations.
  - Use `money()` utility for all currency values.
  - Respect `managed = False` on models.
- **Frontend:** 
  - Prefer Server Components for data fetching.
  - Use Shadcn primitives; do not custom-build UI components unless necessary.
  - Ensure WCAG AAA accessibility.
- **Database:** 
  - Never use floats.
  - Always filter by `org_id` or rely on RLS session variables.

### 7.3 Validation & Verification
- **Testing:** Write failing tests first (TDD) for backend logic. Ensure frontend tests pass (`npm test`).
- **Security:** Verify no JWT leakage to client. Check input validation on all endpoints (especially Banking).
- **Documentation:** Update relevant markdown files (`README.md`, `ACCOMPLISHMENTS.md`) with change details.

### 7.4 Communication & Delivery
- **Transparency:** Document trade-offs. If a security compromise is made for speed, flag it explicitly.
- **Handoff:** Provide clear usage instructions and migration steps (SQL patches).
- **Lessons Learned:** Record challenges encountered during implementation for future reference.

### 7.5 Prohibited Actions
- **NO** Django migrations (`makemigrations`).
- **NO** Float arithmetic for money.
- **NO** Client-side JWT storage (localStorage).
- **NO** Generic Bootstrap-style layouts.
- **NO** Skipping test initialization steps for backend.

---

## 8. Future Roadmap & Priorities

### 8.1 Immediate (High Priority)
- **Banking Module:** Replace stubs in `banking/views.py` with validated logic (SEC-001).
- **Organization Context:** Replace hardcoded `DEFAULT_ORG_ID` with dynamic user context.
- **Error Handling:** Add retry logic and fallback UI for dashboard API failures.

### 8.2 Short-Term (Medium Priority)
- **Rate Limiting:** Implement `django-ratelimit` on auth endpoints (SEC-002).
- **Frontend Tests:** Expand coverage for hooks and forms (SEC-004).
- **CI/CD:** Automate manual DB initialization workflow in GitHub Actions.

### 8.3 Long-Term (Low Priority)
- **InvoiceNow:** Finalize Peppol XML transmission logic.
- **PII Encryption:** Encrypt sensitive data at rest.
- **Mobile Optimization:** Responsive refinements for dashboard.

---

## 9. Conclusion

LedgerSG represents a mature, security-conscious platform balancing regulatory compliance with modern engineering practices. The **SQL-First** design ensures data integrity, while the **Service Layer** ensures maintainability. 

Your role is to protect this integrity. Every line of code you commit must uphold the **Meticulous Approach**. Do not rush. Validate deeply. Ensure that every feature not only works but is secure, compliant, and aesthetically aligned with the "Illuminated Carbon" vision.

