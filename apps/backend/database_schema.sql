-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║                                                                            ║
-- ║   LEDGERSG — COMPLETE POSTGRESQL 16 DATABASE SCHEMA                        ║
-- ║   Enterprise-Grade Accounting Software for Singapore SMBs                  ║
-- ║                                                                            ║
-- ║   Version:    1.0.0                                                        ║
-- ║   DB Engine:  PostgreSQL 16+                                               ║
-- ║   Precision:  NUMERIC(10,4) for all monetary values                        ║
-- ║   Encoding:   UTF-8                                                        ║
-- ║   Collation:  en_SG.UTF-8 (Singapore English)                              ║
-- ║                                                                            ║
-- ║   Design Decisions:                                                        ║
-- ║   • Shared-database, shared-schema multi-tenancy with org_id on all tables ║
-- ║   • Row-Level Security (RLS) via session variable app.current_org_id       ║
-- ║   • UUID primary keys (gen_random_uuid(), native PG13+)                    ║
-- ║   • NUMERIC(10,4) for ALL monetary columns (mirrors Python Decimal)        ║
-- ║   • Immutable audit log (append-only, no UPDATE/DELETE grants)             ║
-- ║   • Double-entry integrity enforced via triggers + constraints             ║
-- ║   • Singapore GST tax codes seeded per IRAS classification                 ║
-- ║   • GST F5 Return structure with all 15 primary boxes                      ║
-- ║   • Chart of Accounts aligned with SFRS for Small Entities                 ║
-- ║                                                                            ║
-- ║   Execution Order:                                                         ║
-- ║    §0  Prerequisites & Extensions                                          ║
-- ║    §1  Schema Creation                                                     ║
-- ║    §2  Utility Functions (RLS helpers, naming, etc.)                        ║
-- ║    §3  Core Schema (Organisation, Users, Roles, Fiscal Periods)            ║
-- ║    §4  COA Schema (Chart of Accounts)                                      ║
-- ║    §5  GST Schema (Tax Codes, Rates)                                       ║
-- ║    §6  Journal Schema (General Ledger)                                     ║
-- ║    §7  Invoicing Schema (Contacts, Documents, Lines)                       ║
-- ║    §8  Banking Schema (Accounts, Payments, Reconciliation)                 ║
-- ║    §9  Audit Schema (Immutable Event Log)                                  ║
-- ║    §10 Stored Procedures (GST Calc, Journal Validation, F5 Return)         ║
-- ║    §11 Triggers (Audit, Balance Check, Timestamps, Sequences)              ║
-- ║    §12 Row-Level Security Policies                                         ║
-- ║    §13 Indexes (Performance-Critical)                                      ║
-- ║    §14 Seed Data (Tax Codes, Default CoA Template, Currencies)             ║
-- ║    §15 Application Roles & Grants                                          ║
-- ║                                                                            ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝


-- ============================================================================
-- §0  PREREQUISITES & EXTENSIONS
-- ============================================================================
-- Run as superuser (postgres) on a freshly created database.
--
-- CREATE DATABASE ledgersg
--     WITH ENCODING = 'UTF8'
--          LC_COLLATE = 'en_US.UTF-8'
--          LC_CTYPE = 'en_US.UTF-8'
--          TEMPLATE = template0;
--
-- \c ledgersg

-- Extensions required
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- Trigram search for contact/invoice lookups
CREATE EXTENSION IF NOT EXISTS "btree_gist";    -- GiST index support for exclusion constraints
CREATE EXTENSION IF NOT EXISTS "pgcrypto";      -- Additional crypto functions (optional, UUID is native)

-- Verify PostgreSQL version (must be 16+)
DO $$
BEGIN
    IF current_setting('server_version_num')::int < 160000 THEN
        RAISE EXCEPTION 'LedgerSG requires PostgreSQL 16 or higher. Current version: %',
            current_setting('server_version');
    END IF;
END $$;


-- ============================================================================
-- §1  SCHEMA CREATION
-- ============================================================================
-- Logical separation by domain. All schemas share the same database
-- for cross-schema FK references and transactional integrity.

DROP SCHEMA IF EXISTS audit     CASCADE;
DROP SCHEMA IF EXISTS banking   CASCADE;
DROP SCHEMA IF EXISTS invoicing CASCADE;
DROP SCHEMA IF EXISTS journal   CASCADE;
DROP SCHEMA IF EXISTS gst       CASCADE;
DROP SCHEMA IF EXISTS coa       CASCADE;
DROP SCHEMA IF EXISTS core      CASCADE;

CREATE SCHEMA core;         -- Organisation, users, roles, fiscal periods, settings
CREATE SCHEMA coa;          -- Chart of Accounts
CREATE SCHEMA gst;          -- GST tax codes, rates, returns
CREATE SCHEMA journal;      -- General Ledger (immutable double-entry)
CREATE SCHEMA invoicing;    -- Contacts, sales/purchase invoices, credit/debit notes
CREATE SCHEMA banking;      -- Bank accounts, payments, reconciliation
CREATE SCHEMA audit;        -- Immutable audit trail

COMMENT ON SCHEMA core      IS 'Tenant management: organisations, users, roles, fiscal configuration';
COMMENT ON SCHEMA coa       IS 'Chart of Accounts aligned with Singapore SFRS for Small Entities';
COMMENT ON SCHEMA gst       IS 'GST tax codes, computation, F5/F7 returns, InvoiceNow status';
COMMENT ON SCHEMA journal   IS 'Immutable double-entry general ledger';
COMMENT ON SCHEMA invoicing IS 'Sales & purchase documents: invoices, credit/debit notes, POs, quotes';
COMMENT ON SCHEMA banking   IS 'Bank accounts, payment recording, reconciliation';
COMMENT ON SCHEMA audit     IS 'Append-only audit log for regulatory compliance (5-year IRAS retention)';


-- ============================================================================
-- §2  UTILITY FUNCTIONS
-- ============================================================================

-- ──────────────────────────────────────────────
-- 2a. RLS Helper: Get current org_id from session
-- ──────────────────────────────────────────────
-- Django middleware will SET LOCAL app.current_org_id = '<uuid>' per transaction.
-- This function safely retrieves it, returning NULL if not set (denying all access).

CREATE OR REPLACE FUNCTION core.current_org_id()
RETURNS UUID
LANGUAGE sql
STABLE               -- Same result within a single statement/transaction
PARALLEL SAFE
AS $$
    SELECT NULLIF(current_setting('app.current_org_id', true), '')::UUID
$$;

COMMENT ON FUNCTION core.current_org_id()
    IS 'Returns the org_id set via SET LOCAL app.current_org_id for RLS policies. Returns NULL if unset.';


-- ──────────────────────────────────────────────
-- 2b. RLS Helper: Get current user_id from session
-- ──────────────────────────────────────────────

CREATE OR REPLACE FUNCTION core.current_user_id()
RETURNS UUID
LANGUAGE sql
STABLE
PARALLEL SAFE
AS $$
    SELECT NULLIF(current_setting('app.current_user_id', true), '')::UUID
$$;

COMMENT ON FUNCTION core.current_user_id()
    IS 'Returns the user_id set via SET LOCAL app.current_user_id for audit/RLS. Returns NULL if unset.';


-- ──────────────────────────────────────────────
-- 2c. Updated-at trigger function (reusable)
-- ──────────────────────────────────────────────

CREATE OR REPLACE FUNCTION core.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION core.set_updated_at()
    IS 'Generic trigger function to auto-set updated_at on row modification.';


-- ============================================================================
-- §3  CORE SCHEMA — Organisation, Users, Roles, Fiscal Periods
-- ============================================================================

-- ──────────────────────────────────────────────
-- 3a. Organisation (Tenant Root)
-- ──────────────────────────────────────────────
-- The central tenant entity. Every business entity in LedgerSG is an organisation.
-- Sole proprietorships, partnerships, LLPs, and Pte Ltds are all modelled here.

CREATE TABLE core.organisation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    legal_name          VARCHAR(255),                -- Official registered name (may differ from trading name)
    uen                 VARCHAR(20) UNIQUE,           -- ACRA Unique Entity Number (e.g., 202301234A)
    entity_type         VARCHAR(20) NOT NULL
        CHECK (entity_type IN ('sole_prop', 'partnership', 'llp', 'pte_ltd')),

    -- GST Configuration
    gst_registered      BOOLEAN NOT NULL DEFAULT FALSE,
    gst_reg_number      VARCHAR(20),                  -- Format: M90312345A (only if gst_registered = TRUE)
    gst_reg_date        DATE,                         -- Effective date of GST registration
    gst_scheme          VARCHAR(30) DEFAULT 'standard'
        CHECK (gst_scheme IN ('standard', 'cash', 'margin')),  -- Accounting basis for GST
    gst_filing_frequency VARCHAR(15) NOT NULL DEFAULT 'quarterly'
        CHECK (gst_filing_frequency IN ('monthly', 'quarterly', 'semi_annual')),

    -- InvoiceNow / Peppol Configuration
    peppol_participant_id VARCHAR(64),                -- Peppol network identifier (e.g., 0195:202301234A)
    peppol_scheme_id    VARCHAR(10) DEFAULT '0195',   -- 0195 = Singapore UEN scheme
    invoicenow_enabled  BOOLEAN NOT NULL DEFAULT FALSE,
    invoicenow_ap_id    VARCHAR(100),                 -- Access Point provider identifier

    -- Financial Year Configuration
    fy_start_month      SMALLINT NOT NULL DEFAULT 1   -- 1=Jan, 4=Apr, 7=Jul, etc.
        CHECK (fy_start_month BETWEEN 1 AND 12),

    -- Base Currency & Locale
    base_currency       CHAR(3) NOT NULL DEFAULT 'SGD',
    timezone            VARCHAR(50) NOT NULL DEFAULT 'Asia/Singapore',
    date_format         VARCHAR(20) NOT NULL DEFAULT 'DD/MM/YYYY',

    -- Business Address
    address_line_1      VARCHAR(255),
    address_line_2      VARCHAR(255),
    postal_code         VARCHAR(10),
    country             CHAR(2) NOT NULL DEFAULT 'SG',

    -- Contact
    phone               VARCHAR(30),
    email               VARCHAR(255),
    website             VARCHAR(255),

    -- Logo / Branding (path to S3/MinIO object)
    logo_url            VARCHAR(500),

    -- Lifecycle
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraint: GST fields must be populated if GST-registered
    CONSTRAINT chk_gst_consistency CHECK (
        (gst_registered = FALSE)
        OR
        (gst_registered = TRUE AND gst_reg_number IS NOT NULL AND gst_reg_date IS NOT NULL)
    )
);

COMMENT ON TABLE core.organisation
    IS 'Root tenant entity. Each business in LedgerSG is an organisation with isolated data.';
COMMENT ON COLUMN core.organisation.uen
    IS 'ACRA Unique Entity Number — primary business identifier in Singapore.';
COMMENT ON COLUMN core.organisation.gst_scheme
    IS 'GST accounting method: standard (accrual), cash (payment basis), margin (second-hand goods).';
COMMENT ON COLUMN core.organisation.peppol_participant_id
    IS 'Peppol network ID for InvoiceNow. Format: schemeID:identifier (e.g., 0195:202301234A).';

CREATE TRIGGER trg_organisation_updated_at
    BEFORE UPDATE ON core.organisation
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ──────────────────────────────────────────────
-- 3b. App User (Authentication & Identity)
-- ──────────────────────────────────────────────
-- Represents a human user of the system. Linked to orgs via user_organisation.
-- Password hashing is handled by Django (not stored here as raw text).

CREATE TABLE core.app_user (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(255) NOT NULL UNIQUE,
    full_name           VARCHAR(150) NOT NULL,
    phone               VARCHAR(30),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_superadmin       BOOLEAN NOT NULL DEFAULT FALSE,  -- Platform-level admin (not org-level)
    last_login_at       TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE core.app_user
    IS 'Application user identity. Password hash managed by Django auth system.';

CREATE TRIGGER trg_app_user_updated_at
    BEFORE UPDATE ON core.app_user
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ──────────────────────────────────────────────
-- 3c. Role (Organisation-Level Permissions)
-- ──────────────────────────────────────────────

CREATE TABLE core.role (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(50) NOT NULL UNIQUE,
    description         TEXT,
    -- Granular permission flags
    can_manage_org      BOOLEAN NOT NULL DEFAULT FALSE,  -- Edit org settings, invite users
    can_manage_users    BOOLEAN NOT NULL DEFAULT FALSE,  -- Assign roles
    can_manage_coa      BOOLEAN NOT NULL DEFAULT FALSE,  -- Edit chart of accounts
    can_create_invoices BOOLEAN NOT NULL DEFAULT FALSE,  -- Create/edit draft invoices
    can_approve_invoices BOOLEAN NOT NULL DEFAULT FALSE, -- Approve invoices (creates journal entry)
    can_void_invoices   BOOLEAN NOT NULL DEFAULT FALSE,  -- Void approved invoices
    can_create_journals BOOLEAN NOT NULL DEFAULT FALSE,  -- Manual journal entries
    can_manage_banking  BOOLEAN NOT NULL DEFAULT FALSE,  -- Bank accounts, reconciliation
    can_file_gst        BOOLEAN NOT NULL DEFAULT FALSE,  -- GST returns
    can_view_reports    BOOLEAN NOT NULL DEFAULT FALSE,  -- Financial reports
    can_export_data     BOOLEAN NOT NULL DEFAULT FALSE,  -- Data export/download
    is_system           BOOLEAN NOT NULL DEFAULT FALSE,  -- System-defined (cannot be deleted)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE core.role
    IS 'Permission roles assignable to users within an organisation context.';


-- ──────────────────────────────────────────────
-- 3d. User ↔ Organisation (Many-to-Many with Role)
-- ──────────────────────────────────────────────
-- A user can belong to multiple organisations (e.g., accountant managing multiple clients).
-- Each membership carries a role defining permissions within that org.

CREATE TABLE core.user_organisation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES core.app_user(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    role_id             UUID NOT NULL REFERENCES core.role(id) ON DELETE RESTRICT,
    is_default          BOOLEAN NOT NULL DEFAULT FALSE,  -- Default org for this user on login
    invited_at          TIMESTAMPTZ,
    accepted_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, org_id)
);

COMMENT ON TABLE core.user_organisation
    IS 'Links users to organisations with a role. One user can serve multiple orgs.';


-- ──────────────────────────────────────────────
-- 3e. Fiscal Year
-- ──────────────────────────────────────────────
-- Singapore businesses can have any financial year-end (e.g., Dec 31, Mar 31).
-- Each fiscal year has 12 periods + optional period 13 for adjustments.

CREATE TABLE core.fiscal_year (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    label               VARCHAR(30) NOT NULL,            -- e.g., 'FY2025', 'FY2025/26'
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    is_closed           BOOLEAN NOT NULL DEFAULT FALSE,  -- Once closed, no new entries allowed
    is_locked           BOOLEAN NOT NULL DEFAULT FALSE,  -- Locked for editing but not yet closed
    closed_at           TIMESTAMPTZ,
    closed_by           UUID REFERENCES core.app_user(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_fy_dates CHECK (end_date > start_date),
    CONSTRAINT chk_fy_max_duration CHECK (end_date <= start_date + INTERVAL '18 months'),
    UNIQUE(org_id, label),
    UNIQUE(org_id, start_date)  -- Prevent overlapping fiscal years
);

COMMENT ON TABLE core.fiscal_year
    IS 'Fiscal years per organisation. Singapore allows any FY end date.';


-- ──────────────────────────────────────────────
-- 3f. Fiscal Period (Months within a Fiscal Year)
-- ──────────────────────────────────────────────

CREATE TABLE core.fiscal_period (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fiscal_year_id      UUID NOT NULL REFERENCES core.fiscal_year(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    period_number       SMALLINT NOT NULL,                -- 1-12 (or 13 for adjustment period)
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    is_open             BOOLEAN NOT NULL DEFAULT TRUE,    -- Only open periods accept entries
    is_adjustment       BOOLEAN NOT NULL DEFAULT FALSE,   -- Period 13: year-end adjustments only
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_period_number CHECK (period_number BETWEEN 1 AND 13),
    CONSTRAINT chk_period_dates CHECK (end_date >= start_date),
    UNIQUE(fiscal_year_id, period_number),
    UNIQUE(org_id, start_date, end_date)
);

COMMENT ON TABLE core.fiscal_period
    IS 'Monthly periods within a fiscal year. Period 13 is for year-end adjustments.';


-- ──────────────────────────────────────────────
-- 3g. Currency (Reference Table)
-- ──────────────────────────────────────────────

CREATE TABLE core.currency (
    code                CHAR(3) PRIMARY KEY,              -- ISO 4217 (SGD, USD, MYR, etc.)
    name                VARCHAR(100) NOT NULL,
    symbol              VARCHAR(5) NOT NULL,
    decimal_places      SMALLINT NOT NULL DEFAULT 2,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE core.currency
    IS 'ISO 4217 currency reference. SGD is the base for all Singapore reporting.';


-- ──────────────────────────────────────────────
-- 3h. Exchange Rate (Daily Rates for Multi-Currency)
-- ──────────────────────────────────────────────
-- IRAS requires consistent rate source. We store rates relative to SGD.
-- Rate = 1 unit of foreign currency in SGD (e.g., 1 USD = 1.3500 SGD)

CREATE TABLE core.exchange_rate (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    currency_code       CHAR(3) NOT NULL REFERENCES core.currency(code),
    rate_date           DATE NOT NULL,
    rate                NUMERIC(12,6) NOT NULL,           -- 1 foreign unit = X SGD
    source              VARCHAR(50) DEFAULT 'manual',     -- 'manual', 'mas', 'oanda', etc.
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_rate_positive CHECK (rate > 0),
    UNIQUE(org_id, currency_code, rate_date)
);

COMMENT ON TABLE core.exchange_rate
    IS 'Daily exchange rates per org. IRAS requires consistent rate source per invoice date.';
COMMENT ON COLUMN core.exchange_rate.rate
    IS '1 unit of foreign currency = X SGD. E.g., 1 USD = 1.3500 SGD → rate = 1.350000';


-- ──────────────────────────────────────────────
-- 3i. Document Sequence (Auto-Numbering)
-- ──────────────────────────────────────────────
-- Each org + document type gets an independent sequence counter.
-- Uses SELECT ... FOR UPDATE to guarantee gap-free sequential numbering.

CREATE TABLE core.document_sequence (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    document_type       VARCHAR(30) NOT NULL,              -- e.g., 'SALES_INVOICE', 'PURCHASE_INVOICE'
    prefix              VARCHAR(20) NOT NULL DEFAULT '',   -- e.g., 'INV-', 'PO-', 'CN-'
    next_number         BIGINT NOT NULL DEFAULT 1,
    padding             SMALLINT NOT NULL DEFAULT 5,       -- Zero-pad width (e.g., 5 → 00001)
    fiscal_year_reset   BOOLEAN NOT NULL DEFAULT FALSE,    -- Reset numbering each FY?
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_next_number_positive CHECK (next_number > 0),
    UNIQUE(org_id, document_type)
);

COMMENT ON TABLE core.document_sequence
    IS 'Auto-numbering sequences per org per document type. Thread-safe via row-level locking.';

CREATE TRIGGER trg_document_sequence_updated_at
    BEFORE UPDATE ON core.document_sequence
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ──────────────────────────────────────────────
-- 3j. Organisation Settings (Key-Value Config)
-- ──────────────────────────────────────────────
-- Flexible settings store for org-level configuration that doesn't
-- warrant its own column on the organisation table.

CREATE TABLE core.organisation_setting (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    setting_key         VARCHAR(100) NOT NULL,
    setting_value       JSONB NOT NULL DEFAULT '{}',
    description         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(org_id, setting_key)
);

COMMENT ON TABLE core.organisation_setting
    IS 'Key-value settings per org (e.g., invoice footer text, default payment terms).';

CREATE TRIGGER trg_org_setting_updated_at
    BEFORE UPDATE ON core.organisation_setting
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ============================================================================
-- §4  COA SCHEMA — Chart of Accounts
-- ============================================================================
-- Aligned with Singapore SFRS for Small Entities structure.
-- Hierarchical via parent_id self-reference.

-- ──────────────────────────────────────────────
-- 4a. Account Type (Classification)
-- ──────────────────────────────────────────────

CREATE TABLE coa.account_type (
    id                  SMALLINT PRIMARY KEY,
    code                VARCHAR(20) NOT NULL UNIQUE,      -- 'ASSET', 'LIABILITY', etc.
    name                VARCHAR(50) NOT NULL,
    normal_balance      VARCHAR(6) NOT NULL
        CHECK (normal_balance IN ('DEBIT', 'CREDIT')),
    classification      VARCHAR(20) NOT NULL
        CHECK (classification IN ('BALANCE_SHEET', 'INCOME_STATEMENT')),
    display_order       SMALLINT NOT NULL,
    is_debit_positive   BOOLEAN NOT NULL                  -- TRUE for Assets/Expenses, FALSE for Liabilities/Equity/Revenue
);

COMMENT ON TABLE coa.account_type
    IS 'Fixed classification of account types. System-defined, not org-specific.';


-- ──────────────────────────────────────────────
-- 4b. Account Sub-Type (Granular Classification)
-- ──────────────────────────────────────────────

CREATE TABLE coa.account_sub_type (
    id                  SMALLINT PRIMARY KEY,
    account_type_id     SMALLINT NOT NULL REFERENCES coa.account_type(id),
    code                VARCHAR(30) NOT NULL UNIQUE,
    name                VARCHAR(80) NOT NULL,
    description         TEXT,
    display_order       SMALLINT NOT NULL
);

COMMENT ON TABLE coa.account_sub_type
    IS 'Sub-classification (e.g., Current Asset, Fixed Asset, Current Liability). System-defined.';


-- ──────────────────────────────────────────────
-- 4c. Account (The Chart of Accounts Itself)
-- ──────────────────────────────────────────────

CREATE TABLE coa.account (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    code                VARCHAR(10) NOT NULL,              -- Hierarchical code: '1000', '1100', '4000'
    name                VARCHAR(150) NOT NULL,
    description         TEXT,
    account_type_id     SMALLINT NOT NULL REFERENCES coa.account_type(id),
    account_sub_type_id SMALLINT REFERENCES coa.account_sub_type(id),
    parent_id           UUID REFERENCES coa.account(id),  -- Self-reference for hierarchy
    currency            CHAR(3) NOT NULL DEFAULT 'SGD' REFERENCES core.currency(code),
    tax_code_default    VARCHAR(10),                       -- Default GST tax code for this account

    -- Flags
    is_system           BOOLEAN NOT NULL DEFAULT FALSE,    -- Locked system accounts (GST Output, Retained Earnings)
    is_header           BOOLEAN NOT NULL DEFAULT FALSE,    -- Header/group account (cannot post to directly)
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_bank             BOOLEAN NOT NULL DEFAULT FALSE,    -- Links to a bank account in banking schema
    is_control          BOOLEAN NOT NULL DEFAULT FALSE,    -- AR/AP control accounts (system-managed)

    -- Tracking
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_account_org_code UNIQUE(org_id, code),
    CONSTRAINT chk_code_format CHECK (code ~ '^[0-9]{3,10}$'),  -- Numeric codes only
    CONSTRAINT chk_no_post_to_header CHECK (
        -- Header accounts cannot be control or bank accounts
        (is_header = FALSE) OR (is_header = TRUE AND is_bank = FALSE AND is_control = FALSE)
    )
);

COMMENT ON TABLE coa.account
    IS 'Chart of Accounts per organisation. Aligned with SFRS for Small Entities classifications.';
COMMENT ON COLUMN coa.account.is_system
    IS 'System-defined accounts (e.g., GST Output, GST Input, Retained Earnings) cannot be deleted.';
COMMENT ON COLUMN coa.account.is_control
    IS 'Control accounts (AR, AP) receive postings only from sub-ledger documents, not manual journals.';
COMMENT ON COLUMN coa.account.tax_code_default
    IS 'Default tax code auto-populated when this account is selected on an invoice line.';

CREATE TRIGGER trg_account_updated_at
    BEFORE UPDATE ON coa.account
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ============================================================================
-- §5  GST SCHEMA — Tax Codes, Rates, Returns
-- ============================================================================

-- ──────────────────────────────────────────────
-- 5a. Tax Code
-- ──────────────────────────────────────────────
-- Singapore IRAS-classified GST tax codes.
-- Supports rate history via effective_from/effective_to for rate change compliance.

CREATE TABLE gst.tax_code (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code                VARCHAR(10) NOT NULL,
    description         VARCHAR(150) NOT NULL,
    rate                NUMERIC(5,4) NOT NULL,             -- 0.0900 for 9%, 0.0000 for 0%
    is_input            BOOLEAN NOT NULL DEFAULT FALSE,    -- TRUE = purchase tax code
    is_output           BOOLEAN NOT NULL DEFAULT FALSE,    -- TRUE = sales tax code
    is_claimable        BOOLEAN NOT NULL DEFAULT TRUE,     -- FALSE for blocked input tax (BL)
    is_reverse_charge   BOOLEAN NOT NULL DEFAULT FALSE,    -- TRUE for reverse charge (RS)
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from      DATE NOT NULL DEFAULT '2024-01-01',
    effective_to        DATE,                               -- NULL = currently active

    -- GST F5 Return mapping
    -- Which box(es) this tax code contributes to
    f5_supply_box       SMALLINT,                          -- Box 1, 2, or 3 (for output codes)
    f5_purchase_box     SMALLINT,                          -- Box 5 (for input codes)
    f5_tax_box          SMALLINT,                          -- Box 6 (output tax) or Box 7 (input tax)

    display_order       SMALLINT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_rate_range CHECK (rate >= 0 AND rate <= 1),
    CONSTRAINT chk_io_flag CHECK (
        -- A tax code must be input, output, or both — but not neither (except for 'NA')
        is_input = TRUE OR is_output = TRUE OR code = 'NA'
    ),
    -- Unique code per effective period (allows historical rates)
    UNIQUE(code, effective_from)
);

COMMENT ON TABLE gst.tax_code
    IS 'IRAS-classified GST tax codes with rate history. Supports 9% rate and future changes.';
COMMENT ON COLUMN gst.tax_code.f5_supply_box
    IS 'Maps to GST F5 supply boxes: 1=Standard-Rated, 2=Zero-Rated, 3=Exempt.';
COMMENT ON COLUMN gst.tax_code.f5_purchase_box
    IS 'Maps to GST F5 Box 5: Total value of taxable purchases.';
COMMENT ON COLUMN gst.tax_code.f5_tax_box
    IS 'Maps to Box 6 (output tax) or Box 7 (claimable input tax) on GST F5.';


-- ──────────────────────────────────────────────
-- 5b. GST Return (GST F5 / F7 / F8)
-- ──────────────────────────────────────────────
-- Stores computed GST return data aligned with IRAS GST F5 form structure.
-- All 15 primary boxes modelled as separate NUMERIC(10,4) columns.

CREATE TABLE gst.return (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    return_type         VARCHAR(5) NOT NULL DEFAULT 'F5'
        CHECK (return_type IN ('F5', 'F7', 'F8')),
    period_start        DATE NOT NULL,
    period_end          DATE NOT NULL,
    filing_due_date     DATE NOT NULL,

    -- ═══════════════════════════════════════════
    -- GST F5 Boxes (per IRAS specification)
    -- All values in SGD, NUMERIC(10,4) precision
    -- ═══════════════════════════════════════════

    -- SUPPLIES
    box1_std_rated_supplies         NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Standard-rated supplies (excl. GST)
    box2_zero_rated_supplies        NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Zero-rated supplies
    box3_exempt_supplies            NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Exempt supplies
    box4_total_supplies             NUMERIC(10,4) NOT NULL DEFAULT 0,  -- = Box 1 + 2 + 3 (auto-computed)

    -- PURCHASES
    box5_total_taxable_purchases    NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Total taxable purchases

    -- TAX
    box6_output_tax                 NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Output tax due (9% of Box 1)
    box7_input_tax_claimable        NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Input tax claimable
    box8_net_gst                    NUMERIC(10,4) NOT NULL DEFAULT 0,  -- = Box 6 - Box 7 (payable if +ve)

    -- SCHEMES (for eligible businesses)
    box9_imports_under_schemes      NUMERIC(10,4) NOT NULL DEFAULT 0,  -- MES/3PL/etc.
    box10_tourist_refund            NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Tourist refund scheme
    box11_bad_debt_relief           NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Bad debt relief claimed
    box12_pre_reg_input_tax         NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Pre-registration input tax

    -- REVENUE
    box13_total_revenue             NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Total revenue for the period

    -- REVERSE CHARGE
    box14_reverse_charge_supplies   NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Value of RC supplies
    box15_electronic_marketplace    NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Marketplace digital services

    -- STATUS & AUDIT
    status              VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'COMPUTED', 'REVIEWED', 'FILED', 'AMENDED')),
    computed_at         TIMESTAMPTZ,
    reviewed_at         TIMESTAMPTZ,
    reviewed_by         UUID REFERENCES core.app_user(id),
    filed_at            TIMESTAMPTZ,
    filed_by            UUID REFERENCES core.app_user(id),
    iras_confirmation   VARCHAR(50),                       -- IRAS acknowledgement number
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_return_dates CHECK (period_end > period_start),
    CONSTRAINT chk_box4_total CHECK (
        status = 'DRAFT' OR box4_total_supplies = box1_std_rated_supplies + box2_zero_rated_supplies + box3_exempt_supplies
    ),
    CONSTRAINT chk_box8_net CHECK (
        status = 'DRAFT' OR box8_net_gst = box6_output_tax - box7_input_tax_claimable
    ),
    UNIQUE(org_id, return_type, period_start, period_end)
);

COMMENT ON TABLE gst.return
    IS 'GST F5/F7/F8 return data per IRAS specification. All 15 boxes mapped as typed columns.';

CREATE TRIGGER trg_gst_return_updated_at
    BEFORE UPDATE ON gst.return
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ──────────────────────────────────────────────
-- 5c. GST Threshold Monitor (for Non-Registered Businesses)
-- ──────────────────────────────────────────────
-- Tracks rolling 12-month taxable turnover to alert when nearing S$1M.

CREATE TABLE gst.threshold_snapshot (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    snapshot_date       DATE NOT NULL,
    rolling_12m_revenue NUMERIC(12,4) NOT NULL DEFAULT 0,
    threshold_amount    NUMERIC(12,4) NOT NULL DEFAULT 1000000.0000,  -- S$1,000,000
    threshold_pct       NUMERIC(5,2) NOT NULL DEFAULT 0,              -- Current % of threshold
    alert_level         VARCHAR(20) NOT NULL DEFAULT 'NONE'
        CHECK (alert_level IN ('NONE', 'WATCH', 'WARNING', 'CRITICAL')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(org_id, snapshot_date)
);

COMMENT ON TABLE gst.threshold_snapshot
    IS 'Monthly snapshot of rolling turnover for non-GST-registered businesses. Triggers registration alerts.';


-- ============================================================================
-- §6  JOURNAL SCHEMA — General Ledger (Immutable Double-Entry)
-- ============================================================================

-- ──────────────────────────────────────────────
-- 6a. Journal Entry (Header)
-- ──────────────────────────────────────────────
-- IMMUTABLE: Once posted, entries cannot be edited — only reversed.
-- Corrections are made by creating a reversal entry with a link.

CREATE TABLE journal.entry (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    entry_number        BIGINT NOT NULL,                   -- Sequential per org (gap-free)
    entry_date          DATE NOT NULL,

    -- Source linkage
    source_type         VARCHAR(30) NOT NULL
        CHECK (source_type IN (
            'MANUAL', 'SALES_INVOICE', 'PURCHASE_INVOICE',
            'SALES_CREDIT_NOTE', 'PURCHASE_CREDIT_NOTE',
            'SALES_DEBIT_NOTE', 'PURCHASE_DEBIT_NOTE',
            'PAYMENT_RECEIVED', 'PAYMENT_MADE',
            'BANK_FEE', 'FX_REVALUATION',
            'YEAR_END', 'OPENING_BALANCE', 'REVERSAL'
        )),
    source_id           UUID,                              -- FK to originating document (if any)

    -- Description
    reference           VARCHAR(100),                      -- External reference (cheque no., bank ref)
    narration           TEXT NOT NULL,                      -- Mandatory description of the entry

    -- Fiscal period linkage
    fiscal_year_id      UUID NOT NULL REFERENCES core.fiscal_year(id),
    fiscal_period_id    UUID NOT NULL REFERENCES core.fiscal_period(id),

    -- Reversal tracking
    is_reversed         BOOLEAN NOT NULL DEFAULT FALSE,
    reversed_by_id      UUID REFERENCES journal.entry(id), -- Points to the reversing entry
    reversal_of_id      UUID REFERENCES journal.entry(id), -- Points to the original reversed entry

    -- Immutability
    posted_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    posted_by           UUID NOT NULL REFERENCES core.app_user(id),

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_entry_org_number UNIQUE(org_id, entry_number),
    CONSTRAINT chk_reversal_consistency CHECK (
        (is_reversed = FALSE AND reversed_by_id IS NULL)
        OR
        (is_reversed = TRUE AND reversed_by_id IS NOT NULL)
    )
);

COMMENT ON TABLE journal.entry
    IS 'Immutable journal entry header. Corrections only via reversal entries. Core of double-entry GL.';
COMMENT ON COLUMN journal.entry.entry_number
    IS 'Gap-free sequential number per org. Generated via core.document_sequence with row locking.';
COMMENT ON COLUMN journal.entry.source_type
    IS 'Origin of the journal entry. System-generated entries link back to invoices/payments.';


-- ──────────────────────────────────────────────
-- 6b. Journal Line (Detail)
-- ──────────────────────────────────────────────
-- Each line represents one debit OR one credit (never both on the same line).

CREATE TABLE journal.line (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id            UUID NOT NULL REFERENCES journal.entry(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES core.organisation(id),  -- Denormalized for RLS
    line_number         SMALLINT NOT NULL,
    account_id          UUID NOT NULL REFERENCES coa.account(id),
    description         VARCHAR(500),

    -- Amounts in TRANSACTION currency
    debit               NUMERIC(10,4) NOT NULL DEFAULT 0,
    credit              NUMERIC(10,4) NOT NULL DEFAULT 0,

    -- GST
    tax_code_id         UUID REFERENCES gst.tax_code(id),
    tax_amount          NUMERIC(10,4) NOT NULL DEFAULT 0,

    -- Multi-currency support
    currency            CHAR(3) NOT NULL DEFAULT 'SGD' REFERENCES core.currency(code),
    exchange_rate       NUMERIC(12,6) NOT NULL DEFAULT 1.000000,

    -- Amounts in BASE currency (SGD) — for reporting
    base_debit          NUMERIC(10,4) NOT NULL DEFAULT 0,
    base_credit         NUMERIC(10,4) NOT NULL DEFAULT 0,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Each line must be purely debit or purely credit (or zero for memo lines)
    CONSTRAINT chk_debit_xor_credit CHECK (
        (debit >= 0 AND credit >= 0)
        AND NOT (debit > 0 AND credit > 0)
    ),
    CONSTRAINT chk_base_debit_xor_credit CHECK (
        (base_debit >= 0 AND base_credit >= 0)
        AND NOT (base_debit > 0 AND base_credit > 0)
    ),
    CONSTRAINT chk_exchange_rate_positive CHECK (exchange_rate > 0),
    UNIQUE(entry_id, line_number)
);

COMMENT ON TABLE journal.line
    IS 'Individual debit/credit line within a journal entry. Each line posts to one GL account.';
COMMENT ON COLUMN journal.line.base_debit
    IS 'Debit amount converted to SGD at the entry date exchange rate. Used for all reporting.';


-- ============================================================================
-- §7  INVOICING SCHEMA — Contacts, Documents, Lines
-- ============================================================================

-- ──────────────────────────────────────────────
-- 7a. Contact (Customers & Suppliers)
-- ──────────────────────────────────────────────

CREATE TABLE invoicing.contact (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    contact_type        VARCHAR(10) NOT NULL
        CHECK (contact_type IN ('CUSTOMER', 'SUPPLIER', 'BOTH')),
    name                VARCHAR(255) NOT NULL,
    legal_name          VARCHAR(255),
    uen                 VARCHAR(20),                       -- Singapore UEN (if applicable)
    gst_reg_number      VARCHAR(20),
    is_gst_registered   BOOLEAN NOT NULL DEFAULT FALSE,
    tax_code_default    VARCHAR(10),                       -- Default tax code for this contact

    -- Communication
    email               VARCHAR(255),
    phone               VARCHAR(30),
    fax                 VARCHAR(30),
    website             VARCHAR(255),

    -- Address
    address_line_1      VARCHAR(255),
    address_line_2      VARCHAR(255),
    city                VARCHAR(100),
    state_province      VARCHAR(100),
    postal_code         VARCHAR(20),
    country             CHAR(2) NOT NULL DEFAULT 'SG',

    -- Financial Defaults
    default_currency    CHAR(3) NOT NULL DEFAULT 'SGD' REFERENCES core.currency(code),
    payment_terms_days  SMALLINT NOT NULL DEFAULT 30,      -- Net X days
    credit_limit        NUMERIC(10,4),                     -- Optional credit limit in SGD

    -- Control Accounts (which AR/AP account to use)
    receivable_account_id UUID REFERENCES coa.account(id), -- Defaults to standard AR
    payable_account_id  UUID REFERENCES coa.account(id),   -- Defaults to standard AP

    -- InvoiceNow / Peppol
    peppol_id           VARCHAR(64),                       -- Contact's Peppol participant ID
    peppol_scheme_id    VARCHAR(10),

    -- Lifecycle
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE invoicing.contact
    IS 'Customers and suppliers. A contact can be both. Each has independent financial defaults.';

CREATE TRIGGER trg_contact_updated_at
    BEFORE UPDATE ON invoicing.contact
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ──────────────────────────────────────────────
-- 7b. Custom ENUM Types for Invoicing
-- ──────────────────────────────────────────────

CREATE TYPE invoicing.doc_type AS ENUM (
    'SALES_INVOICE',
    'SALES_CREDIT_NOTE',
    'SALES_DEBIT_NOTE',
    'PURCHASE_INVOICE',
    'PURCHASE_CREDIT_NOTE',
    'PURCHASE_DEBIT_NOTE',
    'PURCHASE_ORDER',
    'SALES_QUOTE'
);

CREATE TYPE invoicing.doc_status AS ENUM (
    'DRAFT',
    'APPROVED',
    'SENT',
    'PARTIALLY_PAID',
    'PAID',
    'OVERDUE',
    'VOID'
);


-- ──────────────────────────────────────────────
-- 7c. Document (Unified Invoice / Credit Note / PO / Quote)
-- ──────────────────────────────────────────────

CREATE TABLE invoicing.document (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    document_type       invoicing.doc_type NOT NULL,
    document_number     VARCHAR(30) NOT NULL,
    document_date       DATE NOT NULL,
    due_date            DATE,

    -- Parties
    contact_id          UUID NOT NULL REFERENCES invoicing.contact(id) ON DELETE RESTRICT,

    -- Currency
    currency            CHAR(3) NOT NULL DEFAULT 'SGD' REFERENCES core.currency(code),
    exchange_rate       NUMERIC(12,6) NOT NULL DEFAULT 1.000000,

    -- Computed Totals (all NUMERIC(10,4))
    subtotal            NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Sum of line amounts (excl. GST)
    total_discount      NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Sum of line discounts
    total_gst           NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Sum of line GST amounts
    total_amount        NUMERIC(10,4) NOT NULL DEFAULT 0,  -- subtotal + total_gst
    amount_paid         NUMERIC(10,4) NOT NULL DEFAULT 0,  -- Running total of payments received
    amount_due          NUMERIC(10,4) NOT NULL DEFAULT 0,  -- total_amount - amount_paid

    -- Base currency equivalents (for multi-currency reporting)
    base_subtotal       NUMERIC(10,4) NOT NULL DEFAULT 0,
    base_total_gst      NUMERIC(10,4) NOT NULL DEFAULT 0,
    base_total_amount   NUMERIC(10,4) NOT NULL DEFAULT 0,

    -- Status
    status              invoicing.doc_status NOT NULL DEFAULT 'DRAFT',

    -- References
    reference           VARCHAR(100),                      -- Customer PO number, external ref
    internal_notes      TEXT,                               -- Private notes (not printed)
    customer_notes      TEXT,                               -- Printed on invoice

    -- Tax Invoice Compliance
    -- IRAS Reg 11: Tax invoices must include specific fields
    is_tax_invoice      BOOLEAN NOT NULL DEFAULT FALSE,    -- TRUE only if org is GST-registered
    tax_invoice_label   VARCHAR(50),                       -- 'Tax Invoice', 'Simplified Tax Invoice', 'Invoice'

    -- InvoiceNow / Peppol
    peppol_message_id   UUID,
    invoicenow_status   VARCHAR(20) DEFAULT 'NOT_APPLICABLE'
        CHECK (invoicenow_status IN (
            'NOT_APPLICABLE', 'PENDING', 'QUEUED', 'TRANSMITTED',
            'DELIVERED', 'FAILED', 'REJECTED'
        )),
    invoicenow_sent_at  TIMESTAMPTZ,
    invoicenow_error    TEXT,

    -- Linked Journal Entry (created on APPROVE, set to NULL on VOID's new reversal)
    journal_entry_id    UUID REFERENCES journal.entry(id),

    -- Document Relationships
    related_document_id UUID REFERENCES invoicing.document(id),  -- Credit note → original invoice

    -- Lifecycle
    approved_at         TIMESTAMPTZ,
    approved_by         UUID REFERENCES core.app_user(id),
    voided_at           TIMESTAMPTZ,
    voided_by           UUID REFERENCES core.app_user(id),
    void_reason         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_doc_org_type_number UNIQUE(org_id, document_type, document_number),
    CONSTRAINT chk_exchange_rate_positive CHECK (exchange_rate > 0),
    CONSTRAINT chk_amounts_non_negative CHECK (
        subtotal >= 0 AND total_gst >= 0 AND total_amount >= 0 AND amount_paid >= 0
    ),
    CONSTRAINT chk_amount_due CHECK (amount_due = total_amount - amount_paid),
    CONSTRAINT chk_void_reason CHECK (
        (status != 'VOID') OR (status = 'VOID' AND void_reason IS NOT NULL)
    )
);

COMMENT ON TABLE invoicing.document
    IS 'Unified document model for invoices, credit/debit notes, POs, and quotes.';
COMMENT ON COLUMN invoicing.document.is_tax_invoice
    IS 'Per IRAS Reg 11: only GST-registered businesses may issue Tax Invoices.';
COMMENT ON COLUMN invoicing.document.invoicenow_status
    IS 'Peppol InvoiceNow transmission status. NOT_APPLICABLE for non-participating orgs.';

CREATE TRIGGER trg_document_updated_at
    BEFORE UPDATE ON invoicing.document
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ──────────────────────────────────────────────
-- 7d. Document Line (Invoice Line Items)
-- ──────────────────────────────────────────────
-- GST is calculated per line, then summed. Per IRAS guidance.

CREATE TABLE invoicing.document_line (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID NOT NULL REFERENCES invoicing.document(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES core.organisation(id),  -- Denormalized for RLS
    line_number         SMALLINT NOT NULL,
    description         VARCHAR(500) NOT NULL,
    account_id          UUID NOT NULL REFERENCES coa.account(id),

    -- Quantity & Pricing
    quantity            NUMERIC(10,4) NOT NULL DEFAULT 1,
    unit_of_measure     VARCHAR(20) DEFAULT 'EA',          -- EA, HR, KG, etc.
    unit_price          NUMERIC(10,4) NOT NULL,

    -- Discount
    discount_pct        NUMERIC(5,2) NOT NULL DEFAULT 0
        CHECK (discount_pct >= 0 AND discount_pct <= 100),
    discount_amount     NUMERIC(10,4) NOT NULL DEFAULT 0,

    -- GST (computed, stored for performance and audit)
    tax_code_id         UUID NOT NULL REFERENCES gst.tax_code(id),
    tax_rate            NUMERIC(5,4) NOT NULL,              -- Snapshot of rate at creation time
    is_tax_inclusive    BOOLEAN NOT NULL DEFAULT FALSE,     -- TRUE if unit_price includes GST

    -- Computed amounts (all NUMERIC(10,4))
    line_amount         NUMERIC(10,4) NOT NULL,             -- qty × unit_price × (1 - disc%) — before GST
    gst_amount          NUMERIC(10,4) NOT NULL,             -- GST on this line
    total_amount        NUMERIC(10,4) NOT NULL,             -- line_amount + gst_amount

    -- Base currency equivalents
    base_line_amount    NUMERIC(10,4) NOT NULL DEFAULT 0,
    base_gst_amount     NUMERIC(10,4) NOT NULL DEFAULT 0,
    base_total_amount   NUMERIC(10,4) NOT NULL DEFAULT 0,

    -- Optional: inventory item reference (future module)
    item_id             UUID,
    item_code           VARCHAR(30),

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_docline_doc_lineno UNIQUE(document_id, line_number),
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_total_consistency CHECK (
        -- Allow small rounding tolerance (±0.01)
        ABS(total_amount - (line_amount + gst_amount)) < 0.01
    )
);

COMMENT ON TABLE invoicing.document_line
    IS 'Individual line items on an invoice. GST computed per line per IRAS requirements.';
COMMENT ON COLUMN invoicing.document_line.tax_rate
    IS 'Snapshot of the GST rate at the time this line was created. Preserved for audit/historical accuracy.';


-- ──────────────────────────────────────────────
-- 7e. Document Attachment
-- ──────────────────────────────────────────────

CREATE TABLE invoicing.document_attachment (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID NOT NULL REFERENCES invoicing.document(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES core.organisation(id),
    file_name           VARCHAR(255) NOT NULL,
    file_type           VARCHAR(50) NOT NULL,               -- MIME type
    file_size_bytes     BIGINT NOT NULL,
    storage_path        VARCHAR(500) NOT NULL,              -- S3/MinIO object key
    uploaded_by         UUID NOT NULL REFERENCES core.app_user(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE invoicing.document_attachment
    IS 'File attachments linked to invoices/documents. Stored externally in S3/MinIO.';


-- ============================================================================
-- §8  BANKING SCHEMA — Accounts, Payments, Reconciliation
-- ============================================================================

-- ──────────────────────────────────────────────
-- 8a. Bank Account
-- ──────────────────────────────────────────────

CREATE TABLE banking.bank_account (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    account_name        VARCHAR(150) NOT NULL,              -- "DBS Current Account"
    bank_name           VARCHAR(100) NOT NULL,              -- "DBS Bank Ltd"
    account_number      VARCHAR(30) NOT NULL,
    bank_code           VARCHAR(20),                        -- SWIFT/BIC
    branch_code         VARCHAR(20),
    currency            CHAR(3) NOT NULL DEFAULT 'SGD' REFERENCES core.currency(code),
    gl_account_id       UUID NOT NULL REFERENCES coa.account(id),  -- Linked GL account (1100, 1110, etc.)

    -- PayNow (Singapore instant payment)
    paynow_type         VARCHAR(10)                        -- 'UEN', 'MOBILE', 'NRIC'
        CHECK (paynow_type IS NULL OR paynow_type IN ('UEN', 'MOBILE', 'NRIC')),
    paynow_id           VARCHAR(20),                       -- The PayNow proxy ID

    -- Status
    is_default          BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    opening_balance     NUMERIC(10,4) NOT NULL DEFAULT 0,
    opening_balance_date DATE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(org_id, account_number)
);

COMMENT ON TABLE banking.bank_account
    IS 'Organisation bank accounts. Each links to a GL account in the Chart of Accounts.';

CREATE TRIGGER trg_bank_account_updated_at
    BEFORE UPDATE ON banking.bank_account
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ──────────────────────────────────────────────
-- 8b. Payment (Received & Made)
-- ──────────────────────────────────────────────

CREATE TABLE banking.payment (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    payment_type        VARCHAR(15) NOT NULL
        CHECK (payment_type IN ('RECEIVED', 'MADE')),      -- Money in vs. money out
    payment_number      VARCHAR(30) NOT NULL,               -- Auto-generated
    payment_date        DATE NOT NULL,
    contact_id          UUID NOT NULL REFERENCES invoicing.contact(id),
    bank_account_id     UUID NOT NULL REFERENCES banking.bank_account(id),

    -- Amount
    currency            CHAR(3) NOT NULL DEFAULT 'SGD' REFERENCES core.currency(code),
    exchange_rate       NUMERIC(12,6) NOT NULL DEFAULT 1.000000,
    amount              NUMERIC(10,4) NOT NULL,
    base_amount         NUMERIC(10,4) NOT NULL,             -- SGD equivalent
    fx_gain_loss        NUMERIC(10,4) NOT NULL DEFAULT 0,   -- FX difference at settlement

    -- Payment Method
    payment_method      VARCHAR(20) NOT NULL DEFAULT 'BANK_TRANSFER'
        CHECK (payment_method IN (
            'BANK_TRANSFER', 'CHEQUE', 'CASH', 'PAYNOW',
            'CREDIT_CARD', 'GIRO', 'OTHER'
        )),
    payment_reference   VARCHAR(100),                       -- Cheque no., transaction ref, etc.

    -- Journal Link
    journal_entry_id    UUID REFERENCES journal.entry(id),

    -- Status
    is_reconciled       BOOLEAN NOT NULL DEFAULT FALSE,
    is_voided           BOOLEAN NOT NULL DEFAULT FALSE,

    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_payment_amount_positive CHECK (amount > 0),
    UNIQUE(org_id, payment_type, payment_number)
);

COMMENT ON TABLE banking.payment
    IS 'Payment records for money received from customers or paid to suppliers.';

CREATE TRIGGER trg_payment_updated_at
    BEFORE UPDATE ON banking.payment
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ──────────────────────────────────────────────
-- 8c. Payment Allocation (Payment ↔ Document Matching)
-- ──────────────────────────────────────────────
-- A single payment can be allocated across multiple invoices.
-- A single invoice can have multiple partial payments.

CREATE TABLE banking.payment_allocation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id),
    payment_id          UUID NOT NULL REFERENCES banking.payment(id) ON DELETE CASCADE,
    document_id         UUID NOT NULL REFERENCES invoicing.document(id) ON DELETE RESTRICT,
    allocated_amount    NUMERIC(10,4) NOT NULL,
    base_allocated_amount NUMERIC(10,4) NOT NULL,           -- SGD equivalent
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_allocated_positive CHECK (allocated_amount > 0),
    UNIQUE(payment_id, document_id)
);

COMMENT ON TABLE banking.payment_allocation
    IS 'Maps payments to invoices. Supports partial payments and split allocations.';


-- ──────────────────────────────────────────────
-- 8d. Bank Transaction (Imported Bank Feed)
-- ──────────────────────────────────────────────

CREATE TABLE banking.bank_transaction (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES core.organisation(id) ON DELETE CASCADE,
    bank_account_id     UUID NOT NULL REFERENCES banking.bank_account(id),
    transaction_date    DATE NOT NULL,
    value_date          DATE,
    description         TEXT NOT NULL,
    reference           VARCHAR(100),

    -- Amount: positive = money in (credit), negative = money out (debit)
    amount              NUMERIC(10,4) NOT NULL,
    running_balance     NUMERIC(10,4),                      -- Bank-reported running balance

    -- Reconciliation
    is_reconciled       BOOLEAN NOT NULL DEFAULT FALSE,
    reconciled_at       TIMESTAMPTZ,
    matched_payment_id  UUID REFERENCES banking.payment(id),
    matched_journal_id  UUID REFERENCES journal.entry(id),

    -- Import metadata
    import_batch_id     UUID,
    import_source       VARCHAR(50),                        -- 'CSV', 'OFX', 'MT940', 'API'
    external_id         VARCHAR(100),                       -- Bank's transaction reference

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE banking.bank_transaction
    IS 'Imported bank feed transactions for reconciliation matching.';

CREATE TRIGGER trg_bank_transaction_updated_at
    BEFORE UPDATE ON banking.bank_transaction
    FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


-- ============================================================================
-- §9  AUDIT SCHEMA — Immutable Event Log
-- ============================================================================
-- CRITICAL: This table is APPEND-ONLY.
-- No UPDATE or DELETE grants are ever given to the application role.
-- IRAS requires 5-year record retention.

CREATE TABLE audit.event_log (
    id                  BIGSERIAL PRIMARY KEY,
    org_id              UUID NOT NULL,
    user_id             UUID,                              -- NULL for system-generated events
    session_id          VARCHAR(64),                       -- Django session or JWT jti

    -- What happened
    action              VARCHAR(30) NOT NULL
        CHECK (action IN (
            'CREATE', 'UPDATE', 'DELETE', 'APPROVE', 'VOID',
            'REVERSE', 'FILE', 'SEND', 'RECONCILE', 'LOGIN',
            'LOGOUT', 'EXPORT', 'IMPORT', 'SETTINGS_CHANGE'
        )),
    entity_schema       VARCHAR(30) NOT NULL,              -- 'invoicing', 'journal', 'gst', etc.
    entity_table        VARCHAR(50) NOT NULL,              -- 'document', 'entry', 'return', etc.
    entity_id           UUID NOT NULL,                     -- PK of the affected row

    -- Change data
    old_data            JSONB,                             -- Before state (NULL for CREATE)
    new_data            JSONB,                             -- After state (NULL for DELETE)
    changed_fields      TEXT[],                            -- Array of field names that changed

    -- Context
    ip_address          INET,
    user_agent          TEXT,
    request_path        VARCHAR(500),

    -- Immutable timestamp
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()

    -- NOTE: No updated_at — this table is append-only
);

-- Partition by creation time for performance at scale.
-- In production, consider range-partitioning by YEAR.

COMMENT ON TABLE audit.event_log
    IS 'Immutable, append-only audit trail. IRAS requires 5-year retention. No UPDATE/DELETE grants.';

-- Performance indexes
CREATE INDEX idx_audit_org_date ON audit.event_log (org_id, created_at DESC);
CREATE INDEX idx_audit_entity ON audit.event_log (entity_schema, entity_table, entity_id);
CREATE INDEX idx_audit_user ON audit.event_log (user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit.event_log (action, created_at DESC);


-- ============================================================================
-- §10  STORED PROCEDURES
-- ============================================================================

-- ──────────────────────────────────────────────
-- 10a. GST Calculation Engine
-- ──────────────────────────────────────────────
-- Pure function: computes GST for a given amount and tax code.
-- Mirrors the Python GSTCalculator for consistency.

CREATE OR REPLACE FUNCTION gst.calculate(
    p_amount            NUMERIC(10,4),
    p_tax_code          VARCHAR(10),
    p_is_inclusive       BOOLEAN DEFAULT FALSE,
    p_rate_date          DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    net_amount          NUMERIC(10,4),
    gst_amount          NUMERIC(10,4),
    gross_amount        NUMERIC(10,4),
    applied_rate        NUMERIC(5,4)
)
LANGUAGE plpgsql
IMMUTABLE
PARALLEL SAFE
AS $$
DECLARE
    v_rate NUMERIC(5,4);
BEGIN
    -- Look up the applicable rate for the given date
    SELECT tc.rate INTO v_rate
    FROM gst.tax_code tc
    WHERE tc.code = p_tax_code
        AND tc.is_active = TRUE
        AND tc.effective_from <= p_rate_date
        AND (tc.effective_to IS NULL OR tc.effective_to >= p_rate_date)
    ORDER BY tc.effective_from DESC
    LIMIT 1;

    -- Default to 0 if tax code not found
    IF v_rate IS NULL THEN
        v_rate := 0;
    END IF;

    applied_rate := v_rate;

    IF v_rate = 0 THEN
        net_amount   := ROUND(p_amount, 4);
        gst_amount   := 0;
        gross_amount := ROUND(p_amount, 4);
        RETURN NEXT;
        RETURN;
    END IF;

    IF p_is_inclusive THEN
        -- GST-inclusive: extract using tax fraction
        -- For 9%: GST = Amount × 9/109
        gst_amount   := ROUND(p_amount * v_rate / (1 + v_rate), 4);
        net_amount   := ROUND(p_amount - gst_amount, 4);
        gross_amount := ROUND(p_amount, 4);
    ELSE
        -- GST-exclusive: add on top
        net_amount   := ROUND(p_amount, 4);
        gst_amount   := ROUND(p_amount * v_rate, 4);
        gross_amount := ROUND(net_amount + gst_amount, 4);
    END IF;

    RETURN NEXT;
END;
$$;

COMMENT ON FUNCTION gst.calculate
    IS 'Core GST calculation. Returns net, GST, and gross amounts at NUMERIC(10,4) precision.';


-- ──────────────────────────────────────────────
-- 10b. Invoice Line GST Calculation
-- ──────────────────────────────────────────────

CREATE OR REPLACE FUNCTION gst.calculate_line(
    p_quantity          NUMERIC(10,4),
    p_unit_price        NUMERIC(10,4),
    p_discount_pct      NUMERIC(5,2),
    p_tax_code          VARCHAR(10),
    p_is_inclusive       BOOLEAN DEFAULT FALSE,
    p_rate_date          DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    line_amount         NUMERIC(10,4),
    gst_amount          NUMERIC(10,4),
    total_amount        NUMERIC(10,4),
    applied_rate        NUMERIC(5,4)
)
LANGUAGE plpgsql
IMMUTABLE
PARALLEL SAFE
AS $$
DECLARE
    v_line_amount NUMERIC(10,4);
    v_result RECORD;
BEGIN
    -- Calculate line amount: qty × price × (1 - disc/100)
    v_line_amount := ROUND(
        p_quantity * p_unit_price * (1 - COALESCE(p_discount_pct, 0) / 100.0),
        4
    );

    -- Delegate to core GST calculation
    SELECT g.net_amount, g.gst_amount, g.gross_amount, g.applied_rate
    INTO v_result
    FROM gst.calculate(v_line_amount, p_tax_code, p_is_inclusive, p_rate_date) g;

    line_amount  := v_result.net_amount;
    gst_amount   := v_result.gst_amount;
    total_amount := v_result.gross_amount;
    applied_rate := v_result.applied_rate;

    RETURN NEXT;
END;
$$;

COMMENT ON FUNCTION gst.calculate_line
    IS 'Calculates GST for an invoice line item (qty × price - discount, then apply tax code).';


-- ──────────────────────────────────────────────
-- 10c. Next Document Number (Thread-Safe)
-- ──────────────────────────────────────────────

CREATE OR REPLACE FUNCTION core.next_document_number(
    p_org_id            UUID,
    p_document_type     VARCHAR(30)
)
RETURNS VARCHAR(30)
LANGUAGE plpgsql
AS $$
DECLARE
    v_prefix    VARCHAR(20);
    v_next      BIGINT;
    v_padding   SMALLINT;
    v_number    VARCHAR(30);
BEGIN
    -- Lock the sequence row for this org + type (prevents concurrent gaps)
    SELECT prefix, next_number, padding
    INTO v_prefix, v_next, v_padding
    FROM core.document_sequence
    WHERE org_id = p_org_id AND document_type = p_document_type
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No document sequence configured for org % type %',
            p_org_id, p_document_type;
    END IF;

    -- Build the number string: PREFIX + zero-padded number
    v_number := v_prefix || LPAD(v_next::TEXT, v_padding, '0');

    -- Increment
    UPDATE core.document_sequence
    SET next_number = next_number + 1,
        updated_at = NOW()
    WHERE org_id = p_org_id AND document_type = p_document_type;

    RETURN v_number;
END;
$$;

COMMENT ON FUNCTION core.next_document_number
    IS 'Thread-safe sequential document number generator. Uses SELECT FOR UPDATE to prevent gaps.';


-- ──────────────────────────────────────────────
-- 10d. Validate Journal Entry Balance
-- ──────────────────────────────────────────────
-- Called after all lines are inserted for an entry.
-- Ensures total debits = total credits in base currency.

CREATE OR REPLACE FUNCTION journal.validate_balance(
    p_entry_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_total_debit   NUMERIC(10,4);
    v_total_credit  NUMERIC(10,4);
    v_diff          NUMERIC(10,4);
BEGIN
    SELECT COALESCE(SUM(base_debit), 0),
           COALESCE(SUM(base_credit), 0)
    INTO v_total_debit, v_total_credit
    FROM journal.line
    WHERE entry_id = p_entry_id;

    v_diff := ABS(v_total_debit - v_total_credit);

    -- Allow a tiny rounding tolerance of 0.0001 (1/10th of a cent)
    IF v_diff > 0.0001 THEN
        RAISE EXCEPTION 'Journal entry % is UNBALANCED. Debit=%, Credit=%, Diff=%',
            p_entry_id, v_total_debit, v_total_credit, v_diff;
    END IF;

    RETURN TRUE;
END;
$$;

COMMENT ON FUNCTION journal.validate_balance
    IS 'Validates that a journal entry balances (debits = credits in base currency). Raises exception if not.';


-- ──────────────────────────────────────────────
-- 10e. Compute GST F5 Return from Journal Data
-- ──────────────────────────────────────────────

CREATE OR REPLACE FUNCTION gst.compute_f5_return(
    p_org_id            UUID,
    p_period_start      DATE,
    p_period_end        DATE
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_return_id     UUID;
    v_box1          NUMERIC(10,4) := 0;
    v_box2          NUMERIC(10,4) := 0;
    v_box3          NUMERIC(10,4) := 0;
    v_box5          NUMERIC(10,4) := 0;
    v_box6          NUMERIC(10,4) := 0;
    v_box7          NUMERIC(10,4) := 0;
    v_box13         NUMERIC(10,4) := 0;
    v_box14         NUMERIC(10,4) := 0;
    v_filing_due    DATE;
BEGIN
    -- Filing due date: one month after period end
    v_filing_due := (p_period_end + INTERVAL '1 month')::DATE;

    -- ═══════════════════════════════════════════
    -- SALES DOCUMENTS (Invoices + Debit Notes, minus Credit Notes)
    -- ═══════════════════════════════════════════

    -- Box 1: Standard-rated supplies (value excl. GST)
    SELECT COALESCE(SUM(
        CASE
            WHEN d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE')
                THEN dl.base_line_amount
            WHEN d.document_type = 'SALES_CREDIT_NOTE'
                THEN -dl.base_line_amount
            ELSE 0
        END
    ), 0)
    INTO v_box1
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE', 'SALES_CREDIT_NOTE')
        AND tc.f5_supply_box = 1;

    -- Box 2: Zero-rated supplies
    SELECT COALESCE(SUM(
        CASE
            WHEN d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE')
                THEN dl.base_line_amount
            WHEN d.document_type = 'SALES_CREDIT_NOTE'
                THEN -dl.base_line_amount
            ELSE 0
        END
    ), 0)
    INTO v_box2
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE', 'SALES_CREDIT_NOTE')
        AND tc.f5_supply_box = 2;

    -- Box 3: Exempt supplies
    SELECT COALESCE(SUM(
        CASE
            WHEN d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE')
                THEN dl.base_line_amount
            WHEN d.document_type = 'SALES_CREDIT_NOTE'
                THEN -dl.base_line_amount
            ELSE 0
        END
    ), 0)
    INTO v_box3
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE', 'SALES_CREDIT_NOTE')
        AND tc.f5_supply_box = 3;

    -- ═══════════════════════════════════════════
    -- PURCHASE DOCUMENTS
    -- ═══════════════════════════════════════════

    -- Box 5: Total taxable purchases
    SELECT COALESCE(SUM(
        CASE
            WHEN d.document_type IN ('PURCHASE_INVOICE', 'PURCHASE_DEBIT_NOTE')
                THEN dl.base_line_amount
            WHEN d.document_type = 'PURCHASE_CREDIT_NOTE'
                THEN -dl.base_line_amount
            ELSE 0
        END
    ), 0)
    INTO v_box5
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND d.document_type IN ('PURCHASE_INVOICE', 'PURCHASE_DEBIT_NOTE', 'PURCHASE_CREDIT_NOTE')
        AND tc.f5_purchase_box = 5;

    -- ═══════════════════════════════════════════
    -- TAX AMOUNTS
    -- ═══════════════════════════════════════════

    -- Box 6: Output tax due
    SELECT COALESCE(SUM(
        CASE
            WHEN d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE')
                THEN dl.base_gst_amount
            WHEN d.document_type = 'SALES_CREDIT_NOTE'
                THEN -dl.base_gst_amount
            ELSE 0
        END
    ), 0)
    INTO v_box6
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE', 'SALES_CREDIT_NOTE')
        AND tc.f5_tax_box = 6;

    -- Box 7: Input tax claimable (only claimable codes, exclude blocked)
    SELECT COALESCE(SUM(
        CASE
            WHEN d.document_type IN ('PURCHASE_INVOICE', 'PURCHASE_DEBIT_NOTE')
                THEN dl.base_gst_amount
            WHEN d.document_type = 'PURCHASE_CREDIT_NOTE'
                THEN -dl.base_gst_amount
            ELSE 0
        END
    ), 0)
    INTO v_box7
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND d.document_type IN ('PURCHASE_INVOICE', 'PURCHASE_DEBIT_NOTE', 'PURCHASE_CREDIT_NOTE')
        AND tc.f5_tax_box = 7
        AND tc.is_claimable = TRUE;

    -- ═══════════════════════════════════════════
    -- Box 13: Total revenue (all supply types including out-of-scope)
    -- ═══════════════════════════════════════════

    SELECT COALESCE(SUM(
        CASE
            WHEN d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE')
                THEN dl.base_line_amount
            WHEN d.document_type = 'SALES_CREDIT_NOTE'
                THEN -dl.base_line_amount
            ELSE 0
        END
    ), 0)
    INTO v_box13
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND d.document_type IN ('SALES_INVOICE', 'SALES_DEBIT_NOTE', 'SALES_CREDIT_NOTE');

    -- Box 14: Reverse charge supplies
    SELECT COALESCE(SUM(dl.base_line_amount), 0)
    INTO v_box14
    FROM invoicing.document d
    JOIN invoicing.document_line dl ON dl.document_id = d.id
    JOIN gst.tax_code tc ON tc.id = dl.tax_code_id
    WHERE d.org_id = p_org_id
        AND d.document_date BETWEEN p_period_start AND p_period_end
        AND d.status NOT IN ('DRAFT', 'VOID')
        AND tc.is_reverse_charge = TRUE;

    -- ═══════════════════════════════════════════
    -- INSERT THE RETURN
    -- ═══════════════════════════════════════════

    INSERT INTO gst.return (
        org_id, return_type, period_start, period_end, filing_due_date,
        box1_std_rated_supplies,
        box2_zero_rated_supplies,
        box3_exempt_supplies,
        box4_total_supplies,
        box5_total_taxable_purchases,
        box6_output_tax,
        box7_input_tax_claimable,
        box8_net_gst,
        box13_total_revenue,
        box14_reverse_charge_supplies,
        status,
        computed_at
    ) VALUES (
        p_org_id, 'F5', p_period_start, p_period_end, v_filing_due,
        v_box1,
        v_box2,
        v_box3,
        v_box1 + v_box2 + v_box3,                         -- Box 4 = sum of 1+2+3
        v_box5,
        v_box6,
        v_box7,
        v_box6 - v_box7,                                   -- Box 8 = Box 6 - Box 7
        v_box13,
        v_box14,
        'COMPUTED',
        NOW()
    )
    RETURNING id INTO v_return_id;

    RETURN v_return_id;
END;
$$;

COMMENT ON FUNCTION gst.compute_f5_return
    IS 'Auto-computes a GST F5 return from invoicing data for a given period. Populates all box values.';


-- ──────────────────────────────────────────────
-- 10f. Generate Fiscal Periods for a Fiscal Year
-- ──────────────────────────────────────────────

CREATE OR REPLACE FUNCTION core.generate_fiscal_periods(
    p_fiscal_year_id UUID
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_org_id        UUID;
    v_start_date    DATE;
    v_end_date      DATE;
    v_period_start  DATE;
    v_period_end    DATE;
    v_period_num    SMALLINT := 1;
BEGIN
    SELECT fy.org_id, fy.start_date, fy.end_date
    INTO v_org_id, v_start_date, v_end_date
    FROM core.fiscal_year fy
    WHERE fy.id = p_fiscal_year_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Fiscal year % not found', p_fiscal_year_id;
    END IF;

    v_period_start := v_start_date;

    -- Generate monthly periods
    WHILE v_period_start < v_end_date AND v_period_num <= 12 LOOP
        -- Period ends at end of month or fiscal year end, whichever is earlier
        v_period_end := LEAST(
            (v_period_start + INTERVAL '1 month' - INTERVAL '1 day')::DATE,
            v_end_date
        );

        INSERT INTO core.fiscal_period (
            fiscal_year_id, org_id, period_number,
            start_date, end_date, is_open, is_adjustment
        ) VALUES (
            p_fiscal_year_id, v_org_id, v_period_num,
            v_period_start, v_period_end, TRUE, FALSE
        );

        v_period_num := v_period_num + 1;
        v_period_start := (v_period_end + INTERVAL '1 day')::DATE;
    END LOOP;

    -- Generate period 13 (adjustment period — same dates as last regular period)
    INSERT INTO core.fiscal_period (
        fiscal_year_id, org_id, period_number,
        start_date, end_date, is_open, is_adjustment
    ) VALUES (
        p_fiscal_year_id, v_org_id, 13,
        v_end_date, v_end_date, FALSE, TRUE  -- Single-day period
    );
END;
$$;

COMMENT ON FUNCTION core.generate_fiscal_periods
    IS 'Auto-generates 12 monthly periods + 1 adjustment period for a fiscal year.';


-- ============================================================================
-- §11  TRIGGERS
-- ============================================================================

-- ──────────────────────────────────────────────
-- 11a. Generic Audit Trigger Function
-- ──────────────────────────────────────────────
-- Attaches to tables requiring audit logging.
-- Captures old/new state as JSONB, detects changed fields.

CREATE OR REPLACE FUNCTION audit.log_change()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_action        VARCHAR(30);
    v_old_data      JSONB := NULL;
    v_new_data      JSONB := NULL;
    v_changed       TEXT[] := '{}';
    v_org_id        UUID;
    v_entity_id     UUID;
    v_key           TEXT;
BEGIN
    -- Determine action
    IF TG_OP = 'INSERT' THEN
        v_action    := 'CREATE';
        v_new_data  := to_jsonb(NEW);
        v_org_id    := NEW.org_id;
        v_entity_id := NEW.id;
    ELSIF TG_OP = 'UPDATE' THEN
        v_action    := 'UPDATE';
        v_old_data  := to_jsonb(OLD);
        v_new_data  := to_jsonb(NEW);
        v_org_id    := NEW.org_id;
        v_entity_id := NEW.id;

        -- Detect changed fields
        FOR v_key IN SELECT jsonb_object_keys(v_new_data) LOOP
            IF v_old_data->v_key IS DISTINCT FROM v_new_data->v_key THEN
                v_changed := array_append(v_changed, v_key);
            END IF;
        END LOOP;
    ELSIF TG_OP = 'DELETE' THEN
        v_action    := 'DELETE';
        v_old_data  := to_jsonb(OLD);
        v_org_id    := OLD.org_id;
        v_entity_id := OLD.id;
    END IF;

    -- Insert audit record
    INSERT INTO audit.event_log (
        org_id, user_id, action,
        entity_schema, entity_table, entity_id,
        old_data, new_data, changed_fields,
        created_at
    ) VALUES (
        v_org_id,
        core.current_user_id(),
        v_action,
        TG_TABLE_SCHEMA,
        TG_TABLE_NAME,
        v_entity_id,
        v_old_data,
        v_new_data,
        v_changed,
        NOW()
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION audit.log_change()
    IS 'Generic audit trigger. Captures before/after state as JSONB with changed field detection.';


-- ──────────────────────────────────────────────
-- 11b. Attach Audit Triggers to Critical Tables
-- ──────────────────────────────────────────────

-- Organisation changes
CREATE TRIGGER trg_audit_organisation
    AFTER INSERT OR UPDATE OR DELETE ON core.organisation
    FOR EACH ROW EXECUTE FUNCTION audit.log_change();

-- Invoice document changes
CREATE TRIGGER trg_audit_document
    AFTER INSERT OR UPDATE OR DELETE ON invoicing.document
    FOR EACH ROW EXECUTE FUNCTION audit.log_change();

-- Invoice line changes
CREATE TRIGGER trg_audit_document_line
    AFTER INSERT OR UPDATE OR DELETE ON invoicing.document_line
    FOR EACH ROW EXECUTE FUNCTION audit.log_change();

-- Journal entries (should only be INSERT, never UPDATE/DELETE)
CREATE TRIGGER trg_audit_journal_entry
    AFTER INSERT ON journal.entry
    FOR EACH ROW EXECUTE FUNCTION audit.log_change();

-- Journal lines (should only be INSERT)
CREATE TRIGGER trg_audit_journal_line
    AFTER INSERT ON journal.line
    FOR EACH ROW EXECUTE FUNCTION audit.log_change();

-- GST returns
CREATE TRIGGER trg_audit_gst_return
    AFTER INSERT OR UPDATE ON gst.return
    FOR EACH ROW EXECUTE FUNCTION audit.log_change();

-- Payments
CREATE TRIGGER trg_audit_payment
    AFTER INSERT OR UPDATE OR DELETE ON banking.payment
    FOR EACH ROW EXECUTE FUNCTION audit.log_change();

-- Contact changes
CREATE TRIGGER trg_audit_contact
    AFTER INSERT OR UPDATE OR DELETE ON invoicing.contact
    FOR EACH ROW EXECUTE FUNCTION audit.log_change();


-- ──────────────────────────────────────────────
-- 11c. Prevent Journal Entry Mutation Trigger
-- ──────────────────────────────────────────────
-- Journal entries are immutable. Only the is_reversed flag may be updated.

CREATE OR REPLACE FUNCTION journal.prevent_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Allow only is_reversed and reversed_by_id to change
    IF OLD.entry_number IS DISTINCT FROM NEW.entry_number
       OR OLD.entry_date IS DISTINCT FROM NEW.entry_date
       OR OLD.narration IS DISTINCT FROM NEW.narration
       OR OLD.source_type IS DISTINCT FROM NEW.source_type
       OR OLD.source_id IS DISTINCT FROM NEW.source_id
       OR OLD.posted_by IS DISTINCT FROM NEW.posted_by
    THEN
        RAISE EXCEPTION 'Journal entry % is immutable. Create a reversal instead.', OLD.id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_journal_entry_immutable
    BEFORE UPDATE ON journal.entry
    FOR EACH ROW EXECUTE FUNCTION journal.prevent_mutation();


-- ──────────────────────────────────────────────
-- 11d. Prevent Journal Line Mutation/Deletion
-- ──────────────────────────────────────────────

CREATE OR REPLACE FUNCTION journal.prevent_line_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION 'Journal lines are immutable. Create a reversal entry instead.';
    ELSIF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Journal lines cannot be deleted. Create a reversal entry instead.';
    END IF;
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_journal_line_immutable
    BEFORE UPDATE OR DELETE ON journal.line
    FOR EACH ROW EXECUTE FUNCTION journal.prevent_line_mutation();


-- ============================================================================
-- §12  ROW-LEVEL SECURITY POLICIES
-- ============================================================================
-- Multi-tenant data isolation enforced at the database level.
-- Django middleware sets: SET LOCAL app.current_org_id = '<uuid>';
-- Every query is automatically filtered to the current tenant.

-- ──────────────────────────────────────────────
-- Helper: Apply RLS to a table with org_id column
-- ──────────────────────────────────────────────

-- Enable RLS and create policies for all tenant-scoped tables.
-- We use a DO block for DRY application.

DO $$
DECLARE
    v_table RECORD;
BEGIN
    -- List of all tables that have an org_id column and need RLS
    FOR v_table IN
        SELECT schemaname, tablename
        FROM (VALUES
            ('core', 'organisation'),
            ('core', 'fiscal_year'),
            ('core', 'fiscal_period'),
            ('core', 'exchange_rate'),
            ('core', 'document_sequence'),
            ('core', 'organisation_setting'),
            ('coa', 'account'),
            ('gst', 'return'),
            ('gst', 'threshold_snapshot'),
            ('journal', 'entry'),
            ('journal', 'line'),
            ('invoicing', 'contact'),
            ('invoicing', 'document'),
            ('invoicing', 'document_line'),
            ('invoicing', 'document_attachment'),
            ('banking', 'bank_account'),
            ('banking', 'payment'),
            ('banking', 'payment_allocation'),
            ('banking', 'bank_transaction')
        ) AS t(schemaname, tablename)
    LOOP
        -- Enable RLS
        EXECUTE format(
            'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',
            v_table.schemaname, v_table.tablename
        );

        -- Force RLS even for table owner (defense in depth)
        EXECUTE format(
            'ALTER TABLE %I.%I FORCE ROW LEVEL SECURITY',
            v_table.schemaname, v_table.tablename
        );

        -- SELECT policy: user can only see rows belonging to their org
        EXECUTE format(
            'CREATE POLICY rls_select_%s ON %I.%I FOR SELECT USING (org_id = core.current_org_id())',
            v_table.tablename, v_table.schemaname, v_table.tablename
        );

        -- INSERT policy: user can only insert rows into their org
        EXECUTE format(
            'CREATE POLICY rls_insert_%s ON %I.%I FOR INSERT WITH CHECK (org_id = core.current_org_id())',
            v_table.tablename, v_table.schemaname, v_table.tablename
        );

        -- UPDATE policy: user can only update rows belonging to their org
        EXECUTE format(
            'CREATE POLICY rls_update_%s ON %I.%I FOR UPDATE USING (org_id = core.current_org_id())',
            v_table.tablename, v_table.schemaname, v_table.tablename
        );

        -- DELETE policy: user can only delete rows belonging to their org
        EXECUTE format(
            'CREATE POLICY rls_delete_%s ON %I.%I FOR DELETE USING (org_id = core.current_org_id())',
            v_table.tablename, v_table.schemaname, v_table.tablename
        );

        RAISE NOTICE 'RLS enabled on %.%', v_table.schemaname, v_table.tablename;
    END LOOP;
END $$;

-- Special case: core.organisation needs its own policy
-- User can see the org record matching their session org_id
-- (using 'id' instead of 'org_id' since organisation IS the tenant root)
DROP POLICY IF EXISTS rls_select_organisation ON core.organisation;
DROP POLICY IF EXISTS rls_insert_organisation ON core.organisation;
DROP POLICY IF EXISTS rls_update_organisation ON core.organisation;
DROP POLICY IF EXISTS rls_delete_organisation ON core.organisation;

CREATE POLICY rls_select_organisation ON core.organisation
    FOR SELECT USING (id = core.current_org_id());
CREATE POLICY rls_insert_organisation ON core.organisation
    FOR INSERT WITH CHECK (TRUE);  -- Org creation happens before session context exists
CREATE POLICY rls_update_organisation ON core.organisation
    FOR UPDATE USING (id = core.current_org_id());
CREATE POLICY rls_delete_organisation ON core.organisation
    FOR DELETE USING (id = core.current_org_id());

-- Global reference tables: no RLS needed
-- core.currency, core.role, coa.account_type, coa.account_sub_type, gst.tax_code
-- These are shared across all tenants and are read-only for app users.


-- ============================================================================
-- §13  INDEXES (Performance-Critical)
-- ============================================================================
-- Focused on the most common query patterns:
-- - Invoice lists (by org, status, date)
-- - Journal queries (by org, account, period)
-- - Contact search (by name, text search)
-- - GST return computation (by org, date range, tax code)
-- - Bank reconciliation (by org, bank account, date)

-- ── Core ──
CREATE INDEX idx_user_org_user ON core.user_organisation(user_id);
CREATE INDEX idx_user_org_org ON core.user_organisation(org_id);
CREATE INDEX idx_fiscal_year_org ON core.fiscal_year(org_id, start_date);
CREATE INDEX idx_fiscal_period_org ON core.fiscal_period(org_id, start_date, end_date);
CREATE INDEX idx_exchange_rate_lookup ON core.exchange_rate(org_id, currency_code, rate_date DESC);

-- ── Chart of Accounts ──
CREATE INDEX idx_account_org ON coa.account(org_id, code);
CREATE INDEX idx_account_parent ON coa.account(parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX idx_account_type ON coa.account(org_id, account_type_id);

-- ── GST ──
CREATE INDEX idx_tax_code_lookup ON gst.tax_code(code, effective_from DESC)
    WHERE is_active = TRUE;
CREATE INDEX idx_gst_return_org ON gst.return(org_id, period_start, period_end);

-- ── Journal ──
CREATE INDEX idx_journal_entry_org_date ON journal.entry(org_id, entry_date DESC);
CREATE INDEX idx_journal_entry_source ON journal.entry(source_type, source_id)
    WHERE source_id IS NOT NULL;
CREATE INDEX idx_journal_entry_period ON journal.entry(org_id, fiscal_period_id);
CREATE INDEX idx_journal_line_entry ON journal.line(entry_id);
CREATE INDEX idx_journal_line_account ON journal.line(account_id, org_id);
CREATE INDEX idx_journal_line_tax_code ON journal.line(tax_code_id)
    WHERE tax_code_id IS NOT NULL;

-- ── Invoicing ──
CREATE INDEX idx_contact_org_name ON invoicing.contact(org_id, name);
CREATE INDEX idx_contact_org_type ON invoicing.contact(org_id, contact_type);
CREATE INDEX idx_contact_search ON invoicing.contact
    USING gin (name gin_trgm_ops);  -- Trigram search for fuzzy matching

CREATE INDEX idx_document_org_status ON invoicing.document(org_id, status, document_date DESC);
CREATE INDEX idx_document_org_type ON invoicing.document(org_id, document_type, document_date DESC);
CREATE INDEX idx_document_contact ON invoicing.document(contact_id);
CREATE INDEX idx_document_due_date ON invoicing.document(org_id, due_date)
    WHERE status IN ('APPROVED', 'SENT', 'PARTIALLY_PAID');  -- For aging reports
CREATE INDEX idx_document_invoicenow ON invoicing.document(org_id, invoicenow_status)
    WHERE invoicenow_status NOT IN ('NOT_APPLICABLE');

CREATE INDEX idx_document_line_doc ON invoicing.document_line(document_id);
CREATE INDEX idx_document_line_tax ON invoicing.document_line(tax_code_id);
CREATE INDEX idx_document_line_account ON invoicing.document_line(account_id);

-- Composite index for GST F5 computation (the heaviest query)
CREATE INDEX idx_docline_gst_compute ON invoicing.document_line(org_id, tax_code_id)
    INCLUDE (base_line_amount, base_gst_amount);

-- ── Banking ──
CREATE INDEX idx_bank_account_org ON banking.bank_account(org_id);
CREATE INDEX idx_payment_org_date ON banking.payment(org_id, payment_date DESC);
CREATE INDEX idx_payment_contact ON banking.payment(contact_id);
CREATE INDEX idx_payment_alloc_payment ON banking.payment_allocation(payment_id);
CREATE INDEX idx_payment_alloc_document ON banking.payment_allocation(document_id);
CREATE INDEX idx_bank_txn_account_date ON banking.bank_transaction(bank_account_id, transaction_date DESC);
CREATE INDEX idx_bank_txn_unreconciled ON banking.bank_transaction(bank_account_id, transaction_date)
    WHERE is_reconciled = FALSE;  -- For reconciliation UI


-- ============================================================================
-- §14  SEED DATA
-- ============================================================================

-- ──────────────────────────────────────────────
-- 14a. System Roles
-- ──────────────────────────────────────────────

INSERT INTO core.role (name, description, is_system,
    can_manage_org, can_manage_users, can_manage_coa,
    can_create_invoices, can_approve_invoices, can_void_invoices,
    can_create_journals, can_manage_banking, can_file_gst,
    can_view_reports, can_export_data
) VALUES
    ('Owner', 'Business owner with full access',
        TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
    ('Admin', 'Administrator — manages settings and users',
        TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
    ('Accountant', 'Full accounting access without org management',
        TRUE, FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
    ('Bookkeeper', 'Day-to-day transaction entry',
        TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, TRUE, FALSE, TRUE, FALSE),
    ('Viewer', 'Read-only access to reports and documents',
        TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, FALSE);


-- ──────────────────────────────────────────────
-- 14b. Account Types (Fixed — System-Wide)
-- ──────────────────────────────────────────────

INSERT INTO coa.account_type (id, code, name, normal_balance, classification, display_order, is_debit_positive) VALUES
    (1, 'ASSET',      'Asset',      'DEBIT',  'BALANCE_SHEET',      1, TRUE),
    (2, 'LIABILITY',   'Liability',  'CREDIT', 'BALANCE_SHEET',      2, FALSE),
    (3, 'EQUITY',      'Equity',     'CREDIT', 'BALANCE_SHEET',      3, FALSE),
    (4, 'REVENUE',     'Revenue',    'CREDIT', 'INCOME_STATEMENT',   4, FALSE),
    (5, 'COGS',        'Cost of Goods Sold', 'DEBIT', 'INCOME_STATEMENT', 5, TRUE),
    (6, 'EXPENSE',     'Expense',    'DEBIT',  'INCOME_STATEMENT',   6, TRUE),
    (7, 'OTHER_INCOME','Other Income','CREDIT','INCOME_STATEMENT',   7, FALSE),
    (8, 'OTHER_EXPENSE','Other Expense','DEBIT','INCOME_STATEMENT',  8, TRUE);


-- ──────────────────────────────────────────────
-- 14c. Account Sub-Types
-- ──────────────────────────────────────────────

INSERT INTO coa.account_sub_type (id, account_type_id, code, name, display_order) VALUES
    -- Assets
    (101, 1, 'CURRENT_ASSET',       'Current Asset',                1),
    (102, 1, 'CASH_AND_BANK',       'Cash and Bank',                2),
    (103, 1, 'ACCOUNTS_RECEIVABLE', 'Accounts Receivable',          3),
    (104, 1, 'INVENTORY',           'Inventory',                    4),
    (105, 1, 'PREPAID',             'Prepaid Expenses',             5),
    (106, 1, 'FIXED_ASSET',         'Fixed Asset',                  6),
    (107, 1, 'ACCUM_DEPRECIATION',  'Accumulated Depreciation',     7),
    (108, 1, 'OTHER_ASSET',         'Other Asset',                  8),

    -- Liabilities
    (201, 2, 'CURRENT_LIABILITY',    'Current Liability',           1),
    (202, 2, 'ACCOUNTS_PAYABLE',     'Accounts Payable',            2),
    (203, 2, 'TAX_PAYABLE',          'Tax Payable',                 3),
    (204, 2, 'ACCRUED_LIABILITY',    'Accrued Liabilities',         4),
    (205, 2, 'LONG_TERM_LIABILITY',  'Long-Term Liability',         5),
    (206, 2, 'OTHER_LIABILITY',      'Other Liability',             6),

    -- Equity
    (301, 3, 'OWNER_EQUITY',        'Owner''s Equity / Share Capital', 1),
    (302, 3, 'RETAINED_EARNINGS',   'Retained Earnings',           2),
    (303, 3, 'DRAWINGS',            'Owner''s Drawings',            3),
    (304, 3, 'OTHER_EQUITY',        'Other Equity',                4),

    -- Revenue
    (401, 4, 'OPERATING_REVENUE',   'Operating Revenue',           1),
    (402, 4, 'SERVICE_REVENUE',     'Service Revenue',             2),

    -- COGS
    (501, 5, 'DIRECT_COSTS',        'Direct Costs',                1),

    -- Expenses
    (601, 6, 'PAYROLL',             'Payroll & Employee Benefits',  1),
    (602, 6, 'OPERATING_EXPENSE',   'Operating Expense',            2),
    (603, 6, 'ADMIN_EXPENSE',       'Administrative Expense',       3),
    (604, 6, 'SELLING_EXPENSE',     'Selling & Marketing Expense',  4),
    (605, 6, 'FINANCIAL_EXPENSE',   'Financial Expense',            5),
    (606, 6, 'DEPRECIATION',        'Depreciation & Amortisation',  6),

    -- Other Income
    (701, 7, 'NON_OPERATING_INCOME','Non-Operating Income',         1),

    -- Other Expense
    (801, 8, 'NON_OPERATING_EXPENSE','Non-Operating Expense',       1);


-- ──────────────────────────────────────────────
-- 14d. Currencies (Key Currencies for Singapore SMBs)
-- ──────────────────────────────────────────────

INSERT INTO core.currency (code, name, symbol, decimal_places, is_active) VALUES
    ('SGD', 'Singapore Dollar',     'S$',  2, TRUE),
    ('USD', 'US Dollar',            'US$', 2, TRUE),
    ('EUR', 'Euro',                 '€',   2, TRUE),
    ('GBP', 'British Pound',        '£',   2, TRUE),
    ('MYR', 'Malaysian Ringgit',    'RM',  2, TRUE),
    ('IDR', 'Indonesian Rupiah',    'Rp',  0, TRUE),   -- No cents
    ('THB', 'Thai Baht',            '฿',   2, TRUE),
    ('PHP', 'Philippine Peso',      '₱',   2, TRUE),
    ('VND', 'Vietnamese Dong',      '₫',   0, TRUE),   -- No cents
    ('CNY', 'Chinese Yuan',         '¥',   2, TRUE),
    ('JPY', 'Japanese Yen',         '¥',   0, TRUE),   -- No cents
    ('KRW', 'South Korean Won',     '₩',   0, TRUE),   -- No cents
    ('HKD', 'Hong Kong Dollar',     'HK$', 2, TRUE),
    ('TWD', 'New Taiwan Dollar',    'NT$', 2, TRUE),
    ('AUD', 'Australian Dollar',    'A$',  2, TRUE),
    ('NZD', 'New Zealand Dollar',   'NZ$', 2, TRUE),
    ('INR', 'Indian Rupee',         '₹',   2, TRUE),
    ('AED', 'UAE Dirham',           'AED', 2, TRUE),
    ('CHF', 'Swiss Franc',          'CHF', 2, TRUE),
    ('CAD', 'Canadian Dollar',      'C$',  2, TRUE);


-- ──────────────────────────────────────────────
-- 14e. GST Tax Codes (Singapore IRAS Classification)
-- ──────────────────────────────────────────────
-- Current rate: 9% effective 1 Jan 2024.
-- Historical rates preserved for audit compliance.

-- ── OUTPUT (Sales) Tax Codes ──
INSERT INTO gst.tax_code (
    code, description, rate,
    is_input, is_output, is_claimable, is_reverse_charge,
    effective_from, effective_to,
    f5_supply_box, f5_purchase_box, f5_tax_box,
    display_order
) VALUES
    -- Standard-Rated Supply @ 9%
    ('SR',   'Standard-Rated Supply (9%)',                     0.0900,
     FALSE, TRUE, TRUE, FALSE,
     '2024-01-01', NULL,
     1, NULL, 6,
     10),

    -- Zero-Rated Supply (exports, international services)
    ('ZR',   'Zero-Rated Supply (0%)',                         0.0000,
     FALSE, TRUE, TRUE, FALSE,
     '2024-01-01', NULL,
     2, NULL, NULL,
     20),

    -- Exempt Supply (financial services, residential property)
    ('ES',   'Exempt Supply',                                  0.0000,
     FALSE, TRUE, TRUE, FALSE,
     '2024-01-01', NULL,
     3, NULL, NULL,
     30),

    -- Out-of-Scope Supply (not subject to GST)
    ('OS',   'Out-of-Scope Supply',                            0.0000,
     FALSE, TRUE, TRUE, FALSE,
     '2024-01-01', NULL,
     NULL, NULL, NULL,
     40);

-- ── INPUT (Purchase) Tax Codes ──
INSERT INTO gst.tax_code (
    code, description, rate,
    is_input, is_output, is_claimable, is_reverse_charge,
    effective_from, effective_to,
    f5_supply_box, f5_purchase_box, f5_tax_box,
    display_order
) VALUES
    -- Taxable Purchase @ 9% (claimable)
    ('TX',   'Taxable Purchase (9%)',                          0.0900,
     TRUE, FALSE, TRUE, FALSE,
     '2024-01-01', NULL,
     NULL, 5, 7,
     50),

    -- Taxable Purchase — Input Tax Denied (non-claimable)
    ('TX-E', 'Taxable Purchase — Input Tax Denied',            0.0900,
     TRUE, FALSE, FALSE, FALSE,
     '2024-01-01', NULL,
     NULL, 5, NULL,
     55),

    -- Blocked Input Tax (motor car, medical, etc.)
    ('BL',   'Blocked Input Tax (Reg 26/27)',                  0.0900,
     TRUE, FALSE, FALSE, FALSE,
     '2024-01-01', NULL,
     NULL, NULL, NULL,
     60),

    -- Zero-Rated Purchase (imports under approved schemes)
    ('ZP',   'Zero-Rated Purchase',                            0.0000,
     TRUE, FALSE, TRUE, FALSE,
     '2024-01-01', NULL,
     NULL, 5, NULL,
     70),

    -- Exempt Purchase
    ('EP',   'Exempt Purchase',                                0.0000,
     TRUE, FALSE, FALSE, FALSE,
     '2024-01-01', NULL,
     NULL, NULL, NULL,
     80),

    -- Out-of-Scope Purchase
    ('OP',   'Out-of-Scope Purchase',                          0.0000,
     TRUE, FALSE, FALSE, FALSE,
     '2024-01-01', NULL,
     NULL, NULL, NULL,
     90),

    -- Reverse Charge (imported services by RC businesses)
    ('RS',   'Reverse Charge (9%)',                            0.0900,
     TRUE, FALSE, TRUE, TRUE,
     '2024-01-01', NULL,
     NULL, 5, 7,
     95);

-- ── SPECIAL: Non-Applicable (for non-GST-registered businesses) ──
INSERT INTO gst.tax_code (
    code, description, rate,
    is_input, is_output, is_claimable, is_reverse_charge,
    effective_from, effective_to,
    f5_supply_box, f5_purchase_box, f5_tax_box,
    display_order
) VALUES
    ('NA',   'Not Applicable (Non-GST Registered)',            0.0000,
     FALSE, FALSE, FALSE, FALSE,
     '2024-01-01', NULL,
     NULL, NULL, NULL,
     100);

-- ── HISTORICAL: 8% rate (1 Jan 2023 to 31 Dec 2023) for retrospective lookups ──
INSERT INTO gst.tax_code (
    code, description, rate,
    is_input, is_output, is_claimable, is_reverse_charge,
    effective_from, effective_to,
    f5_supply_box, f5_purchase_box, f5_tax_box,
    display_order
) VALUES
    ('SR',   'Standard-Rated Supply (8%)',                     0.0800,
     FALSE, TRUE, TRUE, FALSE,
     '2023-01-01', '2023-12-31',
     1, NULL, 6,
     10),
    ('TX',   'Taxable Purchase (8%)',                          0.0800,
     TRUE, FALSE, TRUE, FALSE,
     '2023-01-01', '2023-12-31',
     NULL, 5, 7,
     50);

-- ── HISTORICAL: 7% rate (1 Jul 2007 to 31 Dec 2022) ──
INSERT INTO gst.tax_code (
    code, description, rate,
    is_input, is_output, is_claimable, is_reverse_charge,
    effective_from, effective_to,
    f5_supply_box, f5_purchase_box, f5_tax_box,
    display_order
) VALUES
    ('SR',   'Standard-Rated Supply (7%)',                     0.0700,
     FALSE, TRUE, TRUE, FALSE,
     '2007-07-01', '2022-12-31',
     1, NULL, 6,
     10),
    ('TX',   'Taxable Purchase (7%)',                          0.0700,
     TRUE, FALSE, TRUE, FALSE,
     '2007-07-01', '2022-12-31',
     NULL, 5, 7,
     50);


-- ──────────────────────────────────────────────
-- 14f. Default Chart of Accounts Template
-- ──────────────────────────────────────────────
-- This is a TEMPLATE stored as a function, not directly in a table.
-- Called when a new organisation is created to seed their COA.
-- Aligned with SFRS for Small Entities classification.

CREATE OR REPLACE FUNCTION core.seed_default_chart_of_accounts(
    p_org_id UUID,
    p_is_gst_registered BOOLEAN DEFAULT FALSE
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    -- ═══════════════════════════════════════════
    -- ASSETS (1000-1999)
    -- ═══════════════════════════════════════════

    -- Header: Current Assets
    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, is_header, is_system) VALUES
        (p_org_id, '1000', 'Current Assets', 1, 101, TRUE, TRUE);

    -- Cash & Bank
    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, parent_id, is_bank)
    SELECT p_org_id, v.code, v.name, 1, 102,
           (SELECT id FROM coa.account WHERE org_id = p_org_id AND code = '1000'), v.is_bank
    FROM (VALUES
        ('1010', 'Cash on Hand',             FALSE),
        ('1020', 'Petty Cash',               FALSE),
        ('1100', 'Bank Account — SGD',       TRUE),
        ('1110', 'Bank Account — USD',       TRUE),
        ('1120', 'Bank Account — Other',     TRUE)
    ) AS v(code, name, is_bank);

    -- Accounts Receivable
    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, parent_id, is_system, is_control)
    SELECT p_org_id, v.code, v.name, 1, 103,
           (SELECT id FROM coa.account WHERE org_id = p_org_id AND code = '1000'), v.is_system, v.is_control
    FROM (VALUES
        ('1200', 'Accounts Receivable',           TRUE, TRUE),
        ('1210', 'Accounts Receivable — Foreign',  FALSE, TRUE)
    ) AS v(code, name, is_system, is_control);

    -- Inventory
    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, parent_id) VALUES
        (p_org_id, '1300', 'Inventory', 1, 104,
         (SELECT id FROM coa.account WHERE org_id = p_org_id AND code = '1000'));

    -- Prepaid
    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, parent_id)
    SELECT p_org_id, v.code, v.name, 1, 105,
           (SELECT id FROM coa.account WHERE org_id = p_org_id AND code = '1000')
    FROM (VALUES
        ('1400', 'Prepaid Expenses'),
        ('1410', 'Deposits Paid')
    ) AS v(code, name);

    -- GST Input Tax Account (only for GST-registered)
    IF p_is_gst_registered THEN
        INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, parent_id, is_system, tax_code_default) VALUES
            (p_org_id, '1600', 'GST Input Tax', 1, 101,
             (SELECT id FROM coa.account WHERE org_id = p_org_id AND code = '1000'),
             TRUE, 'TX');
    END IF;

    -- Header: Non-Current Assets
    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, is_header, is_system) VALUES
        (p_org_id, '1500', 'Non-Current Assets', 1, 106, TRUE, TRUE);

    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, parent_id)
    SELECT p_org_id, v.code, v.name, 1, v.sub_type,
           (SELECT id FROM coa.account WHERE org_id = p_org_id AND code = '1500')
    FROM (VALUES
        ('1510', 'Office Equipment',                  106),
        ('1520', 'Furniture & Fittings',              106),
        ('1530', 'Computer Equipment',                106),
        ('1540', 'Motor Vehicles',                    106),
        ('1550', 'Leasehold Improvements',            106),
        ('1560', 'Intangible Assets',                 108),
        ('1710', 'Accumulated Depreciation — Office Equipment',    107),
        ('1720', 'Accumulated Depreciation — Furniture & Fittings',107),
        ('1730', 'Accumulated Depreciation — Computer Equipment',  107),
        ('1740', 'Accumulated Depreciation — Motor Vehicles',      107),
        ('1750', 'Accumulated Depreciation — Leasehold Improvements', 107)
    ) AS v(code, name, sub_type);

    -- ═══════════════════════════════════════════
    -- LIABILITIES (2000-2999)
    -- ═══════════════════════════════════════════

    -- Header: Current Liabilities
    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, is_header, is_system) VALUES
        (p_org_id, '2000', 'Current Liabilities', 2, 201, TRUE, TRUE);

    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, parent_id, is_system, is_control)
    SELECT p_org_id, v.code, v.name, 2, v.sub_type,
           (SELECT id FROM coa.account WHERE org_id = p_org_id AND code = '2000'),
           v.is_system, v.is_control
    FROM (VALUES
        ('2100', 'Accounts Payable',                  202, TRUE, TRUE),
        ('2110', 'Accounts Payable — Foreign',         202, FALSE, TRUE),
        ('2200', 'Accrued Expenses',                   204, FALSE, FALSE),
        ('2300', 'Income Tax Payable',                 203, TRUE, FALSE),
        ('2400', 'CPF Payable',                        203, FALSE, FALSE),
        ('2410', 'Skills Development Levy Payable',    203, FALSE, FALSE),
        ('2500', 'Other Current Liabilities',          206, FALSE, FALSE),
        ('2510', 'Deposits Received',                  201, FALSE, FALSE),
        ('2520', 'Deferred Revenue',                   201, FALSE, FALSE)
    ) AS v(code, name, sub_type, is_system, is_control);

    -- GST Output Tax Account (only for GST-registered)
    IF p_is_gst_registered THEN
        INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, parent_id, is_system, tax_code_default)
        VALUES
            (p_org_id, '2600', 'GST Output Tax', 2, 203,
             (SELECT id FROM coa.account WHERE org_id = p_org_id AND code = '2000'),
             TRUE, 'SR'),
            (p_org_id, '2610', 'GST Payable / Receivable', 2, 203,
             (SELECT id FROM coa.account WHERE org_id = p_org_id AND code = '2000'),
             TRUE, NULL);
    END IF;

    -- Header: Non-Current Liabilities
    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, is_header) VALUES
        (p_org_id, '2700', 'Non-Current Liabilities', 2, 205, TRUE);

    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, parent_id)
    SELECT p_org_id, v.code, v.name, 2, 205,
           (SELECT id FROM coa.account WHERE org_id = p_org_id AND code = '2700')
    FROM (VALUES
        ('2710', 'Bank Loan'),
        ('2720', 'Hire Purchase Payable'),
        ('2730', 'Director''s Loan'),
        ('2740', 'Other Long-Term Liabilities')
    ) AS v(code, name);

    -- ═══════════════════════════════════════════
    -- EQUITY (3000-3999)
    -- ═══════════════════════════════════════════

    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, is_system)
    SELECT p_org_id, v.code, v.name, 3, v.sub_type, v.is_system
    FROM (VALUES
        ('3000', 'Share Capital / Owner''s Equity',   301, TRUE),
        ('3100', 'Retained Earnings',                  302, TRUE),
        ('3200', 'Current Year Earnings',              302, TRUE),
        ('3300', 'Owner''s Drawings',                  303, FALSE),
        ('3400', 'Dividends Paid',                     304, FALSE),
        ('3500', 'Other Reserves',                     304, FALSE)
    ) AS v(code, name, sub_type, is_system);

    -- ═══════════════════════════════════════════
    -- REVENUE (4000-4999)
    -- ═══════════════════════════════════════════

    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, tax_code_default)
    SELECT p_org_id, v.code, v.name, 4, v.sub_type,
           CASE WHEN p_is_gst_registered THEN v.tax_code ELSE 'NA' END
    FROM (VALUES
        ('4000', 'Sales Revenue',                      401, 'SR'),
        ('4100', 'Service Revenue',                    402, 'SR'),
        ('4200', 'Other Operating Revenue',            401, 'SR'),
        ('4300', 'Discount Allowed',                   401, 'SR')
    ) AS v(code, name, sub_type, tax_code);

    -- ═══════════════════════════════════════════
    -- COST OF GOODS SOLD (5000-5999)
    -- ═══════════════════════════════════════════

    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, tax_code_default)
    SELECT p_org_id, v.code, v.name, 5, 501,
           CASE WHEN p_is_gst_registered THEN v.tax_code ELSE 'NA' END
    FROM (VALUES
        ('5000', 'Cost of Goods Sold',                 'TX'),
        ('5100', 'Purchase Discounts',                 'TX'),
        ('5200', 'Freight & Delivery — Inward',       'TX'),
        ('5300', 'Direct Labour',                      'OP'),
        ('5400', 'Subcontractor Costs',                'TX')
    ) AS v(code, name, tax_code);

    -- ═══════════════════════════════════════════
    -- EXPENSES (6000-6999)
    -- ═══════════════════════════════════════════

    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, tax_code_default)
    SELECT p_org_id, v.code, v.name, 6, v.sub_type,
           CASE WHEN p_is_gst_registered THEN v.tax_code ELSE 'NA' END
    FROM (VALUES
        -- Payroll (out-of-scope for GST)
        ('6000', 'Salaries & Wages',                   601, 'OP'),
        ('6010', 'CPF Contributions — Employer',      601, 'OP'),
        ('6020', 'Skills Development Levy',            601, 'OP'),
        ('6030', 'Foreign Worker Levy',                601, 'OP'),
        ('6040', 'Staff Benefits',                     601, 'TX'),
        ('6050', 'Staff Training',                     601, 'TX'),
        ('6060', 'Director''s Fees',                   601, 'OP'),
        ('6070', 'Bonus & Commission',                 601, 'OP'),

        -- Operating Expenses
        ('6100', 'Rental Expense',                     602, 'TX'),
        ('6110', 'Utilities',                          602, 'TX'),
        ('6120', 'Cleaning & Maintenance',             602, 'TX'),
        ('6200', 'Office Supplies',                    603, 'TX'),
        ('6210', 'Printing & Stationery',              603, 'TX'),
        ('6220', 'Postage & Courier',                  603, 'TX'),
        ('6300', 'Telecommunications',                 603, 'TX'),
        ('6310', 'Internet & Software Subscriptions',  603, 'TX'),
        ('6400', 'Insurance',                          603, 'TX'),
        ('6500', 'Professional Fees — Accounting',    603, 'TX'),
        ('6510', 'Professional Fees — Legal',         603, 'TX'),
        ('6520', 'Professional Fees — Consulting',    603, 'TX'),
        ('6530', 'Company Secretary Fees',             603, 'TX'),
        ('6600', 'Advertising & Marketing',            604, 'TX'),
        ('6610', 'Entertainment',                      604, 'TX'),
        ('6620', 'Travel & Transport',                 604, 'TX'),
        ('6630', 'Motor Vehicle Expenses',             604, 'BL'),  -- Blocked input tax (S-plate)
        ('6700', 'Bank Charges',                       605, 'EP'),  -- Exempt (financial service)
        ('6710', 'Interest Expense',                   605, 'EP'),
        ('6720', 'Credit Card Fees',                   605, 'TX'),
        ('6800', 'Depreciation',                       606, 'OP'),  -- Out-of-scope (no supply)
        ('6810', 'Amortisation',                       606, 'OP'),
        ('6900', 'Bad Debt Expense',                   602, 'OP'),
        ('6910', 'Repairs & Maintenance',              602, 'TX'),
        ('6950', 'Miscellaneous Expenses',             602, 'TX'),
        ('6980', 'Penalties & Fines',                  602, 'OP'),  -- Not deductible / no GST
        ('6990', 'Rounding Difference',                602, 'OP')
    ) AS v(code, name, sub_type, tax_code);

    -- ═══════════════════════════════════════════
    -- OTHER INCOME (7000-7999)
    -- ═══════════════════════════════════════════

    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, tax_code_default)
    SELECT p_org_id, v.code, v.name, 7, 701,
           CASE WHEN p_is_gst_registered THEN v.tax_code ELSE 'NA' END
    FROM (VALUES
        ('7000', 'Interest Income',                    'ES'),  -- Exempt supply
        ('7100', 'Dividend Income',                    'OS'),  -- Out-of-scope
        ('7200', 'Rental Income',                      'SR'),
        ('7300', 'Government Grants & Subsidies',      'OS'),
        ('7400', 'Gain on Disposal of Assets',         'OS'),
        ('7500', 'Foreign Exchange Gain',              'OS'),
        ('7600', 'Other Income',                       'OS')
    ) AS v(code, name, tax_code);

    -- ═══════════════════════════════════════════
    -- OTHER EXPENSES (8000-8999)
    -- ═══════════════════════════════════════════

    INSERT INTO coa.account (org_id, code, name, account_type_id, account_sub_type_id, tax_code_default)
    SELECT p_org_id, v.code, v.name, 8, 801,
           CASE WHEN p_is_gst_registered THEN v.tax_code ELSE 'NA' END
    FROM (VALUES
        ('8000', 'Loss on Disposal of Assets',         'OS'),
        ('8100', 'Foreign Exchange Loss',              'OS'),
        ('8200', 'Income Tax Expense',                 'OP'),
        ('8300', 'Other Expenses',                     'OS')
    ) AS v(code, name, tax_code);

    -- ═══════════════════════════════════════════
    -- SEED DOCUMENT SEQUENCES
    -- ═══════════════════════════════════════════

    INSERT INTO core.document_sequence (org_id, document_type, prefix, next_number, padding) VALUES
        (p_org_id, 'SALES_INVOICE',          'INV-',  1, 5),
        (p_org_id, 'SALES_CREDIT_NOTE',      'CN-',   1, 5),
        (p_org_id, 'SALES_DEBIT_NOTE',       'DN-',   1, 5),
        (p_org_id, 'PURCHASE_INVOICE',       'BILL-', 1, 5),
        (p_org_id, 'PURCHASE_CREDIT_NOTE',   'PCN-',  1, 5),
        (p_org_id, 'PURCHASE_DEBIT_NOTE',    'PDN-',  1, 5),
        (p_org_id, 'PURCHASE_ORDER',         'PO-',   1, 5),
        (p_org_id, 'SALES_QUOTE',            'QT-',   1, 5),
        (p_org_id, 'JOURNAL_ENTRY',          'JE-',   1, 6),
        (p_org_id, 'PAYMENT_RECEIVED',       'REC-',  1, 5),
        (p_org_id, 'PAYMENT_MADE',           'PAY-',  1, 5);

END;
$$;

COMMENT ON FUNCTION core.seed_default_chart_of_accounts
    IS 'Seeds a complete Singapore-aligned Chart of Accounts for a new organisation.';


-- ============================================================================
-- §15  APPLICATION ROLES & GRANTS
-- ============================================================================
-- Two PostgreSQL database roles:
--   1. ledgersg_owner — Owns all objects (used for migrations/DDL)
--   2. ledgersg_app   — Application role (used by Django via connection pool)
--
-- The app role gets DML access but no DDL.
-- RLS policies ensure tenant isolation.

-- Create roles (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ledgersg_owner') THEN
        CREATE ROLE ledgersg_owner WITH LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ledgersg_app') THEN
        CREATE ROLE ledgersg_app WITH LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
    END IF;
END $$;

-- Schema usage grants
GRANT USAGE ON SCHEMA core, coa, gst, journal, invoicing, banking, audit
    TO ledgersg_app;

-- Table-level grants
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA
    core, coa, gst, journal, invoicing, banking
    TO ledgersg_app;

-- AUDIT: Append-only — NO UPDATE or DELETE
GRANT SELECT, INSERT ON audit.event_log TO ledgersg_app;
-- Explicitly revoke UPDATE/DELETE on audit log
REVOKE UPDATE, DELETE ON audit.event_log FROM ledgersg_app;

-- Sequence grants
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA
    core, coa, gst, journal, invoicing, banking, audit
    TO ledgersg_app;

-- Function execution grants
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core, gst, journal, audit
    TO ledgersg_app;

-- Default grants for future tables (created by migrations)
ALTER DEFAULT PRIVILEGES IN SCHEMA core, coa, gst, journal, invoicing, banking
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ledgersg_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA audit
    GRANT SELECT, INSERT ON TABLES TO ledgersg_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA core, coa, gst, journal, invoicing, banking, audit
    GRANT USAGE, SELECT ON SEQUENCES TO ledgersg_app;


-- ============================================================================
-- SCHEMA VERIFICATION
-- ============================================================================
-- Quick sanity check to verify all schemas and key objects exist.

DO $$
DECLARE
    v_schema_count INT;
    v_table_count  INT;
    v_func_count   INT;
    v_tax_codes    INT;
    v_currencies   INT;
    v_roles        INT;
BEGIN
    SELECT count(*) INTO v_schema_count
    FROM information_schema.schemata
    WHERE schema_name IN ('core', 'coa', 'gst', 'journal', 'invoicing', 'banking', 'audit');

    SELECT count(*) INTO v_table_count
    FROM information_schema.tables
    WHERE table_schema IN ('core', 'coa', 'gst', 'journal', 'invoicing', 'banking', 'audit')
        AND table_type = 'BASE TABLE';

    SELECT count(*) INTO v_func_count
    FROM information_schema.routines
    WHERE routine_schema IN ('core', 'gst', 'journal', 'audit');

    SELECT count(*) INTO v_tax_codes FROM gst.tax_code;
    SELECT count(*) INTO v_currencies FROM core.currency;
    SELECT count(*) INTO v_roles FROM core.role;

    RAISE NOTICE '';
    RAISE NOTICE '══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  LEDGERSG DATABASE SCHEMA — INSTALLATION COMPLETE';
    RAISE NOTICE '══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  Schemas created:        %', v_schema_count;
    RAISE NOTICE '  Tables created:         %', v_table_count;
    RAISE NOTICE '  Functions created:       %', v_func_count;
    RAISE NOTICE '  GST tax codes seeded:    % (incl. historical rates)', v_tax_codes;
    RAISE NOTICE '  Currencies seeded:       %', v_currencies;
    RAISE NOTICE '  System roles seeded:     %', v_roles;
    RAISE NOTICE '══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  Next steps:';
    RAISE NOTICE '    1. Change ledgersg_owner and ledgersg_app passwords';
    RAISE NOTICE '    2. Create your first organisation via Django admin';
    RAISE NOTICE '    3. The system will auto-seed CoA via';
    RAISE NOTICE '       core.seed_default_chart_of_accounts(org_id, gst_registered)';
    RAISE NOTICE '══════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
END $$;


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  END OF SCHEMA SCRIPT                                                      ║
-- ║  LedgerSG v1.0.0 — PostgreSQL 16 Database Initialization                  ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
