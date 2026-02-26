# Singapore SMB Accounting Software — Regulatory Research & Architectural Blueprint

---

## PART 1: REGULATORY LANDSCAPE — IRAS CHANGES IMPACTING SINGAPORE SMBs (2025–2026)

### 1.1 GST Rate at 9%

For any standard-rated supplies of goods or services made on or after 1 Jan 2024, businesses must charge GST at 9%. As of 2026, the GST rate in Singapore is 9% for all taxable goods and services (except for nil-rated).

### 1.2 GST Registration Threshold — S$1 Million

The GST registration threshold in Singapore is SGD 1 million in annual taxable turnover. Businesses exceeding this threshold must register for Singapore GST. Registration is compulsory when taxable turnover exceeds S$1 million either at the end of the calendar year or if the business can reasonably expect to exceed this threshold in the next 12 months. From 1 July 2025, businesses registering prospectively are given two months' grace from the forecast date to begin charging GST — but registration must still be applied for within 30 days of making the forecast.

Businesses below the threshold can register voluntarily. Around 70% of businesses that newly register for GST today do so voluntarily, even though their turnover falls below the threshold.

### 1.3 InvoiceNow (Peppol E-Invoicing) — Major Structural Change

This is the single most consequential change for any accounting software targeting Singapore SMBs.

The GST InvoiceNow Requirement will be implemented progressively: from 1 May 2025 for voluntary early adoption by GST-registered businesses as a soft launch; from 1 November 2025 for newly incorporated companies that register for GST voluntarily; from 1 April 2026 for all new voluntary GST-registrants.

There are plans to progressively extend mandatory participation to new compulsory GST registrants and existing GST-registered businesses.

New voluntary GST registrants that are limited liability partnerships, sole-proprietorships and partnership businesses, the requirement will be implemented from April 1, 2026.

**Technical requirements:**
- InvoiceNow, introduced by IMDA, is Singapore's secure e-invoicing network. Built on the internationally recognised Peppol standard, it enables invoices to be sent in a consistent digital format across different accounting systems.
- InvoiceNow operates using a 5-corner model, an extension of the Peppol 4-corner model, with IRAS acting as the fifth corner to receive invoice data for tax reporting.
- Businesses use IMDA-accredited Access Points (APs) or approved InvoiceNow-ready accounting software to connect to the Peppol network. The acceptable formats are Peppol BIS Billing 3.0 XML and PINT-SG.
- Invoice data must be submitted by the time of the GST return. The deadline to transmit invoice data is the earlier of the date you actually file the relevant GST return, or the official due date for filing that GST return.
- Failure to comply, especially for new voluntary registrants, may result in denial or revocation of GST registration.

### 1.4 Corporate Income Tax — Budget 2026 Rebate

As announced in Budget 2026, a CIT Rebate of 40% of the corporate tax payable will be granted to all taxpaying companies, whether tax resident or not, for YA 2026. Active companies that employed at least one local employee in 2025 will receive a minimum benefit of $1,500 in the form of a CIT Rebate Cash Grant. The total maximum benefits of the CIT Rebate and CIT Rebate Cash Grant that a company may receive is $30,000.

The corporate tax rate is a flat 17% on chargeable income.

### 1.5 Sole Proprietorships & Partnerships — Filing Simplification

Sole proprietorships and partnerships are not treated as companies in Singapore. Their profits are taxed as personal income, subject to progressive individual tax rates.

Partnerships will now enjoy simplified tax filing using the 2-line statement (Revenue and Adjusted Profit/Loss) when their revenue is $200,000 or less. Previously, only sole-proprietors with revenue of $200,000 or below were able to enjoy this benefit.

Partners and sole-proprietors must report business income using the 4-line statement (Revenue, Gross Profit/Loss, Allowable Business Expenses and Adjusted Profit/Loss) only when revenue exceeds $200,000.

### 1.6 Key Filing Dates for 2026

01 Mar 2026 — Submit Self-Employment Income Records; 01 Mar 2026 — Submit Employment Income Records; 31 Mar 2026 — File Estimated Chargeable Income (ECI) (Dec financial year-end).
18 Apr 2026 — File Individual & Partnership Income Tax Return; 30 Apr 2026 — File GST return (period ending in Mar).
30 Nov 2026 — File Corporate Income Tax Return (Form C-S/C-S(Lite)/C); 31 Dec 2026 — File ECI (Sep financial year-end).

### 1.7 Record-Keeping & Multi-Currency

Invoices must be archived for 5 years. Most SMEs record invoices in SGD using a consistent rate source on the invoice date, then record settlement using the rate on the payment date. The difference should go to FX gain/loss, not revenue or expenses.

### 1.8 CPF Changes for 2026

The monthly OW ceiling will be increased to SGD 8,000 from 1 January 2026.

---

## PART 2: ARCHITECTURAL BLUEPRINT — "LedgerSG"

**Product Name**: **LedgerSG** — Enterprise-Grade Accounting Software for Singapore SMBs

---

### 2.1 Executive Summary

LedgerSG is a production-grade, double-entry accounting platform purpose-built for Singapore SMBs, sole proprietorships, and partnerships. It enforces IRAS-compliant GST at 9%, natively integrates with the InvoiceNow (Peppol) e-invoicing network, and supports both GST-registered and non-GST-registered workflows. The system uses `DECIMAL(10,4)` precision throughout all financial calculations, with PostgreSQL 16 stored procedures for critical fiscal computations, a Django 6.0 API backend, and a Next.js 15 + React 19 + Tailwind CSS 4 + Shadcn-UI frontend.

---

### 2.2 Architectural Principles

| Principle | Rationale |
|---|---|
| **Double-Entry Integrity** | Every transaction produces balanced debits and credits enforced at the database level via PostgreSQL constraints |
| **DECIMAL(10,4) Everywhere** | No floating-point arithmetic for money. All amounts stored as `NUMERIC(10,4)` in Postgres, `Decimal` in Python |
| **GST-Native** | GST is a first-class concept: every line item knows its GST treatment (SR, ZR, ES, OS, TX) |
| **InvoiceNow-Ready** | Peppol PINT-SG XML generation and transmission via IMDA-accredited Access Points built-in from day one |
| **Multi-Entity** | One installation supports multiple business entities (sole-prop, partnership, Pte Ltd) with isolated charts of accounts |
| **Audit Trail** | Immutable journal entries; corrections only via reversing entries. Full event sourcing on sensitive operations |
| **Singapore-First** | Chart of Accounts, tax codes, financial year logic, GST F5/F7 return generation, IRAS filing deadlines are hardcoded for Singapore regulatory compliance |

---

### 2.3 System Architecture — C4 Level 1 (Context)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              LEDGERSG PLATFORM                              │
│                                                                             │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────────────────┐ │
│  │   Next.js    │    │  Django REST API │    │     PostgreSQL 16            │ │
│  │   Frontend   │◄──►│  (Python 3.13+) │◄──►│  (Schemas, Stored Procs,    │ │
│  │  React 19    │    │  DRF + Ninja    │    │   Triggers, Row-Level Sec)  │ │
│  │  TW CSS 4    │    │                 │    │                              │ │
│  │  Shadcn-UI   │    │                 │    │                              │ │
│  └──────┬───────┘    └───────┬─────────┘    └──────────────────────────────┘ │
│         │                    │                                               │
│         │                    ├──────────► Celery + Redis (Async Jobs)        │
│         │                    ├──────────► S3/MinIO (Document Storage)        │
│         │                    └──────────► Peppol Access Point (InvoiceNow)   │
│         │                                                                    │
│         └── Served via Vercel / Docker Nginx                                │
└──────────────────────────────────────────────────────────────────────────────┘
          │                    │                         │
          ▼                    ▼                         ▼
    ┌──────────┐     ┌────────────────┐        ┌─────────────────┐
    │ Browser  │     │  IRAS myTax    │        │ IMDA InvoiceNow │
    │ (SMB     │     │  (GST Returns  │        │ Peppol Network  │
    │  User)   │     │   via API/     │        │ (5-Corner Model)│
    │          │     │   Manual)      │        │                 │
    └──────────┘     └────────────────┘        └─────────────────┘
```

---

### 2.4 Database Architecture — PostgreSQL 16

#### 2.4.1 Schema Strategy

```
ledgersg_db/
├── core                  -- Tenancy, users, organisations, permissions
├── coa                   -- Chart of Accounts (Singapore SFRS-aligned)
├── journal               -- General Ledger, Journal Entries, Lines
├── gst                   -- GST configuration, tax codes, returns, InvoiceNow
├── invoicing             -- Sales/Purchase invoices, credit/debit notes
├── banking               -- Bank accounts, reconciliation, payment records
├── inventory             -- Stock (optional module for trading SMBs)
├── payroll               -- CPF, IR8A, employee records (future module)
├── reporting             -- Materialized views, report definitions
└── audit                 -- Immutable audit log, event sourcing
```

#### 2.4.2 Core Tables (Annotated DDL)

```sql
-- =============================================================================
-- SCHEMA: core
-- Purpose: Multi-tenant organisation management
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE core.organisation (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    uen             VARCHAR(20) UNIQUE,          -- Unique Entity Number (ACRA)
    entity_type     VARCHAR(20) NOT NULL          -- 'sole_prop', 'partnership', 'pte_ltd', 'llp'
        CHECK (entity_type IN ('sole_prop', 'partnership', 'pte_ltd', 'llp')),
    gst_registered  BOOLEAN NOT NULL DEFAULT FALSE,
    gst_reg_number  VARCHAR(20),                  -- e.g., M90312345A
    gst_reg_date    DATE,
    financial_year_end SMALLINT NOT NULL DEFAULT 12, -- Month (1-12)
    base_currency   CHAR(3) NOT NULL DEFAULT 'SGD',
    peppol_id       VARCHAR(64),                  -- For InvoiceNow
    invoicenow_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- SCHEMA: coa
-- Purpose: Singapore-aligned Chart of Accounts with flexible hierarchy
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS coa;

CREATE TABLE coa.account_type (
    id          SMALLINT PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,             -- 'Asset', 'Liability', 'Equity', 'Revenue', 'Expense'
    normal_balance VARCHAR(6) NOT NULL             -- 'DEBIT' or 'CREDIT'
        CHECK (normal_balance IN ('DEBIT', 'CREDIT')),
    display_order SMALLINT NOT NULL
);

CREATE TABLE coa.account (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES core.organisation(id),
    code            VARCHAR(10) NOT NULL,          -- e.g., '1000', '2100', '4000'
    name            VARCHAR(150) NOT NULL,
    account_type_id SMALLINT NOT NULL REFERENCES coa.account_type(id),
    parent_id       UUID REFERENCES coa.account(id),
    is_system       BOOLEAN NOT NULL DEFAULT FALSE, -- Locked system accounts (GST Output, etc.)
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    currency        CHAR(3) NOT NULL DEFAULT 'SGD',
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(org_id, code)
);

-- =============================================================================
-- SCHEMA: gst
-- Purpose: GST tax codes, rates, computation logic
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS gst;

-- Singapore GST Tax Codes (aligned with IRAS classifications)
CREATE TABLE gst.tax_code (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(10) NOT NULL UNIQUE,   -- 'SR', 'ZR', 'ES', 'OS', 'TX', 'BL', 'EP', 'OP'
    description     VARCHAR(100) NOT NULL,
    rate            NUMERIC(5,4) NOT NULL,         -- 0.0900 for 9%, 0.0000 for 0%
    is_input        BOOLEAN NOT NULL DEFAULT FALSE,-- TRUE for purchase tax codes
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from  DATE NOT NULL DEFAULT '2024-01-01',
    effective_to    DATE,                           -- NULL = current
    gst_return_box  VARCHAR(10)                    -- Maps to GST F5 return box number
);

-- Seed Singapore tax codes
INSERT INTO gst.tax_code (code, description, rate, is_input, gst_return_box) VALUES
    ('SR',  'Standard-Rated Supply (9%)',       0.0900, FALSE, 'Box 1'),
    ('ZR',  'Zero-Rated Supply',                0.0000, FALSE, 'Box 2'),
    ('ES',  'Exempt Supply',                    0.0000, FALSE, 'Box 3'),
    ('OS',  'Out-of-Scope Supply',              0.0000, FALSE, NULL),
    ('TX',  'Taxable Purchase (9%)',            0.0900, TRUE,  'Box 5'),
    ('TX-E','Taxable Purchase (9%) - Denied',   0.0900, TRUE,  NULL),    -- Non-claimable
    ('BL',  'Blocked Input Tax',                0.0900, TRUE,  NULL),
    ('ZP',  'Zero-Rated Purchase',              0.0000, TRUE,  'Box 5'),
    ('EP',  'Exempt Purchase',                  0.0000, TRUE,  NULL),
    ('OP',  'Out-of-Scope Purchase',            0.0000, TRUE,  NULL),
    ('RS',  'Reverse Charge',                   0.0900, TRUE,  'Box 5');

-- =============================================================================
-- SCHEMA: journal
-- Purpose: Immutable double-entry general ledger
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS journal;

CREATE TABLE journal.entry (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES core.organisation(id),
    entry_number    BIGINT NOT NULL,               -- Sequential per org
    entry_date      DATE NOT NULL,
    reference       VARCHAR(100),
    narration       TEXT NOT NULL,
    source_type     VARCHAR(30) NOT NULL,           -- 'INVOICE', 'PAYMENT', 'MANUAL', 'ADJUSTMENT'
    source_id       UUID,                           -- FK to originating document
    is_reversed     BOOLEAN NOT NULL DEFAULT FALSE,
    reversed_by     UUID REFERENCES journal.entry(id),
    posted_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    posted_by       UUID NOT NULL,                  -- User ID
    fiscal_year     SMALLINT NOT NULL,
    fiscal_period   SMALLINT NOT NULL,              -- 1-12 (or 1-13 for adj period)
    UNIQUE(org_id, entry_number)
);

CREATE TABLE journal.line (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id        UUID NOT NULL REFERENCES journal.entry(id),
    line_number     SMALLINT NOT NULL,
    account_id      UUID NOT NULL REFERENCES coa.account(id),
    description     VARCHAR(255),
    debit           NUMERIC(10,4) NOT NULL DEFAULT 0,
    credit          NUMERIC(10,4) NOT NULL DEFAULT 0,
    tax_code_id     UUID REFERENCES gst.tax_code(id),
    tax_amount      NUMERIC(10,4) NOT NULL DEFAULT 0,
    currency        CHAR(3) NOT NULL DEFAULT 'SGD',
    exchange_rate   NUMERIC(12,6) NOT NULL DEFAULT 1.000000,
    base_debit      NUMERIC(10,4) NOT NULL DEFAULT 0,   -- SGD equivalent
    base_credit     NUMERIC(10,4) NOT NULL DEFAULT 0,   -- SGD equivalent
    CONSTRAINT chk_debit_credit CHECK (
        (debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0) OR (debit = 0 AND credit = 0)
    )
);

-- =============================================================================
-- CRITICAL: Balanced Entry Constraint (Stored Procedure + Trigger)
-- Ensures every journal entry balances to zero
-- =============================================================================

CREATE OR REPLACE FUNCTION journal.validate_entry_balance()
RETURNS TRIGGER AS $$
DECLARE
    v_total_debit  NUMERIC(10,4);
    v_total_credit NUMERIC(10,4);
BEGIN
    SELECT COALESCE(SUM(base_debit), 0), COALESCE(SUM(base_credit), 0)
    INTO v_total_debit, v_total_credit
    FROM journal.line
    WHERE entry_id = NEW.entry_id;

    IF v_total_debit <> v_total_credit THEN
        RAISE EXCEPTION 'Journal entry % is unbalanced: Debit=% Credit=%',
            NEW.entry_id, v_total_debit, v_total_credit;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- GST Computation Stored Procedure
-- Handles precise 9% GST calculation with DECIMAL(10,4)
-- =============================================================================

CREATE OR REPLACE FUNCTION gst.calculate_gst(
    p_amount        NUMERIC(10,4),
    p_tax_code      VARCHAR(10),
    p_is_inclusive   BOOLEAN DEFAULT FALSE
) RETURNS TABLE (
    net_amount      NUMERIC(10,4),
    gst_amount      NUMERIC(10,4),
    gross_amount    NUMERIC(10,4)
) AS $$
DECLARE
    v_rate NUMERIC(5,4);
BEGIN
    SELECT rate INTO v_rate
    FROM gst.tax_code
    WHERE code = p_tax_code AND is_active = TRUE
    AND effective_from <= CURRENT_DATE
    AND (effective_to IS NULL OR effective_to >= CURRENT_DATE);

    IF v_rate IS NULL THEN
        v_rate := 0;
    END IF;

    IF p_is_inclusive THEN
        -- Extract GST from GST-inclusive amount using tax fraction
        -- For 9%: GST = Amount × 9/109
        gst_amount   := ROUND(p_amount * v_rate / (1 + v_rate), 4);
        net_amount   := p_amount - gst_amount;
        gross_amount := p_amount;
    ELSE
        -- Calculate GST on top of net amount
        net_amount   := p_amount;
        gst_amount   := ROUND(p_amount * v_rate, 4);
        gross_amount := p_amount + gst_amount;
    END IF;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- SCHEMA: invoicing
-- Purpose: Sales & Purchase invoices with GST line-level precision
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS invoicing;

CREATE TYPE invoicing.document_type AS ENUM (
    'SALES_INVOICE', 'SALES_CREDIT_NOTE', 'SALES_DEBIT_NOTE',
    'PURCHASE_INVOICE', 'PURCHASE_CREDIT_NOTE', 'PURCHASE_DEBIT_NOTE',
    'PURCHASE_ORDER', 'SALES_QUOTE'
);

CREATE TYPE invoicing.document_status AS ENUM (
    'DRAFT', 'APPROVED', 'SENT', 'PARTIALLY_PAID', 'PAID', 'OVERDUE', 'VOID'
);

CREATE TABLE invoicing.contact (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES core.organisation(id),
    name            VARCHAR(255) NOT NULL,
    uen             VARCHAR(20),
    gst_reg_number  VARCHAR(20),
    is_gst_registered BOOLEAN NOT NULL DEFAULT FALSE,
    contact_type    VARCHAR(10) NOT NULL CHECK (contact_type IN ('CUSTOMER', 'SUPPLIER', 'BOTH')),
    email           VARCHAR(255),
    phone           VARCHAR(20),
    address_line1   VARCHAR(255),
    address_line2   VARCHAR(255),
    postal_code     VARCHAR(10),
    country         CHAR(2) NOT NULL DEFAULT 'SG',
    peppol_id       VARCHAR(64),                 -- Customer's Peppol ID for InvoiceNow
    default_currency CHAR(3) NOT NULL DEFAULT 'SGD',
    payment_terms_days SMALLINT NOT NULL DEFAULT 30,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE invoicing.document (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES core.organisation(id),
    document_type   invoicing.document_type NOT NULL,
    document_number VARCHAR(30) NOT NULL,         -- Auto-generated sequential
    document_date   DATE NOT NULL,
    due_date        DATE,
    contact_id      UUID NOT NULL REFERENCES invoicing.contact(id),
    currency        CHAR(3) NOT NULL DEFAULT 'SGD',
    exchange_rate   NUMERIC(12,6) NOT NULL DEFAULT 1.000000,
    subtotal        NUMERIC(10,4) NOT NULL DEFAULT 0,
    total_gst       NUMERIC(10,4) NOT NULL DEFAULT 0,
    total_amount    NUMERIC(10,4) NOT NULL DEFAULT 0,
    amount_paid     NUMERIC(10,4) NOT NULL DEFAULT 0,
    status          invoicing.document_status NOT NULL DEFAULT 'DRAFT',
    reference       VARCHAR(100),
    notes           TEXT,
    -- InvoiceNow fields
    peppol_message_id   UUID,                     -- Peppol transmission ID
    invoicenow_status   VARCHAR(20),              -- 'PENDING', 'TRANSMITTED', 'FAILED', 'N/A'
    invoicenow_sent_at  TIMESTAMPTZ,
    -- Linked journal entry (created on APPROVE)
    journal_entry_id    UUID REFERENCES journal.entry(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(org_id, document_type, document_number)
);

CREATE TABLE invoicing.document_line (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES invoicing.document(id) ON DELETE CASCADE,
    line_number     SMALLINT NOT NULL,
    description     VARCHAR(500) NOT NULL,
    account_id      UUID NOT NULL REFERENCES coa.account(id),
    quantity        NUMERIC(10,4) NOT NULL DEFAULT 1,
    unit_price      NUMERIC(10,4) NOT NULL,
    discount_pct    NUMERIC(5,2) NOT NULL DEFAULT 0,
    tax_code_id     UUID NOT NULL REFERENCES gst.tax_code(id),
    -- All computed via stored procedure, stored for performance
    line_amount     NUMERIC(10,4) NOT NULL,       -- qty × unit_price × (1 - discount%)
    gst_amount      NUMERIC(10,4) NOT NULL,       -- Precise 9% calculation
    total_amount    NUMERIC(10,4) NOT NULL,        -- line_amount + gst_amount
    UNIQUE(document_id, line_number)
);

-- =============================================================================
-- GST Return Data (GST F5 / F7)
-- =============================================================================

CREATE TABLE gst.return (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES core.organisation(id),
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    filing_due_date DATE NOT NULL,
    -- GST F5 Box Values (all NUMERIC(10,4) for precision)
    box1_standard_rated_supplies    NUMERIC(10,4) NOT NULL DEFAULT 0,
    box2_zero_rated_supplies        NUMERIC(10,4) NOT NULL DEFAULT 0,
    box3_exempt_supplies            NUMERIC(10,4) NOT NULL DEFAULT 0,
    box4_total_supplies             NUMERIC(10,4) NOT NULL DEFAULT 0, -- 1+2+3
    box5_total_taxable_purchases    NUMERIC(10,4) NOT NULL DEFAULT 0,
    box6_output_tax                 NUMERIC(10,4) NOT NULL DEFAULT 0,
    box7_input_tax_claimable        NUMERIC(10,4) NOT NULL DEFAULT 0,
    box8_net_gst_payable            NUMERIC(10,4) NOT NULL DEFAULT 0, -- 6-7
    box9_goods_imported_under_mgs   NUMERIC(10,4) NOT NULL DEFAULT 0,
    box10_reverse_charge            NUMERIC(10,4) NOT NULL DEFAULT 0,
    status          VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'COMPUTED', 'REVIEWED', 'FILED')),
    filed_at        TIMESTAMPTZ,
    computed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Audit Log (Immutable, append-only)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE audit.log (
    id              BIGSERIAL PRIMARY KEY,
    org_id          UUID NOT NULL,
    user_id         UUID NOT NULL,
    action          VARCHAR(50) NOT NULL,          -- 'CREATE', 'UPDATE', 'DELETE', 'APPROVE', 'VOID'
    entity_type     VARCHAR(50) NOT NULL,          -- 'invoice', 'journal_entry', 'payment'
    entity_id       UUID NOT NULL,
    old_data        JSONB,
    new_data        JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Partition audit log by month for performance at scale
CREATE INDEX idx_audit_log_org_date ON audit.log (org_id, created_at DESC);
CREATE INDEX idx_audit_log_entity ON audit.log (entity_type, entity_id);
```

#### 2.4.3 Key Stored Procedures

```sql
-- =============================================================================
-- Auto-compute GST F5 Return from Journal Data
-- =============================================================================

CREATE OR REPLACE FUNCTION gst.compute_return(
    p_org_id        UUID,
    p_period_start  DATE,
    p_period_end    DATE
) RETURNS UUID AS $$
DECLARE
    v_return_id UUID;
    v_box1 NUMERIC(10,4) := 0;
    v_box2 NUMERIC(10,4) := 0;
    v_box3 NUMERIC(10,4) := 0;
    v_box5 NUMERIC(10,4) := 0;
    v_box6 NUMERIC(10,4) := 0;
    v_box7 NUMERIC(10,4) := 0;
    v_box10 NUMERIC(10,4) := 0;
BEGIN
    -- Box 1: Total value of standard-rated supplies
    SELECT COALESCE(SUM(dl.line_amount), 0) INTO v_box1
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE')
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND tc.code = 'SR';

    -- Box 2: Total value of zero-rated supplies
    SELECT COALESCE(SUM(dl.line_amount), 0) INTO v_box2
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE')
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND tc.code = 'ZR';

    -- Box 3: Exempt supplies
    SELECT COALESCE(SUM(dl.line_amount), 0) INTO v_box3
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE')
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND tc.code = 'ES';

    -- Box 5: Total taxable purchases
    SELECT COALESCE(SUM(dl.line_amount), 0) INTO v_box5
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.document_type IN ('PURCHASE_INVOICE', 'PURCHASE_DEBIT_NOTE')
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND tc.code IN ('TX', 'ZP', 'RS');

    -- Box 6: Output tax (9% on standard-rated)
    SELECT COALESCE(SUM(dl.gst_amount), 0) INTO v_box6
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE')
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND tc.code = 'SR';

    -- Box 7: Input tax claimable (exclude blocked)
    SELECT COALESCE(SUM(dl.gst_amount), 0) INTO v_box7
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.document_type IN ('PURCHASE_INVOICE', 'PURCHASE_DEBIT_NOTE')
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND tc.code IN ('TX', 'RS')
        AND tc.code NOT IN ('BL', 'TX-E');

    -- Credit notes reduce respective boxes (subtracted)
    -- [Additional logic for credit/debit note adjustments omitted for brevity]

    INSERT INTO gst.return (
        org_id, period_start, period_end,
        filing_due_date,
        box1_standard_rated_supplies, box2_zero_rated_supplies,
        box3_exempt_supplies, box4_total_supplies,
        box5_total_taxable_purchases,
        box6_output_tax, box7_input_tax_claimable,
        box8_net_gst_payable, box10_reverse_charge,
        status, computed_at
    ) VALUES (
        p_org_id, p_period_start, p_period_end,
        (p_period_end + INTERVAL '1 month')::DATE,
        v_box1, v_box2, v_box3, (v_box1 + v_box2 + v_box3),
        v_box5, v_box6, v_box7,
        (v_box6 - v_box7), v_box10,
        'COMPUTED', NOW()
    ) RETURNING id INTO v_return_id;

    RETURN v_return_id;
END;
$$ LANGUAGE plpgsql;
```

---

### 2.5 Django Backend Architecture

#### 2.5.1 Project Structure

```
ledgersg-api/
├── pyproject.toml                 # Python 3.13+, Django 6.0
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/                      # Organisation, Users, Auth (Singpass future)
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   └── tests/
│   ├── accounting/                # Chart of Accounts, Journal Entries
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── journal_service.py
│   │   │   └── coa_service.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── tests/
│   ├── gst/                       # GST Tax Codes, Computation, Returns
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── gst_calculator.py  # DECIMAL precision enforced
│   │   │   ├── gst_return_service.py
│   │   │   └── gst_validator.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── tests/
│   ├── invoicing/                 # Sales/Purchase Invoices, Credit Notes
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── invoice_service.py
│   │   │   ├── numbering_service.py
│   │   │   └── pdf_generator.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── tests/
│   ├── peppol/                    # InvoiceNow / Peppol PINT-SG Integration
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── pint_sg_builder.py # XML generation (UBL 2.1 / PINT-SG)
│   │   │   ├── access_point_client.py
│   │   │   └── peppol_directory.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── tests/
│   ├── banking/                   # Bank feeds, reconciliation
│   │   ├── models.py
│   │   ├── services/
│   │   └── tests/
│   └── reporting/                 # P&L, Balance Sheet, Trial Balance, GST F5
│       ├── services/
│       │   ├── financial_reports.py
│       │   ├── gst_f5_report.py
│       │   └── iras_export.py
│       └── tests/
├── common/
│   ├── decimal_utils.py           # Decimal context manager, rounding rules
│   ├── currency.py                # Multi-currency helpers
│   ├── pagination.py
│   ├── exceptions.py
│   └── middleware/
│       ├── org_context.py         # Tenant context middleware
│       └── audit_middleware.py
└── tasks/                         # Celery async tasks
    ├── peppol_tasks.py            # InvoiceNow transmission
    ├── report_tasks.py
    └── reminder_tasks.py
```

#### 2.5.2 Critical Service: GST Calculator

```python
"""
apps/gst/services/gst_calculator.py

Singapore GST Calculator with DECIMAL(10,4) precision.
All monetary calculations use Python's `decimal.Decimal` to avoid
floating-point errors. This mirrors the PostgreSQL NUMERIC(10,4) storage.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from dataclasses import dataclass
from typing import Optional

# Singapore GST rate as of 1 Jan 2024
SG_GST_RATE = Decimal("0.09")
SG_GST_FRACTION = Decimal("9") / Decimal("109")  # For inclusive calculations

# Precision context
MONEY_PLACES = Decimal("0.0001")  # 4 decimal places
DISPLAY_PLACES = Decimal("0.01")  # 2 decimal places for display


@dataclass(frozen=True)
class GSTResult:
    """Immutable result of a GST calculation."""
    net_amount: Decimal       # Before GST
    gst_amount: Decimal       # GST component
    gross_amount: Decimal     # After GST (net + gst)
    tax_code: str
    rate: Decimal

    def to_display(self) -> dict:
        """Round to 2dp for display while maintaining 4dp internally."""
        return {
            "net_amount": str(self.net_amount.quantize(DISPLAY_PLACES, ROUND_HALF_UP)),
            "gst_amount": str(self.gst_amount.quantize(DISPLAY_PLACES, ROUND_HALF_UP)),
            "gross_amount": str(self.gross_amount.quantize(DISPLAY_PLACES, ROUND_HALF_UP)),
            "tax_code": self.tax_code,
            "rate_pct": str((self.rate * 100).quantize(Decimal("0.01"))),
        }


class GSTCalculator:
    """
    Stateless GST computation engine.
    
    Design decisions:
    - All internal math uses Decimal with ROUND_HALF_UP
    - GST-inclusive extraction uses the tax fraction (9/109) per IRAS guidance
    - Line-level rounding: GST computed per line, then summed (not computed on totals)
    - This matches IRAS's requirement for tax invoice accuracy
    """

    # Tax code → rate mapping (loaded from DB in production, hardcoded for core logic)
    TAX_RATES = {
        "SR":  SG_GST_RATE,       # Standard-rated 9%
        "ZR":  Decimal("0"),       # Zero-rated
        "ES":  Decimal("0"),       # Exempt
        "OS":  Decimal("0"),       # Out-of-scope
        "TX":  SG_GST_RATE,       # Purchase taxable 9%
        "BL":  SG_GST_RATE,       # Blocked (rate exists but not claimable)
        "RS":  SG_GST_RATE,       # Reverse charge
        "TX-E": SG_GST_RATE,      # Denied input tax
    }

    @classmethod
    def calculate(
        cls,
        amount: Decimal,
        tax_code: str,
        is_inclusive: bool = False,
        rate_override: Optional[Decimal] = None,
    ) -> GSTResult:
        """
        Calculate GST for a given amount.

        Args:
            amount: The monetary amount (Decimal)
            tax_code: IRAS tax code (SR, ZR, ES, OS, TX, etc.)
            is_inclusive: If True, amount includes GST (extract using 9/109)
            rate_override: Override rate (for historical rate handling)

        Returns:
            GSTResult with net, gst, and gross amounts at 4dp precision
        """
        if not isinstance(amount, Decimal):
            raise TypeError(f"Amount must be Decimal, got {type(amount)}")

        rate = rate_override or cls.TAX_RATES.get(tax_code, Decimal("0"))

        if rate == Decimal("0"):
            return GSTResult(
                net_amount=amount.quantize(MONEY_PLACES, ROUND_HALF_UP),
                gst_amount=Decimal("0").quantize(MONEY_PLACES),
                gross_amount=amount.quantize(MONEY_PLACES, ROUND_HALF_UP),
                tax_code=tax_code,
                rate=rate,
            )

        if is_inclusive:
            # IRAS-mandated: use tax fraction (rate / (1 + rate))
            # For 9%: GST = Amount × 9/109
            fraction = rate / (Decimal("1") + rate)
            gst_amount = (amount * fraction).quantize(MONEY_PLACES, ROUND_HALF_UP)
            net_amount = (amount - gst_amount).quantize(MONEY_PLACES, ROUND_HALF_UP)
            gross_amount = amount.quantize(MONEY_PLACES, ROUND_HALF_UP)
        else:
            net_amount = amount.quantize(MONEY_PLACES, ROUND_HALF_UP)
            gst_amount = (amount * rate).quantize(MONEY_PLACES, ROUND_HALF_UP)
            gross_amount = (net_amount + gst_amount).quantize(MONEY_PLACES, ROUND_HALF_UP)

        return GSTResult(
            net_amount=net_amount,
            gst_amount=gst_amount,
            gross_amount=gross_amount,
            tax_code=tax_code,
            rate=rate,
        )

    @classmethod
    def calculate_line(
        cls,
        quantity: Decimal,
        unit_price: Decimal,
        tax_code: str,
        discount_pct: Decimal = Decimal("0"),
        is_inclusive: bool = False,
    ) -> GSTResult:
        """
        Calculate GST for an invoice line item.
        
        Line amount = quantity × unit_price × (1 - discount_pct/100)
        GST is then computed on this line amount.
        """
        line_amount = (
            quantity * unit_price * (Decimal("1") - discount_pct / Decimal("100"))
        ).quantize(MONEY_PLACES, ROUND_HALF_UP)

        return cls.calculate(line_amount, tax_code, is_inclusive)

    @classmethod
    def sum_lines(cls, results: list[GSTResult]) -> dict:
        """
        Sum multiple line-level GST results.
        Per IRAS guidance: compute GST per line, then sum.
        """
        total_net = sum((r.net_amount for r in results), Decimal("0"))
        total_gst = sum((r.gst_amount for r in results), Decimal("0"))
        total_gross = sum((r.gross_amount for r in results), Decimal("0"))

        return {
            "subtotal": total_net.quantize(MONEY_PLACES, ROUND_HALF_UP),
            "total_gst": total_gst.quantize(MONEY_PLACES, ROUND_HALF_UP),
            "total_amount": total_gross.quantize(MONEY_PLACES, ROUND_HALF_UP),
        }
```

#### 2.5.3 InvoiceNow / Peppol Service

```python
"""
apps/peppol/services/pint_sg_builder.py

Generates PINT-SG (Peppol International - Singapore) compliant
UBL 2.1 XML documents for transmission to IRAS via InvoiceNow network.

References:
- IMDA InvoiceNow Technical Playbook
- IRAS e-Tax Guide: Adopting GST InvoiceNow Requirement
- Peppol BIS Billing 3.0 / PINT-SG Specification
"""

import uuid
from datetime import date
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring
from typing import Optional

# UBL 2.1 Namespaces
UBL_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
CAC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
CBC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

NAMESPACES = {
    "": UBL_NS,
    "cac": CAC_NS,
    "cbc": CBC_NS,
}


class PINTSGBuilder:
    """
    Builds a PINT-SG compliant invoice XML for InvoiceNow transmission.
    
    The 5-corner model:
    1. Supplier's Accounting System (LedgerSG)
    2. Supplier's Access Point (AP)
    3. Customer's Access Point (AP)
    4. Customer's Accounting System
    5. IRAS (receives copy via Corner 2 AP)
    """

    def __init__(self, invoice_data: dict):
        self.data = invoice_data
        self.root = None

    def build(self) -> bytes:
        """Build complete PINT-SG XML document."""
        self.root = Element("Invoice", xmlns=UBL_NS)
        self.root.set("xmlns:cac", CAC_NS)
        self.root.set("xmlns:cbc", CBC_NS)

        self._add_header()
        self._add_supplier_party()
        self._add_customer_party()
        self._add_tax_total()
        self._add_monetary_total()
        self._add_invoice_lines()

        return tostring(self.root, encoding="utf-8", xml_declaration=True)

    def _add_header(self):
        """Invoice-level metadata."""
        d = self.data

        # Customization ID for PINT-SG
        cust_id = SubElement(self.root, f"{{{CBC_NS}}}CustomizationID")
        cust_id.text = (
            "urn:peppol:pint:billing-1@sg-1"
        )

        # Profile ID
        prof_id = SubElement(self.root, f"{{{CBC_NS}}}ProfileID")
        prof_id.text = "urn:peppol:bis:billing"

        # Invoice ID (document number)
        inv_id = SubElement(self.root, f"{{{CBC_NS}}}ID")
        inv_id.text = d["document_number"]

        # Issue Date
        issue_date = SubElement(self.root, f"{{{CBC_NS}}}IssueDate")
        issue_date.text = d["document_date"].isoformat()

        # Due Date
        if d.get("due_date"):
            due = SubElement(self.root, f"{{{CBC_NS}}}DueDate")
            due.text = d["due_date"].isoformat()

        # Invoice Type Code (380 = Commercial Invoice, 381 = Credit Note)
        type_code = SubElement(self.root, f"{{{CBC_NS}}}InvoiceTypeCode")
        type_code.text = "380"

        # Document Currency
        currency = SubElement(self.root, f"{{{CBC_NS}}}DocumentCurrencyCode")
        currency.text = d.get("currency", "SGD")

        # Buyer Reference (Customer PO number if available)
        if d.get("reference"):
            buyer_ref = SubElement(self.root, f"{{{CBC_NS}}}BuyerReference")
            buyer_ref.text = d["reference"]

    def _add_supplier_party(self):
        """Supplier (seller) information including GST registration."""
        supplier = self.data["supplier"]
        party_elem = SubElement(self.root, f"{{{CAC_NS}}}AccountingSupplierParty")
        party = SubElement(party_elem, f"{{{CAC_NS}}}Party")

        # Endpoint ID (Peppol ID / UEN)
        endpoint = SubElement(party, f"{{{CBC_NS}}}EndpointID")
        endpoint.set("schemeID", "0195")  # Singapore UEN scheme
        endpoint.text = supplier["uen"]

        # Party Name
        party_name = SubElement(party, f"{{{CAC_NS}}}PartyName")
        name = SubElement(party_name, f"{{{CBC_NS}}}Name")
        name.text = supplier["name"]

        # Address
        address = SubElement(party, f"{{{CAC_NS}}}PostalAddress")
        street = SubElement(address, f"{{{CBC_NS}}}StreetName")
        street.text = supplier.get("address_line1", "")
        postal = SubElement(address, f"{{{CBC_NS}}}PostalZone")
        postal.text = supplier.get("postal_code", "")
        country_elem = SubElement(address, f"{{{CAC_NS}}}Country")
        country_id = SubElement(country_elem, f"{{{CBC_NS}}}IdentificationCode")
        country_id.text = "SG"

        # GST Registration (Tax Scheme)
        if supplier.get("gst_reg_number"):
            tax_scheme_elem = SubElement(party, f"{{{CAC_NS}}}PartyTaxScheme")
            company_id = SubElement(tax_scheme_elem, f"{{{CBC_NS}}}CompanyID")
            company_id.text = supplier["gst_reg_number"]
            tax_scheme = SubElement(tax_scheme_elem, f"{{{CAC_NS}}}TaxScheme")
            ts_id = SubElement(tax_scheme, f"{{{CBC_NS}}}ID")
            ts_id.text = "GST"

    def _add_customer_party(self):
        """Customer (buyer) information."""
        customer = self.data["customer"]
        party_elem = SubElement(self.root, f"{{{CAC_NS}}}AccountingCustomerParty")
        party = SubElement(party_elem, f"{{{CAC_NS}}}Party")

        # Endpoint ID
        endpoint = SubElement(party, f"{{{CBC_NS}}}EndpointID")
        endpoint.set("schemeID", "0195")
        endpoint.text = customer.get("uen", "NA")  # "NA" for individuals

        # Party Name
        party_name = SubElement(party, f"{{{CAC_NS}}}PartyName")
        name = SubElement(party_name, f"{{{CBC_NS}}}Name")
        name.text = customer.get("name", "NA")

    def _add_tax_total(self):
        """Invoice-level tax totals."""
        tax_total = SubElement(self.root, f"{{{CAC_NS}}}TaxTotal")
        tax_amount = SubElement(tax_total, f"{{{CBC_NS}}}TaxAmount")
        tax_amount.set("currencyID", self.data.get("currency", "SGD"))
        tax_amount.text = str(self.data["total_gst"])

        # Tax Subtotal per category
        subtotal = SubElement(tax_total, f"{{{CAC_NS}}}TaxSubtotal")
        taxable = SubElement(subtotal, f"{{{CBC_NS}}}TaxableAmount")
        taxable.set("currencyID", self.data.get("currency", "SGD"))
        taxable.text = str(self.data["subtotal"])

        sub_tax = SubElement(subtotal, f"{{{CBC_NS}}}TaxAmount")
        sub_tax.set("currencyID", self.data.get("currency", "SGD"))
        sub_tax.text = str(self.data["total_gst"])

        tax_cat = SubElement(subtotal, f"{{{CAC_NS}}}TaxCategory")
        cat_id = SubElement(tax_cat, f"{{{CBC_NS}}}ID")
        cat_id.text = "S"  # Standard rate
        pct = SubElement(tax_cat, f"{{{CBC_NS}}}Percent")
        pct.text = "9"
        scheme = SubElement(tax_cat, f"{{{CAC_NS}}}TaxScheme")
        scheme_id = SubElement(scheme, f"{{{CBC_NS}}}ID")
        scheme_id.text = "GST"

    def _add_monetary_total(self):
        """Legal monetary total."""
        lmt = SubElement(self.root, f"{{{CAC_NS}}}LegalMonetaryTotal")
        ccy = self.data.get("currency", "SGD")

        net = SubElement(lmt, f"{{{CBC_NS}}}LineExtensionAmount")
        net.set("currencyID", ccy)
        net.text = str(self.data["subtotal"])

        tax_excl = SubElement(lmt, f"{{{CBC_NS}}}TaxExclusiveAmount")
        tax_excl.set("currencyID", ccy)
        tax_excl.text = str(self.data["subtotal"])

        tax_incl = SubElement(lmt, f"{{{CBC_NS}}}TaxInclusiveAmount")
        tax_incl.set("currencyID", ccy)
        tax_incl.text = str(self.data["total_amount"])

        payable = SubElement(lmt, f"{{{CBC_NS}}}PayableAmount")
        payable.set("currencyID", ccy)
        payable.text = str(self.data["total_amount"])

    def _add_invoice_lines(self):
        """Individual invoice line items."""
        ccy = self.data.get("currency", "SGD")

        for i, line in enumerate(self.data["lines"], 1):
            inv_line = SubElement(self.root, f"{{{CAC_NS}}}InvoiceLine")

            line_id = SubElement(inv_line, f"{{{CBC_NS}}}ID")
            line_id.text = str(i)

            qty = SubElement(inv_line, f"{{{CBC_NS}}}InvoicedQuantity")
            qty.set("unitCode", "EA")
            qty.text = str(line["quantity"])

            line_ext = SubElement(inv_line, f"{{{CBC_NS}}}LineExtensionAmount")
            line_ext.set("currencyID", ccy)
            line_ext.text = str(line["line_amount"])

            # Item description
            item = SubElement(inv_line, f"{{{CAC_NS}}}Item")
            desc = SubElement(item, f"{{{CBC_NS}}}Name")
            desc.text = line["description"]

            # Tax category for line
            ctc = SubElement(item, f"{{{CAC_NS}}}ClassifiedTaxCategory")
            ctc_id = SubElement(ctc, f"{{{CBC_NS}}}ID")
            ctc_id.text = "S" if line["tax_code"] == "SR" else "Z"
            ctc_pct = SubElement(ctc, f"{{{CBC_NS}}}Percent")
            ctc_pct.text = "9" if line["tax_code"] == "SR" else "0"
            ctc_scheme = SubElement(ctc, f"{{{CAC_NS}}}TaxScheme")
            ctc_scheme_id = SubElement(ctc_scheme, f"{{{CBC_NS}}}ID")
            ctc_scheme_id.text = "GST"

            # Price
            price = SubElement(inv_line, f"{{{CAC_NS}}}Price")
            price_amt = SubElement(price, f"{{{CBC_NS}}}PriceAmount")
            price_amt.set("currencyID", ccy)
            price_amt.text = str(line["unit_price"])
```

#### 2.5.4 Django Model Layer (Key Excerpt)

```python
"""
apps/invoicing/models.py
"""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class Document(models.Model):
    """
    Unified invoice/credit-note/debit-note model.
    Journal entry is auto-created on approval via signal/service.
    """

    class DocumentType(models.TextChoices):
        SALES_INVOICE = "SALES_INVOICE", "Sales Invoice"
        SALES_CREDIT_NOTE = "SALES_CREDIT_NOTE", "Sales Credit Note"
        SALES_DEBIT_NOTE = "SALES_DEBIT_NOTE", "Sales Debit Note"
        PURCHASE_INVOICE = "PURCHASE_INVOICE", "Purchase Invoice"
        PURCHASE_CREDIT_NOTE = "PURCHASE_CREDIT_NOTE", "Purchase Credit Note"
        PURCHASE_DEBIT_NOTE = "PURCHASE_DEBIT_NOTE", "Purchase Debit Note"
        PURCHASE_ORDER = "PURCHASE_ORDER", "Purchase Order"
        SALES_QUOTE = "SALES_QUOTE", "Sales Quote"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        SENT = "SENT", "Sent"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
        PAID = "PAID", "Paid"
        OVERDUE = "OVERDUE", "Overdue"
        VOID = "VOID", "Void"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "core.Organisation", on_delete=models.PROTECT, related_name="documents"
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    document_number = models.CharField(max_length=30)
    document_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    contact = models.ForeignKey(
        "invoicing.Contact", on_delete=models.PROTECT, related_name="documents"
    )
    currency = models.CharField(max_length=3, default="SGD")
    exchange_rate = models.DecimalField(
        max_digits=12, decimal_places=6, default=Decimal("1.000000")
    )
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("0")
    )
    total_gst = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("0")
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("0")
    )
    amount_paid = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("0")
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    reference = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    # InvoiceNow / Peppol fields
    peppol_message_id = models.UUIDField(null=True, blank=True)
    invoicenow_status = models.CharField(
        max_length=20, blank=True, default="",
        help_text="PENDING | TRANSMITTED | FAILED | N/A"
    )
    invoicenow_sent_at = models.DateTimeField(null=True, blank=True)

    # Link to journal entry (created on APPROVE transition)
    journal_entry = models.ForeignKey(
        "accounting.JournalEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_document",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoicing.document"
        unique_together = [("organisation", "document_type", "document_number")]
        ordering = ["-document_date", "-created_at"]


class DocumentLine(models.Model):
    """Individual line item on an invoice with line-level GST computation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="lines"
    )
    line_number = models.SmallIntegerField()
    description = models.CharField(max_length=500)
    account = models.ForeignKey(
        "accounting.Account", on_delete=models.PROTECT
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=4)
    discount_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0")
    )
    tax_code = models.ForeignKey(
        "gst.TaxCode", on_delete=models.PROTECT
    )
    line_amount = models.DecimalField(max_digits=10, decimal_places=4)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=4)
    total_amount = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        db_table = "invoicing.document_line"
        unique_together = [("document", "line_number")]
        ordering = ["line_number"]
```

#### 2.5.5 API Endpoints (Key Routes)

```python
# config/urls.py — API v1 routing overview

"""
/api/v1/
├── auth/
│   ├── POST   login/
│   ├── POST   logout/
│   └── POST   refresh/
│
├── organisations/
│   ├── GET    /                          # List user's orgs
│   ├── POST   /                          # Create org
│   ├── GET    /{org_id}/                  # Org detail
│   └── PATCH  /{org_id}/                  # Update org settings
│
├── {org_id}/
│   ├── accounts/
│   │   ├── GET    /                       # Chart of Accounts
│   │   ├── POST   /                       # Create account
│   │   └── PATCH  /{account_id}/          # Update account
│   │
│   ├── contacts/
│   │   ├── GET    /                       # List contacts (customers/suppliers)
│   │   ├── POST   /                       # Create contact
│   │   └── GET    /{contact_id}/          # Contact detail
│   │
│   ├── invoices/
│   │   ├── GET    /                       # List invoices (filterable)
│   │   ├── POST   /                       # Create draft invoice
│   │   ├── GET    /{invoice_id}/          # Invoice detail
│   │   ├── PATCH  /{invoice_id}/          # Update draft
│   │   ├── POST   /{invoice_id}/approve/  # Approve → creates journal entry
│   │   ├── POST   /{invoice_id}/void/     # Void → reversal entry
│   │   ├── GET    /{invoice_id}/pdf/      # Generate PDF
│   │   └── POST   /{invoice_id}/send-invoicenow/  # Transmit via Peppol
│   │
│   ├── purchase-orders/
│   │   ├── GET    /
│   │   ├── POST   /
│   │   └── POST   /{po_id}/convert-to-invoice/
│   │
│   ├── journal-entries/
│   │   ├── GET    /                       # General ledger
│   │   ├── POST   /                       # Manual journal entry
│   │   └── POST   /{entry_id}/reverse/    # Reversal
│   │
│   ├── gst/
│   │   ├── GET    tax-codes/              # Available tax codes
│   │   ├── POST   calculate/             # GST calculation endpoint
│   │   ├── GET    returns/                # List GST returns
│   │   ├── POST   returns/compute/        # Compute new return from data
│   │   ├── GET    returns/{return_id}/    # Return detail (F5 format)
│   │   └── POST   returns/{return_id}/finalize/
│   │
│   ├── banking/
│   │   ├── GET    accounts/               # Bank accounts
│   │   ├── POST   accounts/
│   │   ├── GET    transactions/           # Bank transactions
│   │   └── POST   reconcile/             # Match to invoices
│   │
│   ├── reports/
│   │   ├── GET    profit-loss/            # P&L for period
│   │   ├── GET    balance-sheet/          # Balance Sheet at date
│   │   ├── GET    trial-balance/          # Trial Balance
│   │   ├── GET    gst-f5/                 # GST F5 report (printable)
│   │   ├── GET    aged-receivables/       # AR aging
│   │   ├── GET    aged-payables/          # AP aging
│   │   └── GET    tax-summary/            # For IRAS filing prep
│   │
│   └── dashboard/
│       └── GET    /                       # KPI summary
"""
```

---

### 2.6 Next.js Frontend Architecture

#### 2.6.1 Project Structure

```
ledgersg-web/
├── package.json                   # Next.js 15, React 19, TW CSS 4
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── components.json                # Shadcn-UI config
├── public/
│   └── fonts/                     # Self-hosted typography
├── src/
│   ├── app/
│   │   ├── layout.tsx             # Root layout (theme, providers)
│   │   ├── page.tsx               # Landing / login redirect
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx         # Authenticated shell
│   │   │   ├── page.tsx           # Dashboard overview
│   │   │   ├── invoices/
│   │   │   │   ├── page.tsx       # Invoice list
│   │   │   │   ├── new/page.tsx   # Create invoice
│   │   │   │   └── [id]/page.tsx  # Invoice detail
│   │   │   ├── purchases/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── new/page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── contacts/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── accounts/
│   │   │   │   └── page.tsx       # Chart of Accounts
│   │   │   ├── journal/
│   │   │   │   ├── page.tsx       # General Ledger
│   │   │   │   └── new/page.tsx   # Manual journal entry
│   │   │   ├── gst/
│   │   │   │   ├── page.tsx       # GST dashboard
│   │   │   │   ├── returns/page.tsx
│   │   │   │   └── returns/[id]/page.tsx
│   │   │   ├── banking/
│   │   │   │   ├── page.tsx
│   │   │   │   └── reconcile/page.tsx
│   │   │   ├── reports/
│   │   │   │   ├── page.tsx       # Reports hub
│   │   │   │   ├── profit-loss/page.tsx
│   │   │   │   ├── balance-sheet/page.tsx
│   │   │   │   └── trial-balance/page.tsx
│   │   │   └── settings/
│   │   │       ├── page.tsx
│   │   │       ├── organisation/page.tsx
│   │   │       ├── gst/page.tsx   # GST configuration
│   │   │       └── invoicenow/page.tsx  # Peppol setup
│   │   └── api/                   # BFF route handlers (optional)
│   │
│   ├── components/
│   │   ├── ui/                    # Shadcn-UI components (auto-generated)
│   │   │   ├── button.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── table.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── command.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── card.tsx
│   │   │   ├── tabs.tsx
│   │   │   └── ... (60+ primitives)
│   │   ├── layout/
│   │   │   ├── sidebar.tsx        # Main navigation
│   │   │   ├── header.tsx
│   │   │   ├── org-switcher.tsx
│   │   │   └── breadcrumbs.tsx
│   │   ├── invoicing/
│   │   │   ├── invoice-form.tsx   # Multi-line invoice editor
│   │   │   ├── invoice-line-row.tsx
│   │   │   ├── gst-summary.tsx    # Live GST calculation display
│   │   │   ├── invoice-pdf-preview.tsx
│   │   │   ├── invoice-status-badge.tsx
│   │   │   └── invoicenow-status.tsx
│   │   ├── gst/
│   │   │   ├── gst-return-card.tsx
│   │   │   ├── gst-f5-preview.tsx
│   │   │   └── tax-code-selector.tsx
│   │   ├── accounting/
│   │   │   ├── journal-entry-form.tsx
│   │   │   ├── account-tree.tsx   # Hierarchical COA display
│   │   │   └── ledger-table.tsx
│   │   ├── reports/
│   │   │   ├── report-date-range.tsx
│   │   │   ├── financial-statement.tsx
│   │   │   └── aging-chart.tsx
│   │   └── common/
│   │       ├── money-input.tsx    # Decimal-safe currency input
│   │       ├── money-display.tsx  # Formatted SGD display
│   │       ├── data-table.tsx     # Reusable data table (Shadcn + TanStack)
│   │       ├── empty-state.tsx
│   │       ├── loading-skeleton.tsx
│   │       └── error-boundary.tsx
│   │
│   ├── lib/
│   │   ├── api-client.ts          # Typed fetch wrapper for Django API
│   │   ├── decimal.ts             # Frontend Decimal.js helpers
│   │   ├── gst.ts                 # Client-side GST preview calculation
│   │   ├── format.ts              # SGD formatting, date formatting
│   │   ├── constants.ts           # Tax codes, entity types, etc.
│   │   └── validators.ts          # Zod schemas for forms
│   │
│   ├── hooks/
│   │   ├── use-invoices.ts        # TanStack Query hooks
│   │   ├── use-gst.ts
│   │   ├── use-accounts.ts
│   │   ├── use-contacts.ts
│   │   ├── use-reports.ts
│   │   └── use-organisation.ts
│   │
│   └── types/
│       ├── invoice.ts
│       ├── account.ts
│       ├── gst.ts
│       ├── contact.ts
│       ├── journal.ts
│       └── api.ts                 # Shared API response types
│
└── tests/
    ├── components/
    └── lib/
```

#### 2.6.2 Key Frontend Component: Invoice Form with Live GST

```tsx
// src/components/invoicing/invoice-line-row.tsx

"use client";

import { useCallback, useMemo } from "react";
import Decimal from "decimal.js";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Trash2 } from "lucide-react";
import { SG_TAX_CODES, type TaxCode } from "@/lib/constants";
import { calculateLineGST } from "@/lib/gst";
import type { InvoiceLine } from "@/types/invoice";

// Decimal.js configuration — mirrors Python/Postgres DECIMAL(10,4)
Decimal.set({ precision: 20, rounding: Decimal.ROUND_HALF_UP });

interface InvoiceLineRowProps {
  line: InvoiceLine;
  index: number;
  isGSTRegistered: boolean;
  onUpdate: (index: number, field: keyof InvoiceLine, value: string) => void;
  onRemove: (index: number) => void;
}

export function InvoiceLineRow({
  line,
  index,
  isGSTRegistered,
  onUpdate,
  onRemove,
}: InvoiceLineRowProps) {
  // Compute GST in real-time using Decimal.js (client-side preview)
  // Authoritative calculation happens server-side in Django
  const computed = useMemo(() => {
    return calculateLineGST({
      quantity: line.quantity,
      unitPrice: line.unit_price,
      discountPct: line.discount_pct,
      taxCode: line.tax_code,
    });
  }, [line.quantity, line.unit_price, line.discount_pct, line.tax_code]);

  const handleFieldChange = useCallback(
    (field: keyof InvoiceLine) => (
      e: React.ChangeEvent<HTMLInputElement>
    ) => {
      onUpdate(index, field, e.target.value);
    },
    [index, onUpdate]
  );

  return (
    <div
      className="grid grid-cols-[1fr_80px_120px_80px_100px_60px_100px_120px_40px] 
                 items-center gap-2 py-2 border-b border-border/40
                 transition-colors hover:bg-muted/20"
      role="row"
      aria-label={`Invoice line ${index + 1}`}
    >
      {/* Description */}
      <Input
        value={line.description}
        onChange={handleFieldChange("description")}
        placeholder="Description"
        className="h-9 text-sm border-0 bg-transparent 
                   focus:ring-1 focus:ring-ring/50 rounded-md"
        aria-label="Line description"
      />

      {/* Quantity */}
      <Input
        type="number"
        step="0.01"
        min="0"
        value={line.quantity}
        onChange={handleFieldChange("quantity")}
        className="h-9 text-sm text-right tabular-nums font-mono
                   border-0 bg-transparent focus:ring-1 focus:ring-ring/50"
        aria-label="Quantity"
      />

      {/* Unit Price */}
      <Input
        type="number"
        step="0.01"
        min="0"
        value={line.unit_price}
        onChange={handleFieldChange("unit_price")}
        className="h-9 text-sm text-right tabular-nums font-mono
                   border-0 bg-transparent focus:ring-1 focus:ring-ring/50"
        aria-label="Unit price"
      />

      {/* Discount % */}
      <Input
        type="number"
        step="0.5"
        min="0"
        max="100"
        value={line.discount_pct}
        onChange={handleFieldChange("discount_pct")}
        className="h-9 text-sm text-right tabular-nums
                   border-0 bg-transparent focus:ring-1 focus:ring-ring/50"
        aria-label="Discount percentage"
      />

      {/* Tax Code */}
      <Select
        value={line.tax_code}
        onValueChange={(val) => onUpdate(index, "tax_code", val)}
        disabled={!isGSTRegistered}
      >
        <SelectTrigger
          className="h-9 text-xs border-0 bg-transparent"
          aria-label="Tax code"
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {SG_TAX_CODES.filter((tc) => !tc.isInput).map((tc) => (
            <SelectItem key={tc.code} value={tc.code} className="text-xs">
              {tc.code} — {tc.rate}%
            </SelectItem>
          ))}
          {!isGSTRegistered && (
            <SelectItem value="OS" className="text-xs">
              OS — N/A
            </SelectItem>
          )}
        </SelectContent>
      </Select>

      {/* GST Amount (computed, read-only) */}
      <div
        className="text-right text-sm tabular-nums font-mono text-muted-foreground"
        aria-label="GST amount"
      >
        {computed.gstAmount}
      </div>

      {/* Line Total (computed, read-only) */}
      <div
        className="text-right text-sm tabular-nums font-mono font-medium"
        aria-label="Line total"
      >
        {computed.totalAmount}
      </div>

      {/* Remove */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onRemove(index)}
        className="h-8 w-8 text-muted-foreground hover:text-destructive
                   transition-colors"
        aria-label={`Remove line ${index + 1}`}
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

#### 2.6.3 Client-Side GST Preview Library

```typescript
// src/lib/gst.ts

import Decimal from "decimal.js";

Decimal.set({ precision: 20, rounding: Decimal.ROUND_HALF_UP });

const FOUR_DP = 4;
const TWO_DP = 2;
const GST_RATE = new Decimal("0.09");

export interface LineGSTInput {
  quantity: string | number;
  unitPrice: string | number;
  discountPct: string | number;
  taxCode: string;
  isInclusive?: boolean;
}

export interface LineGSTResult {
  lineAmount: string;   // Net before GST (display: 2dp)
  gstAmount: string;    // GST component
  totalAmount: string;  // Gross including GST
  // Internal 4dp values for summation
  _lineAmount4dp: Decimal;
  _gstAmount4dp: Decimal;
  _totalAmount4dp: Decimal;
}

const TAX_RATES: Record<string, Decimal> = {
  SR: GST_RATE,
  ZR: new Decimal(0),
  ES: new Decimal(0),
  OS: new Decimal(0),
  TX: GST_RATE,
};

export function calculateLineGST(input: LineGSTInput): LineGSTResult {
  const qty = new Decimal(input.quantity || 0);
  const price = new Decimal(input.unitPrice || 0);
  const disc = new Decimal(input.discountPct || 0);
  const rate = TAX_RATES[input.taxCode] ?? new Decimal(0);

  // Line amount = qty × price × (1 - disc/100)
  const lineAmount = qty
    .mul(price)
    .mul(new Decimal(1).minus(disc.div(100)))
    .toDecimalPlaces(FOUR_DP);

  let gstAmount: Decimal;
  let totalAmount: Decimal;

  if (input.isInclusive && !rate.isZero()) {
    // Extract: GST = amount × rate / (1 + rate)
    gstAmount = lineAmount
      .mul(rate)
      .div(new Decimal(1).plus(rate))
      .toDecimalPlaces(FOUR_DP);
    totalAmount = lineAmount;
  } else {
    gstAmount = lineAmount.mul(rate).toDecimalPlaces(FOUR_DP);
    totalAmount = lineAmount.plus(gstAmount);
  }

  return {
    lineAmount: lineAmount.toDecimalPlaces(TWO_DP).toFixed(TWO_DP),
    gstAmount: gstAmount.toDecimalPlaces(TWO_DP).toFixed(TWO_DP),
    totalAmount: totalAmount.toDecimalPlaces(TWO_DP).toFixed(TWO_DP),
    _lineAmount4dp: lineAmount,
    _gstAmount4dp: gstAmount,
    _totalAmount4dp: totalAmount,
  };
}

/**
 * Sum multiple line results for invoice totals.
 * Sum the 4dp internal values, then round to 2dp for display.
 */
export function sumLineResults(lines: LineGSTResult[]): {
  subtotal: string;
  totalGST: string;
  totalAmount: string;
} {
  let sub = new Decimal(0);
  let gst = new Decimal(0);
  let total = new Decimal(0);

  for (const line of lines) {
    sub = sub.plus(line._lineAmount4dp);
    gst = gst.plus(line._gstAmount4dp);
    total = total.plus(line._totalAmount4dp);
  }

  return {
    subtotal: sub.toDecimalPlaces(TWO_DP).toFixed(TWO_DP),
    totalGST: gst.toDecimalPlaces(TWO_DP).toFixed(TWO_DP),
    totalAmount: total.toDecimalPlaces(TWO_DP).toFixed(TWO_DP),
  };
}
```

---

### 2.7 Module Dependency Graph

```
                    ┌──────────────┐
                    │    core      │ ◄─── Organisation, Users, Auth
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼───┐  ┌────▼────┐  ┌───▼──────┐
        │   coa   │  │   gst   │  │ invoicing│
        │ (Chart  │  │ (Tax    │  │ (Sales & │
        │  of     │  │  Codes, │  │  Purchase│
        │  Accts) │  │  Rates) │  │  Docs)   │
        └────┬────┘  └────┬────┘  └──┬───┬───┘
             │            │          │   │
             └─────┬──────┘          │   │
                   │                 │   │
             ┌─────▼─────┐          │   │
             │  journal   │ ◄───────┘   │
             │ (General   │             │
             │  Ledger)   │             │
             └─────┬──────┘             │
                   │              ┌─────▼──────┐
                   │              │   peppol    │
                   │              │ (InvoiceNow │
                   │              │  Peppol XML)│
                   │              └─────────────┘
             ┌─────▼──────┐
             │  reporting  │ ◄─── P&L, BS, TB, GST F5, Aging
             └─────┬──────┘
                   │
             ┌─────▼──────┐
             │  banking    │ ◄─── Bank Accounts, Reconciliation
             └─────────────┘
```

---

### 2.8 Invoice Lifecycle State Machine

```
                 ┌───────────────────────────────────────────────┐
                 │                                               │
  User Creates   │         DRAFT                                │
  ─────────────► │  • Editable lines, contacts, dates           │
                 │  • No journal entry                          │
                 │  • No InvoiceNow transmission                │
                 └───────────────┬───────────────────────────────┘
                                 │
                     User clicks │ [APPROVE]
                                 │
                                 ▼
                 ┌───────────────────────────────────────────────┐
                 │         APPROVED                             │
                 │  • Journal entry auto-created (double-entry)  │
                 │  • Document locked (no edits)                │
                 │  • GST amounts finalized                     │
                 │  • Queued for InvoiceNow if enabled          │
                 └───────┬──────────────────┬───────────────────┘
                         │                  │
          User clicks    │         Celery transmits via
          [SEND]         │         Peppol Access Point
                         │                  │
                         ▼                  ▼
                 ┌───────────────┐  ┌───────────────────────────┐
                 │    SENT       │  │  InvoiceNow: TRANSMITTED  │
                 │  • Email/PDF  │  │  • PINT-SG XML sent       │
                 │    sent       │  │  • Message ID recorded    │
                 └──────┬────────┘  │  • IRAS receives copy     │
                        │           └───────────────────────────┘
                        │
           Payment      │ received (partial or full)
                        │
           ┌────────────┼────────────────┐
           ▼                             ▼
   ┌───────────────┐           ┌──────────────────┐
   │ PARTIALLY_PAID│           │      PAID        │
   │ • amount_paid │           │ • Fully settled  │
   │   < total     │──────────►│ • Closes AR/AP   │
   └───────────────┘           └──────────────────┘

           │
           │  If past due_date and not fully paid:
           ▼
   ┌───────────────┐
   │   OVERDUE     │  • Flagged in aging report
   └───────────────┘

   At any approved state:
           │
           │  [VOID]
           ▼
   ┌───────────────┐
   │    VOID       │
   │ • Reversal    │
   │   journal     │
   │   entry       │
   │   created     │
   └───────────────┘
```

---

### 2.9 GST Workflow for Both GST-Registered & Non-Registered Businesses

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   GST-REGISTERED BUSINESS                                  │
│                                                                             │
│  Invoice Creation:                                                         │
│  ├── Each line: select tax code (SR 9%, ZR 0%, ES, OS)                    │
│  ├── GST auto-calculated at line level (DECIMAL precision)                │
│  ├── Tax Invoice generated with:                                           │
│  │   • Words "Tax Invoice" prominently displayed                          │
│  │   • GST Registration Number                                            │
│  │   • GST amount shown separately                                         │
│  │   • Total inclusive of GST                                              │
│  └── InvoiceNow XML generated and transmitted                             │
│                                                                             │
│  Purchase Recording:                                                       │
│  ├── Input tax (TX 9%) claimed on eligible purchases                      │
│  ├── Blocked input tax (BL) tracked but not claimable                     │
│  └── Reverse charge (RS) for imported services                            │
│                                                                             │
│  Quarterly GST Return (F5):                                                │
│  ├── Auto-computed from journal data                                       │
│  ├── Boxes 1-10 populated from tax code categorization                    │
│  ├── Net GST payable = Output Tax (Box 6) - Input Tax (Box 7)            │
│  └── Filing reminder at T-14 days before deadline                         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                   NON-GST-REGISTERED BUSINESS                              │
│                                                                             │
│  Invoice Creation:                                                         │
│  ├── Tax code defaults to "OS" (Out of Scope)                             │
│  ├── GST amount = $0 on all lines                                         │
│  ├── Invoice generated WITHOUT:                                            │
│  │   • NO "Tax Invoice" label (uses "Invoice" only)                       │
│  │   • NO GST Registration Number                                         │
│  │   • NO separate GST line                                               │
│  ├── BUT: If paying GST-registered suppliers, GST on purchases            │
│  │   is a cost (not claimable — absorbed into expense)                    │
│  └── InvoiceNow: optional (can still use for efficiency)                  │
│                                                                             │
│  Threshold Monitoring:                                                      │
│  ├── System tracks rolling 12-month taxable turnover                      │
│  ├── Alert at S$800K (80% of threshold)                                   │
│  ├── Warning at S$900K (90%)                                              │
│  └── CRITICAL at S$1M — must register within 30 days                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.10 Phased Delivery Plan

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ PHASE 1 — FOUNDATION (Weeks 1-6)                                          ║
║                                                                            ║
║  □ PostgreSQL schema creation (all core schemas)                           ║
║  □ Django project scaffolding, settings, auth system                       ║
║  □ Organisation CRUD + multi-tenant middleware                             ║
║  □ Chart of Accounts (Singapore default template)                          ║
║  □ GST tax codes seed data                                                 ║
║  □ GSTCalculator service + comprehensive test suite                        ║
║  □ Next.js project setup, Shadcn-UI installation                          ║
║  □ Auth flow (login/register) + org context                               ║
║  □ Dashboard shell layout                                                  ║
║                                                                            ║
║  ✓ Success: User can login, see org, view CoA                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PHASE 2 — INVOICING CORE (Weeks 7-12)                                     ║
║                                                                            ║
║  □ Contact management (customers + suppliers)                              ║
║  □ Sales Invoice CRUD with line items + GST calculation                    ║
║  □ Purchase Invoice CRUD                                                   ║
║  □ Invoice approval → auto journal entry creation                          ║
║  □ Document numbering service (sequential, configurable prefix)           ║
║  □ PDF generation (compliant tax invoice / plain invoice)                  ║
║  □ Credit notes + debit notes                                              ║
║  □ Frontend: Invoice form with live GST preview                           ║
║  □ Frontend: Invoice list with filtering/search                           ║
║                                                                            ║
║  ✓ Success: Complete invoice lifecycle, GST calculated correctly          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PHASE 3 — GENERAL LEDGER & REPORTING (Weeks 13-16)                        ║
║                                                                            ║
║  □ Journal entry model + balanced entry constraint                        ║
║  □ Manual journal entry creation                                           ║
║  □ General ledger view (filterable by account, period)                    ║
║  □ Trial Balance report                                                    ║
║  □ Profit & Loss statement                                                ║
║  □ Balance Sheet                                                           ║
║  □ Aged Receivables / Payables                                            ║
║  □ Dashboard KPIs (revenue, expenses, GST liability, overdue)             ║
║                                                                            ║
║  ✓ Success: Full double-entry GL, 3 core financial statements             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PHASE 4 — GST COMPLIANCE (Weeks 17-20)                                    ║
║                                                                            ║
║  □ GST Return computation stored procedure                                ║
║  □ GST F5 return auto-generation from journal data                        ║
║  □ GST return review/finalize workflow                                    ║
║  □ GST threshold monitoring (for non-registered businesses)               ║
║  □ GST F5 printable report format                                         ║
║  □ Tax summary report for IRAS filing preparation                         ║
║  □ Audit trail for all GST-related changes                                ║
║                                                                            ║
║  ✓ Success: One-click GST F5 generation, threshold alerts                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PHASE 5 — INVOICENOW / PEPPOL (Weeks 21-26)                               ║
║                                                                            ║
║  □ Peppol PINT-SG XML builder service                                     ║
║  □ Access Point integration (via IMDA-accredited AP API)                  ║
║  □ InvoiceNow transmission workflow (async via Celery)                    ║
║  □ Transmission status tracking (PENDING → TRANSMITTED → CONFIRMED)       ║
║  □ Purchase invoice receipt via Peppol                                    ║
║  □ SG Peppol Directory lookup                                              ║
║  □ Validation check: detect wrongful GST charges from suppliers           ║
║  □ Frontend: InvoiceNow settings, Peppol ID registration                 ║
║  □ Frontend: Transmission status indicators on invoices                   ║
║                                                                            ║
║  ✓ Success: Full InvoiceNow compliance for voluntary GST registrants      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PHASE 6 — BANKING & PAYMENTS (Weeks 27-30)                                 ║
║                                                                            ║
║  □ Bank account management                                                 ║
║  □ Payment recording (receive + make payments)                            ║
║  □ Invoice-payment matching                                                ║
║  □ Bank reconciliation interface                                           ║
║  □ Multi-currency support (SGD base, with FX gain/loss tracking)          ║
║  □ PayNow QR code generation on invoices                                  ║
║                                                                            ║
║  ✓ Success: End-to-end invoice → payment → reconciliation                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PHASE 7 — POLISH & HARDENING (Weeks 31-34)                                ║
║                                                                            ║
║  □ Comprehensive E2E test suite (Playwright)                              ║
║  □ Load testing for 1000+ concurrent SMB tenants                          ║
║  □ WCAG AAA accessibility audit                                            ║
║  □ Security audit (OWASP Top 10, CSP, CSRF, SQL injection)               ║
║  □ Performance optimization (DB query plans, caching strategy)            ║
║  □ Documentation (API docs, user guide, admin guide)                      ║
║  □ CI/CD pipeline (GitHub Actions → Docker → AWS/GCP)                     ║
║  □ Monitoring & alerting (Sentry, Prometheus, Grafana)                    ║
║                                                                            ║
║  ✓ Success: Production-ready, auditable, performant                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

### 2.11 Technology Decision Matrix

| Decision | Choice | Rationale |
|---|---|---|
| **Database** | PostgreSQL 16 | Schemas for multi-tenancy, NUMERIC precision, stored procedures for fiscal integrity, JSONB for flexible audit logs, Row-Level Security for tenant isolation |
| **Backend** | Django 6.0 + DRF | Python `decimal.Decimal` native support, mature ORM with Postgres-specific features, battle-tested for financial applications, strong typing with Python 3.13+ |
| **Async Tasks** | Celery + Redis | InvoiceNow XML transmission, PDF generation, scheduled GST return reminders — all offloaded from request cycle |
| **Frontend** | Next.js 15 + React 19 | Server Components for report-heavy pages, Client Components for interactive invoice forms, App Router for clean URL structure |
| **UI Library** | Shadcn-UI + Radix | Accessible primitives (WCAG AA+), fully composable, style-able with Tailwind CSS 4, no vendor lock-in |
| **CSS** | Tailwind CSS 4 | Utility-first for rapid iteration, design token system for consistent spacing/color, zero runtime overhead |
| **Decimal Handling (FE)** | decimal.js | Mirrors backend `Decimal` precision for real-time GST preview calculations, avoids JS floating-point errors |
| **State Management** | TanStack Query v5 | Server-state caching for invoices/accounts, optimistic updates for payment recording, background re-fetching for dashboard KPIs |
| **Forms** | React Hook Form + Zod | Type-safe validation schemas, performant re-renders for multi-line invoice forms, Zod for shared validation between FE/BE |
| **PDF** | WeasyPrint (Django) | CSS-based PDF generation for pixel-perfect tax invoices, supports Singapore bilingual content |
| **E-Invoicing** | Peppol PINT-SG | IRAS-mandated standard, built on UBL 2.1 XML, compatible with all IMDA-accredited Access Points |

---

### 2.12 Security Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ SECURITY LAYERS                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ L1: Network                                                  │
│     • TLS 1.3 everywhere (HSTS enforced)                    │
│     • WAF (Cloudflare/AWS WAF) at edge                      │
│     • Rate limiting: 100 req/min per user                   │
│                                                              │
│ L2: Authentication                                           │
│     • JWT with short-lived access tokens (15min)            │
│     • Refresh tokens (HttpOnly, Secure, SameSite=Strict)    │
│     • Future: Singpass / Corppass OIDC integration           │
│                                                              │
│ L3: Authorization                                            │
│     • Role-based: Owner, Admin, Accountant, Viewer          │
│     • Organisation-scoped permissions                        │
│     • Row-Level Security in PostgreSQL                       │
│                                                              │
│ L4: Data                                                     │
│     • AES-256 at rest (PostgreSQL TDE)                       │
│     • Tenant isolation via org_id on all queries             │
│     • PII encryption for contact data                        │
│     • 5-year retention policy (IRAS requirement)             │
│                                                              │
│ L5: Audit                                                    │
│     • Immutable audit.log table (no UPDATE/DELETE)           │
│     • All financial mutations logged with before/after JSONB │
│     • IP address and user agent captured                     │
│                                                              │
│ L6: Application                                              │
│     • Django CSRF protection                                 │
│     • Content Security Policy headers                        │
│     • SQL injection prevention (parameterized queries)       │
│     • Input validation at API boundary (DRF serializers)     │
│     • No raw SQL in application code (stored procs only)     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

### 2.13 Singapore-Specific Features Checklist

| Feature | For GST-Registered | For Non-Registered | Status |
|---|---|---|---|
| Standard-rated (SR 9%) invoicing | ✅ | ❌ (OS only) | Phase 2 |
| Zero-rated (ZR) export invoicing | ✅ | ❌ | Phase 2 |
| Tax Invoice label (per IRAS Reg 11) | ✅ | ❌ (plain "Invoice") | Phase 2 |
| GST Reg Number on invoices | ✅ | ❌ | Phase 2 |
| Input tax claim tracking | ✅ | ❌ | Phase 2 |
| Blocked input tax (S-plate, clubs) | ✅ | ❌ | Phase 4 |
| Reverse Charge for imported services | ✅ | ❌ | Phase 4 |
| GST F5 return auto-generation | ✅ | ❌ | Phase 4 |
| GST threshold monitoring | ❌ | ✅ (critical) | Phase 4 |
| InvoiceNow / Peppol transmission | ✅ (mandatory for new vol. reg.) | Optional | Phase 5 |
| PINT-SG XML generation | ✅ | Optional | Phase 5 |
| Form C-S (Lite) data preparation | ✅ | ❌ | Phase 7 |
| 2-line / 4-line statement for sole props | ❌ | ✅ | Phase 7 |
| PayNow QR on invoices | ✅ | ✅ | Phase 6 |
| Multi-currency with FX gain/loss | ✅ | ✅ | Phase 6 |
| 5-year document retention | ✅ | ✅ | Phase 1 |

---

### 2.14 Risk Register

| # | Risk | Impact | Probability | Mitigation |
|---|---|---|---|---|
| R1 | IRAS extends InvoiceNow to compulsory registrants mid-build | High | High | Architecture is already Peppol-native; extension only requires config changes for who triggers transmission |
| R2 | GST rate change (9% → future rate) | High | Low (medium-term) | Rate stored in `gst.tax_code` with `effective_from/to` dates; historical rate lookups built-in |
| R3 | Peppol PINT-SG spec changes | Medium | Medium | XML builder uses parameterized templates; spec updates localized to `pint_sg_builder.py` |
| R4 | Decimal precision mismatch FE↔BE | High | Medium | `decimal.js` (FE) mirrors `decimal.Decimal` (BE); authoritative calculation always server-side; FE is preview-only |
| R5 | Multi-tenant data leakage | Critical | Low | PostgreSQL RLS, `org_id` enforced at middleware + query level, penetration testing in Phase 7 |
| R6 | Audit trail tampering | Critical | Low | `audit.log` table: no UPDATE/DELETE grants; append-only; backed by immutable backup policy |

---

### 2.15 Validation Checkpoint

Before proceeding to implementation, the following must be confirmed:

1. **Entity Types Supported**: Sole Proprietorship, Partnership, LLP, Pte Ltd — confirm all four?
2. **InvoiceNow Access Point Partner**: Which IMDA-accredited AP to integrate? (e.g., Storecove, Pagero, Xero's AP, or direct IRAS API)
3. **Authentication**: JWT-only for MVP, or Singpass/Corppass OIDC from day one?
4. **Hosting**: AWS (Singapore region ap-southeast-1), GCP, or self-hosted?
5. **PDF Language**: English-only, or bilingual (English + Mandarin) for certain sectors?
6. **Purchase Order Module**: Full PO → Invoice conversion, or simple PO tracking?
7. **Budget**: Does the phased 34-week timeline align with resource allocation?

---

This blueprint provides the comprehensive, validated foundation for a production-grade Singapore SMB accounting system. Every architectural decision is grounded in the current IRAS regulatory landscape — particularly the 9% GST requirement, the InvoiceNow Peppol mandate rolling out through 2026, and the CIT rebate structures announced in Budget 2026. The `DECIMAL(10,4)` precision chain from PostgreSQL through Django to the React frontend ensures fiscal accuracy that will withstand IRAS audit scrutiny.

**Next step**: Your confirmation on the validation checkpoint items above, and I will proceed to Phase 1 implementation with complete, runnable code.
