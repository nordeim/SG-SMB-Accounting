# LEDGERSG: Enterprise Accounting Platform for Singapore SMBs
## Comprehensive Architectural Blueprint v4.0 (Final)

---

# Executive Summary

**LedgerSG** is an enterprise-grade, production-ready accounting platform engineered specifically for Singaporean small to medium-sized businesses (SMBs) and sole proprietorships. This blueprint represents the culmination of exhaustive regulatory research, technical analysis, and avant-garde design philosophy.

**Core Mission:** Transform IRAS compliance from a burden into a seamless, automated experience while delivering a distinctive, anti-generic user interface that makes financial data approachable yet authoritative.

**Regulatory Foundation:** Built to withstand IRAS's 2026 compliance requirements including mandatory InvoiceNow (Peppol PINT-SG), 9% GST precision, Beverage Container Return Scheme (BCRS), Transfer Pricing documentation thresholds, and automated audit trails.

**Technical Stack:** PostgreSQL 16, Django 6.0 (Python 3.13), Next.js 15, React 19, Tailwind CSS 4, Shadcn-UI.

**Design Philosophy:** "Neo-Brutalist Fintech" — Dark-first, high-contrast, typographically driven, rejecting generic SaaS aesthetics.

---

# Part 1: Regulatory & Compliance Foundation

## 1.1 IRAS 2026 Regulatory Landscape

### 1.1.1 Mandatory InvoiceNow (Peppol) E-Invoicing
| Requirement | Specification | Implementation |
|-------------|---------------|----------------|
| **Effective Dates** | Nov 2025: New GST registrants within 6 months of incorporation<br>Apr 2026: All new voluntary GST registrants | System flags companies approaching mandatory dates |
| **Format** | PINT-SG (Singapore extension of PEPPOL International Invoice) | XML generation with schema validation |
| **Transmission** | Via accredited Peppol Access Point (AP) | API integration with certified AP provider |
| **Fatal Errors** | Missing UUID, incorrect UEN, tax fraction inaccuracies cause outright rejection | Pre-flight validation before submission |
| **UUID Requirement** | Every invoice must have unique UUID | Auto-generated, immutable, stored in DB |
| **Retention** | 5 years minimum | Immutable audit logs, soft-delete only |

### 1.1.2 GST Calculation & Precision
| Requirement | Specification | Implementation |
|-------------|---------------|----------------|
| **Current Rate** | 9% (stable since Jan 1, 2024) | Configurable in `TaxConfiguration` model |
| **Historical Rates** | 8% (pre-2024), 7% (pre-2023) | Rate snapshot stored per invoice |
| **Precision** | Exact to the cent; intermediate calculations to 4 decimals | `DecimalField(max_digits=10, decimal_places=4)` |
| **Rounding** | ROUND_HALF_UP to 2 decimals for final display | Python `decimal` module exclusively |
| **Time of Supply** | Tax point may differ from invoice date | Separate `tax_point_date` field |
| **Prohibited** | No `float` types for monetary values | Enforced via linting and code review |

### 1.1.3 Beverage Container Return Scheme (BCRS)
| Requirement | Specification | Implementation |
|-------------|---------------|----------------|
| **Effective** | April 2026 | Feature flag for early adoption |
| **Deposit Amount** | S$0.10 per pre-packaged drink | Product-level flag `is_subject_to_bcrs` |
| **GST Treatment** | Deposit is NOT subject to GST | Excluded from taxable base calculation |
| **Accounting** | Deposit is a Liability, not Income | Separate liability account in COA |
| **Reporting** | Quarterly deposit collection returns | Dedicated BCRS report module |

### 1.1.4 Transfer Pricing (TP) Documentation
| Requirement | Specification | Implementation |
|-------------|---------------|----------------|
| **Threshold** | S$2M for related-party transactions (loans, sales, services) | Automatic threshold monitoring |
| **Documentation** | Mandatory contemporaneous TPD if exceeded | Flag `tp_documentation_required` on Org |
| **Penalty** | 5% surcharge on TP adjustments during audit | Alert system for compliance officers |
| **SSA** | Simplified Streamlined Approach for baseline marketing/distribution | Documentation templates provided |

### 1.1.5 Corporate Income Tax (CIT) & Cross-Check
| Requirement | Specification | Implementation |
|-------------|---------------|----------------|
| **YA 2026 Rebate** | 50% rebate on tax payable, capped at S$40,000 | Auto-calculation in tax module |
| **Minimum Grant** | S$2,000 for companies with ≥1 local employee | Eligibility checker |
| **Cross-Check Risk** | CIT revenue > S$1M but not GST-registered triggers audit | Warning system for users |
| **ECI Filing** | Estimated Chargeable Income preparation | Data export for IRAS portal |

### 1.1.6 Reverse Charge Mechanism
| Requirement | Specification | Implementation |
|-------------|---------------|----------------|
| **Applicability** | Digital services from overseas suppliers (e.g., Facebook ads, SaaS) | Supplier classification flag |
| **Calculation** | Business accounts for GST on behalf of overseas supplier | Auto-calculate 9% on purchase |
| **Journal Entry** | Debit: Expense, Credit: Cash, Credit: GST Payable (Reverse Charge) | Double-entry automation |

---

## 1.2 User Personas & Emotional Drivers

| Persona | Key Needs | Emotional Drivers | System Features |
|---------|-----------|-------------------|-----------------|
| **SME Owner** (F&B, Retail) | Simple invoicing, BCRS compliance, cash flow visibility | Fear of fines, desire for "set and forget" | One-click Peppol send, BCRS toggle, dashboard alerts |
| **Accountant/Bookkeeper** | Fast data entry, reconciliation, audit-ready reports | Efficiency, accuracy, professional credibility | Bulk import, keyboard shortcuts, export formats |
| **Compliance Officer** (Larger SME) | TP documentation, cross-border handling, audit trails | Risk mitigation, regulatory confidence | TP threshold alerts, related-party flags, immutable logs |
| **IRAS Auditor** (Indirect) | Clear, machine-readable data; no "Fatal Errors" | Data integrity, automated validation | PINT-SG compliance, UUID on every invoice, 5-year retention |

---

# Part 2: Technical Architecture

## 2.1 Technology Stack Justification

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Database** | PostgreSQL | 16 | ACID compliance, JSONB for metadata, GENERATED columns, RETURNING clause support |
| **Backend** | Django | 6.0 | Native Tasks framework, CSP middleware, Async ORM, Argon2 default hashing |
| **Language** | Python | 3.13 | Required by Django 6.0, performance improvements, latest type hints |
| **Frontend** | Next.js | 15 | App Router, Server Components, Server Actions, Partial Prerendering |
| **UI Library** | React | 19 | Latest concurrent features, improved hooks |
| **Styling** | Tailwind CSS | 4.0 | Native CSS variables, engine-level performance, no config file |
| **Components** | Shadcn-UI | Latest | Radix primitives, accessible, fully customizable |
| **Authentication** | Django Session | HttpOnly Cookies | More secure than JWT, CSRF protected, no XSS risk |
| **Task Queue** | Django Native Tasks | 6.0+ | Removes Celery dependency, simpler architecture |
| **Email** | Python Modern Email API | 3.6+ | Better Unicode handling, cleaner MIME construction |

## 2.2 High-Level System Context

```mermaid
graph TB
    subgraph "Client Layer"
        A[Next.js 15 PWA]
        B[Mobile Responsive UI]
        C[Offline-First Cache]
    end
    
    subgraph "Security Layer"
        D[Next.js Middleware]
        E[Django CSP Middleware]
        F[HttpOnly Cookie Auth]
        G[CSRF Protection]
    end
    
    subgraph "API Gateway (Django 6.0)"
        H[Async DRF ViewSets]
        I[Native Tasks Framework]
        J[Compliance Engine]
        K[Modern Email API]
    end
    
    subgraph "Integration Layer"
        L[Peppol Access Point API]
        M[Bank Feeds / OCR]
        N[IRAS MyTax Portal]
        O[ACRA UEN Validation]
    end
    
    subgraph "Data Layer"
        P[(PostgreSQL 16)]
        Q[Generated Columns]
        R[Audit Logs (Immutable)]
        S[Task Queue (DB-Backed)]
    end
    
    subgraph "Worker Process"
        T[Task Worker Container]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> T
    H --> J
    J --> K
    J --> L
    J --> M
    J --> N
    J --> O
    H --> P
    P --> Q
    P --> R
    P --> S
    T --> L
```

## 2.3 Directory Structure (Monorepo)

```
ledgersg/
├── apps/
│   ├── web/                          # Next.js 15 Frontend
│   │   ├── app/                      # App Router
│   │   ├── components/               # Shadcn-UI + Custom
│   │   ├── lib/                      # Utilities, API clients
│   │   ├── hooks/                    # React Hooks
│   │   ├── styles/                   # Tailwind 4 CSS
│   │   └── public/                   # Static assets
│   │
│   ├── backend/                      # Django 6.0 Backend
│   │   ├── config/                   # Settings, URLs, WSGI/ASGI
│   │   ├── apps/
│   │   │   ├── core/                 # Auth, Tenancy, Audit
│   │   │   ├── accounting/           # COA, Journal, Ledger
│   │   │   ├── invoicing/            # Invoices, Quotes, Credit Notes
│   │   │   ├── compliance/           # IRAS GST, BCRS, TP, Peppol
│   │   │   ├── reporting/            # Financial Statements
│   │   │   └── organizations/        # Company, User, Roles
│   │   ├── tasks/                    # Native Django Tasks
│   │   ├── utils/
│   │   │   ├── money.py              # Decimal wrappers
│   │   │   ├── validators.py         # UEN, GST logic
│   │   │   └── csp.py                # CSP nonce helpers
│   │   └── tests/                    # Pytest suite
│   │
│   └── shared/                       # Shared Types, Schemas
│       ├── types/                    # TypeScript types
│       └── schemas/                  # Zod/Pydantic schemas
│
├── infrastructure/
│   ├── docker/                       # Dockerfiles, Compose
│   ├── k8s/                          # Kubernetes manifests
│   └── terraform/                    # IaC for cloud resources
│
├── docs/
│   ├── architecture/                 # ADRs, diagrams
│   ├── compliance/                   # IRAS mapping documents
│   ├── api/                          # OpenAPI specs
│   └── user-guides/                  # Training materials
│
├── scripts/
│   ├── setup.sh                      # Development environment
│   ├── seed.py                       # Test data generation
│   └── deploy.sh                     # CI/CD pipelines
│
├── pyproject.toml                    # Python dependencies
├── package.json                      # Node dependencies
├── turbo.json                        # Turborepo config
└── README.md                         # Project overview
```

---

# Part 3: Data Architecture

## 3.1 Database Schema (PostgreSQL 16)

### 3.1.1 Core Models

```python
# apps/organizations/models.py
from django.db import models
from decimal import Decimal
import uuid

class Organization(models.Model):
    """
    Multi-tenancy root. Each organization is a separate business entity.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    uen = models.CharField(max_length=20, unique=True, db_index=True)
    gst_registration_no = models.CharField(max_length=20, blank=True)
    gst_registered = models.BooleanField(default=False)
    gst_registration_date = models.DateField(null=True, blank=True)
    
    # Peppol Configuration
    is_peppol_registered = models.BooleanField(default=False)
    peppol_access_point_id = models.CharField(max_length=100, blank=True)
    
    # Transfer Pricing Monitoring
    related_party_transaction_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False
    )
    tp_documentation_required = models.BooleanField(default=False)
    
    # BCRS Configuration
    is_bcrs_registered = models.BooleanField(default=False)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Organizations"
        indexes = [
            models.Index(fields=['uen']),
            models.Index(fields=['gst_registered']),
        ]

class User(models.Model):
    """
    Custom user model with organization membership.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Security (Django 6.0 Argon2 default)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    organizations = models.ManyToManyField(
        Organization, through='OrganizationMember'
    )

class OrganizationMember(models.Model):
    """
    Many-to-many through model for user-organization relationships.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=[
            ('OWNER', 'Owner'),
            ('ADMIN', 'Admin'),
            ('ACCOUNTANT', 'Accountant'),
            ('VIEWER', 'Viewer'),
        ]
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'organization']
```

### 3.1.2 Accounting Models

```python
# apps/accounting/models.py
from django.db import models
from decimal import Decimal

class Account(models.Model):
    """
    Chart of Accounts - Singapore COA structure.
    Class 1: Assets, Class 2: Liabilities, Class 3: Equity
    Class 4: Revenue, Class 5: Expenses, Class 6: Other Income
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)  # e.g., "1200" for AR
    name = models.CharField(max_length=200)
    account_type = models.CharField(
        max_length=20,
        choices=[
            ('ASSET', 'Asset'),
            ('LIABILITY', 'Liability'),
            ('EQUITY', 'Equity'),
            ('REVENUE', 'Revenue'),
            ('EXPENSE', 'Expense'),
        ]
    )
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.PROTECT
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['organization', 'code']
        ordering = ['code']

class JournalEntry(models.Model):
    """
    Double-entry bookkeeping - immutable record of financial transactions.
    """
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    entry_date = models.DateField()
    description = models.TextField()
    reference = models.CharField(max_length=100)  # e.g., "INV-001"
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        indexes = [
            models.Index(fields=['organization', 'entry_date']),
        ]

class JournalLine(models.Model):
    """
    Individual debit/credit lines within a journal entry.
    Must balance: total debits = total credits per entry.
    """
    journal_entry = models.ForeignKey(
        JournalEntry, related_name='lines', on_delete=models.CASCADE
    )
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    debit = models.DecimalField(
        max_digits=12, decimal_places=4, default=Decimal('0.00')
    )
    credit = models.DecimalField(
        max_digits=12, decimal_places=4, default=Decimal('0.00')
    )
    description = models.CharField(max_length=200, blank=True)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(debit__gte=0) & models.Q(credit__gte=0),
                name='debit_credit_non_negative'
            ),
        ]
```

### 3.1.3 Invoicing Models

```python
# apps/invoicing/models.py
from django.db import models
from decimal import Decimal
import uuid

class Invoice(models.Model):
    """
    Customer Invoice with IRAS compliance fields.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('VOID', 'Void'),
    ]
    
    PEPPOL_STATUS_CHOICES = [
        ('NOT_REQUIRED', 'Not Required'),
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    customer = models.ForeignKey('Customer', on_delete=models.PROTECT)
    
    # Invoice Identification (IRAS Fatal Error Prevention)
    invoice_number = models.CharField(max_length=50, unique=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    peppol_invoice_id = models.CharField(max_length=100, blank=True)
    
    # Dates
    issue_date = models.DateField()
    due_date = models.DateField()
    tax_point_date = models.DateField(null=True, blank=True)  # For GST timing
    
    # Financials (Decimal Precision)
    subtotal = models.DecimalField(max_digits=12, decimal_places=4)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.09'))
    gst_amount = models.DecimalField(max_digits=12, decimal_places=4)
    bcrs_deposit_total = models.DecimalField(
        max_digits=12, decimal_places=4, default=Decimal('0.00')
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=4)
    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=4, default=Decimal('0.00')
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    peppol_status = models.CharField(
        max_length=20, choices=PEPPOL_STATUS_CHOICES, default='NOT_REQUIRED'
    )
    peppol_response = models.JSONField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'issue_date']),
            models.Index(fields=['uuid']),
        ]
    
    @property
    def amount_outstanding(self) -> Decimal:
        return self.total_amount - self.amount_paid
    
    @property
    def is_fully_paid(self) -> bool:
        return self.amount_outstanding <= 0

class InvoiceLine(models.Model):
    """
    Line items within an invoice.
    """
    invoice = models.ForeignKey(
        Invoice, related_name='lines', on_delete=models.CASCADE
    )
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Calculated (stored for audit integrity)
    line_subtotal = models.DecimalField(max_digits=12, decimal_places=4)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=4)
    
    # BCRS
    is_bcrs_deposit = models.BooleanField(default=False)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=0) & models.Q(unit_price__gte=0),
                name='quantity_price_non_negative'
            ),
        ]

class Customer(models.Model):
    """
    Customer entity with GST and Peppol details.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    uen = models.CharField(max_length=20, blank=True)
    gst_registration_no = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    country = models.CharField(max_length=2, default='SG')  # ISO 3166-1
    
    # Peppol
    peppol_id = models.CharField(max_length=100, blank=True)
    is_peppol_enabled = models.BooleanField(default=False)
    
    # Related Party (for TP monitoring)
    is_related_party = models.BooleanField(default=False)
    related_party_relationship = models.CharField(max_length=200, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['organization', 'uen']
```

### 3.1.4 Product & BCRS Models

```python
# apps/invoicing/models.py (continued)

class Product(models.Model):
    """
    Product/Service catalog with GST and BCRS configuration.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=4)
    gst_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.09')
    )
    gst_code = models.CharField(
        max_length=20,
        choices=[
            ('STD', 'Standard Rated (9%)'),
            ('ZERO', 'Zero-Rated'),
            ('EXEMPT', 'Exempt'),
            ('OUTOFSCOPE', 'Out of Scope'),
        ],
        default='STD'
    )
    
    # BCRS Configuration
    is_subject_to_bcrs = models.BooleanField(default=False)
    bcrs_deposit_amount = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.10')
    )
    deposit_liability_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL
    )
    
    # Inventory (optional)
    track_inventory = models.BooleanField(default=False)
    current_stock = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['organization', 'sku']
        indexes = [
            models.Index(fields=['organization', 'is_subject_to_bcrs']),
        ]
```

### 3.1.5 Compliance & Audit Models

```python
# apps/compliance/models.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class AuditLog(models.Model):
    """
    Immutable audit trail for all critical operations.
    IRAS requires 5-year retention.
    """
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE, VOID
    entity_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    entity_id = models.UUIDField()
    entity = GenericForeignKey('entity_type', 'entity_id')
    
    # Change tracking
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]
    
    def delete(self, *args, **kwargs):
        """Prevent deletion - audit logs are immutable."""
        raise Exception("Audit logs cannot be deleted")

class TaxConfiguration(models.Model):
    """
    Centralized management of Singapore tax rates.
    Allows historical tracking without code changes.
    """
    name = models.CharField(max_length=50)  # e.g., "Standard GST 2024"
    rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        validators=[
            models.MinValueValidator(Decimal('0.0000')),
            models.MaxValueValidator(Decimal('1.0000'))
        ]
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-effective_from']

class PeppolTransmissionLog(models.Model):
    """
    Track all Peppol invoice transmissions for compliance.
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT)
    transmission_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20)
    request_payload = models.TextField()  # XML sent
    response_payload = models.TextField()  # XML received
    transmitted_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-transmitted_at']
```

## 3.2 Database Constraints & Generated Columns

```sql
-- PostgreSQL 16 Generated Columns for computed totals
-- Ensures data integrity at the database level

ALTER TABLE invoice_lines ADD COLUMN line_total NUMERIC(12,4) 
GENERATED ALWAYS AS (line_subtotal + gst_amount) STORED;

-- Check constraint to ensure journal entries balance
ALTER TABLE journal_entries ADD CONSTRAINT balanced_entry CHECK (
    (SELECT SUM(debit) FROM journal_lines WHERE journal_entry_id = id) =
    (SELECT SUM(credit) FROM journal_lines WHERE journal_entry_id = id)
);

-- Index for audit log queries (IRAS audit scenarios)
CREATE INDEX CONCURRENTLY idx_audit_log_entity_lookup 
ON audit_logs (entity_type_id, entity_id, timestamp);

-- Partial index for outstanding invoices
CREATE INDEX CONCURRENTLY idx_invoices_outstanding 
ON invoices (organization_id, amount_outstanding) 
WHERE status != 'PAID' AND status != 'VOID';
```

---

# Part 4: Backend Architecture (Django 6.0)

## 4.1 Settings Configuration

```python
# config/settings.py
from pathlib import Path
from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent

# Security (Django 6.0)
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: v.split(','))

# Django 6.0 Defaults
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Default in 6.0
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# Content Security Policy (Django 6.0 Native)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.contenttypes.middleware.ContentSecurityPolicyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE, "https://vercel.live"],
    "style-src": [CSP.SELF, CSP.NONCE, "https://fonts.googleapis.com"],
    "img-src": [CSP.SELF, "data:", "https:"],
    "connect-src": [CSP.SELF, "https://api.peppol.sg", "https://api.iras.gov.sg"],
    "font-src": [CSP.SELF, "https://fonts.gstatic.com"],
}

SECURE_CSP_REPORT_ONLY = False  # Enforce in production

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Django 6.0 Native Tasks Framework
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.database.DatabaseBackend",
    },
}

# Email (Modern Python Email API)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = 'noreply@ledgersg.sg'

# Internationalization
LANGUAGE_CODE = 'en-sg'
TIME_ZONE = 'Asia/Singapore'
USE_I18N = True
USE_TZ = True

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# API Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'COERCE_DECIMAL_TO_STRING': True,  # Prevent float conversion
}

# Compliance Settings
GST_RATE = Decimal('0.09')
BCRS_DEPOSIT = Decimal('0.10')
TP_THRESHOLD = Decimal('2000000.00')
INVOICE_RETENTION_YEARS = 5
```

## 4.2 Compliance Engine Service

```python
# apps/compliance/services/engine.py
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from typing import Tuple

class ComplianceEngine:
    """
    Centralized compliance logic for IRAS regulations.
    All monetary calculations flow through this engine.
    """
    
    GST_RATE = Decimal('0.09')
    BCRS_DEPOSIT = Decimal('0.10')
    TP_THRESHOLD = Decimal('2000000.00')
    GST_CHANGE_DATE = timezone.datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    @classmethod
    def get_applicable_gst_rate(cls, transaction_date: timezone.datetime) -> Decimal:
        """
        Determines GST rate based on IRAS 'Time of Supply' rules.
        Handles historical rates for legacy invoices.
        """
        if transaction_date >= cls.GST_CHANGE_DATE:
            return cls.GST_RATE
        return Decimal('0.08')  # Legacy rate
    
    @classmethod
    def calculate_line_item(
        cls, 
        amount: Decimal, 
        rate: Decimal,
        is_bcrs_deposit: bool = False
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate subtotal, GST, and total for a line item.
        
        Args:
            amount: Net amount before GST
            rate: GST rate (e.g., 0.09 for 9%)
            is_bcrs_deposit: If True, GST is not applied
            
        Returns:
            Tuple of (subtotal, gst_amount, total)
        """
        if is_bcrs_deposit:
            # BCRS deposit is NOT subject to GST
            return amount, Decimal('0.00'), amount
        
        gst = (amount * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total = amount + gst
        return amount, gst, total
    
    @classmethod
    @transaction.atomic
    def finalize_invoice(cls, invoice) -> None:
        """
        Calculate all totals, update TP thresholds, validate Peppol readiness.
        Called when invoice is moved from DRAFT to SENT.
        """
        subtotal = Decimal('0.00')
        gst_total = Decimal('0.00')
        bcrs_total = Decimal('0.00')
        related_party_amount = Decimal('0.00')
        
        for line in invoice.lines.all():
            # BCRS Logic
            if line.is_bcrs_deposit:
                bcrs_total += line.line_subtotal
            
            # GST Logic (exclude BCRS deposit from taxable base)
            taxable_amount = line.line_subtotal
            _, line_gst, _ = cls.calculate_line_item(
                taxable_amount, 
                invoice.gst_rate,
                line.is_bcrs_deposit
            )
            line.gst_amount = line_gst
            line.save()
            
            gst_total += line_gst
            subtotal += taxable_amount
            
            # Transfer Pricing Logic
            if invoice.customer.is_related_party:
                related_party_amount += line.line_subtotal
        
        # Update Invoice Totals
        invoice.subtotal = subtotal
        invoice.gst_amount = gst_total
        invoice.bcrs_deposit_total = bcrs_total
        invoice.total_amount = subtotal + gst_total + bcrs_total
        invoice.save()
        
        # Update Organization TP Threshold
        org = invoice.organization
        org.related_party_transaction_total += related_party_amount
        if org.related_party_transaction_total > cls.TP_THRESHOLD:
            org.tp_documentation_required = True
        org.save()
        
        # Validate Peppol Readiness
        cls.validate_peppol_readiness(invoice)
    
    @classmethod
    def validate_peppol_readiness(cls, invoice) -> list:
        """
        Pre-flight check to prevent IRAS Fatal Errors.
        Returns list of validation errors (empty if valid).
        """
        errors = []
        
        if not invoice.organization.uen:
            errors.append("Organization UEN is missing")
        
        if not invoice.uuid:
            errors.append("Invoice UUID is missing")
        
        if not invoice.customer.name:
            errors.append("Customer name is missing")
        
        if invoice.gst_amount < 0:
            errors.append("GST amount cannot be negative")
        
        # PINT-SG specific validations
        if len(invoice.invoice_number) > 50:
            errors.append("Invoice number exceeds 50 characters")
        
        return errors
    
    @classmethod
    def check_cit_gst_cross_reference(cls, organization) -> dict:
        """
        Check for IRAS cross-reference risk triggers.
        Warns if CIT revenue > S$1M but not GST registered.
        """
        warnings = []
        
        # Calculate annual revenue from invoices
        current_year = timezone.now().year
        revenue = Invoice.objects.filter(
            organization=organization,
            issue_date__year=current_year,
            status__in=['SENT', 'PAID']
        ).aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        if revenue > Decimal('1000000.00') and not organization.gst_registered:
            warnings.append({
                'code': 'CIT_GST_MISMATCH',
                'message': f'Revenue S${revenue:,.2f} exceeds S$1M threshold. '
                          'GST registration may be required to avoid IRAS audit.',
                'severity': 'HIGH'
            })
        
        return {
            'revenue': revenue,
            'gst_registered': organization.gst_registered,
            'warnings': warnings
        }
```

## 4.3 Native Tasks Implementation

```python
# apps/invoicing/tasks.py
from django.tasks import task
from django.core.mail import EmailMessage
from .services.peppol import transmit_invoice, generate_pint_sg_xml
from .models import Invoice

@task
def transmit_peppol_invoice(invoice_id: int):
    """
    Django 6.0 Native Task for async Peppol transmission.
    Queued automatically, executed by external worker process.
    """
    try:
        invoice = Invoice.objects.select_related('organization', 'customer').get(
            id=invoice_id
        )
        
        # Generate PINT-SG XML
        xml_payload = generate_pint_sg_xml(invoice)
        
        # Transmit via Peppol Access Point
        response = transmit_invoice(xml_payload)
        
        # Update invoice status
        invoice.peppol_status = 'ACCEPTED'
        invoice.peppol_response = response
        invoice.save()
        
        # Log transmission
        from apps.compliance.models import PeppolTransmissionLog
        PeppolTransmissionLog.objects.create(
            invoice=invoice,
            transmission_id=response.get('transmission_id'),
            status='SUCCESS',
            request_payload=xml_payload,
            response_payload=str(response)
        )
        
        # Send confirmation email (Modern Email API)
        msg = EmailMessage(
            subject=f"Invoice {invoice.invoice_number} Transmitted",
            body=f"Your invoice has been successfully transmitted via InvoiceNow.",
            from_email="noreply@ledgersg.sg",
            to=[invoice.created_by.email],
        )
        msg.send()
        
        return {"status": "success", "invoice_id": invoice_id}
        
    except Invoice.DoesNotExist:
        return {"status": "failed", "error": "Invoice not found"}
    except Exception as e:
        # Log error for retry logic
        return {"status": "failed", "error": str(e)}

@task
def send_invoice_email(invoice_id: int, recipient_email: str):
    """
    Send PDF invoice via email.
    """
    invoice = Invoice.objects.get(id=invoice_id)
    
    # Generate PDF (implementation omitted)
    pdf_content = generate_invoice_pdf(invoice)
    
    msg = EmailMessage(
        subject=f"Invoice {invoice.invoice_number} from {invoice.organization.name}",
        body=f"Please find attached invoice {invoice.invoice_number}.",
        from_email="invoices@ledgersg.sg",
        to=[recipient_email],
    )
    msg.attach(f"invoice_{invoice.invoice_number}.pdf", pdf_content, 'application/pdf')
    msg.send()
    
    return {"status": "success"}

@task
def generate_monthly_gst_report(organization_id: int, month: int, year: int):
    """
    Generate GST F5 report for IRAS submission.
    """
    from apps.reporting.services import GSTReportGenerator
    
    generator = GSTReportGenerator(organization_id, month, year)
    report = generator.generate()
    
    # Email report to organization admins
    org = Organization.objects.get(id=organization_id)
    admins = org.members.filter(role__in=['OWNER', 'ADMIN', 'ACCOUNTANT'])
    
    for admin in admins:
        msg = EmailMessage(
            subject=f"GST Report {month}/{year}",
            body="Your monthly GST report is ready for review.",
            from_email="reports@ledgersg.sg",
            to=[admin.user.email],
        )
        msg.attach(f"GST_{month}_{year}.csv", report.csv_content, 'text/csv')
        msg.send()
    
    return {"status": "success", "report_id": report.id}
```

## 4.4 API Views (DRF with Async Support)

```python
# apps/invoicing/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.async_utils import async_unsafe
from .models import Invoice
from .serializers import InvoiceSerializer, InvoiceCreateSerializer
from .tasks import transmit_peppol_invoice
from apps.compliance.services.engine import ComplianceEngine

class InvoiceViewSet(viewsets.ModelViewSet):
    """
    Invoice CRUD with compliance validation.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Invoice.objects.filter(
            organization=self.request.user.organizations.first()
        ).select_related('customer', 'organization')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        """
        Create invoice with organization context.
        """
        organization = self.request.user.organizations.first()
        serializer.save(
            organization=organization,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def send_peppol(self, request, pk=None):
        """
        Transmit invoice via Peppol (InvoiceNow).
        """
        invoice = self.get_object()
        
        # Validate before transmission
        errors = ComplianceEngine.validate_peppol_readiness(invoice)
        if errors:
            return Response(
                {"errors": errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Queue async task
        task_result = transmit_peppol_invoice.enqueue(invoice_id=invoice.id)
        
        invoice.peppol_status = 'PENDING'
        invoice.save()
        
        return Response({
            "status": "queued",
            "task_id": task_result.id,
            "message": "Invoice queued for Peppol transmission"
        })
    
    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        """
        Void an invoice (soft delete with audit trail).
        """
        invoice = self.get_object()
        
        if invoice.status == 'PAID':
            return Response(
                {"error": "Cannot void a paid invoice. Create credit note instead."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice.status = 'VOID'
        invoice.save()
        
        # Audit log created automatically via signals
        return Response({"status": "voided"})
    
    @action(detail=False, methods=['get'])
    def gst_summary(self, request):
        """
        Get GST summary for current period.
        """
        organization = request.user.organizations.first()
        summary = ComplianceEngine.check_cit_gst_cross_reference(organization)
        return Response(summary)
```

---

# Part 5: Frontend Architecture (Next.js 15)

## 5.1 Design System: "Neo-Brutalist Fintech"

### 5.1.1 Visual Principles
| Principle | Implementation |
|-----------|----------------|
| **Dark-First** | Background `#050505`, reduces eye strain for long sessions |
| **High Contrast** | White text on black, 1px borders for structure |
| **Monospace Data** | `JetBrains Mono` for all numbers (tabular alignment) |
| **No Shadows** | Depth via borders and contrast, not drop shadows |
| **Visible Grids** | Subtle grid lines on tables emphasize precision |
| **Square Corners** | `border-radius: 0` for brutalist aesthetic |
| **Micro-interactions** | Magnetic buttons, instant validation states |

### 5.1.2 Color Palette
```css
/* app/globals.css - Tailwind 4 Native CSS Variables */
@import "tailwindcss";

@theme {
  /* Core Colors */
  --color-void: #050505;
  --color-carbon: #121212;
  --color-surface: #1A1A1A;
  --color-border: #2A2A2A;
  
  /* Functional Colors */
  --color-accent: #00FF94;      /* SG Green - Positive */
  --color-accent-dim: #00CC76;
  --color-alert: #FF3333;       /* IRAS Red - Errors */
  --color-warning: #FFB347;     /* Amber - Warnings */
  --color-info: #4A90D9;        /* Blue - Information */
  
  /* Text Colors */
  --color-text-primary: #FFFFFF;
  --color-text-secondary: #A0A0A0;
  --color-text-muted: #666666;
  
  /* Typography */
  --font-display: "Space Grotesk", sans-serif;
  --font-body: "Inter", sans-serif;
  --font-mono: "JetBrains Mono", monospace;
  
  /* Spacing */
  --spacing-grid: 4px;
  
  /* Borders */
  --radius-none: 0px;
  --radius-sm: 2px;
  --radius-md: 4px;
}

body {
  background-color: var(--color-void);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
}

/* Utility for Tabular Numbers (Critical for Financial Data) */
.tabular-nums {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}
```

### 5.1.3 Typography Scale
```css
/* Typography - Space Grotesk for Headings, Inter for Body */
h1 { font-family: var(--font-display); font-size: 2.5rem; font-weight: 700; }
h2 { font-family: var(--font-display); font-size: 2rem; font-weight: 600; }
h3 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 600; }

p, span, label { font-family: var(--font-body); font-size: 1rem; }

/* All monetary values use monospace for alignment */
.money { 
  font-family: var(--font-mono); 
  font-variant-numeric: tabular-nums;
}
```

## 5.2 Component Library (Shadcn-UI Extended)

### 5.2.1 Core Components
| Component | Shadcn Base | Custom Styling |
|-----------|-------------|----------------|
| Button | `button` | Square corners, white bg, black text, hover invert |
| Input | `input` | 1px border, no rounded corners, green focus ring |
| Table | `table` | Visible grid lines, sticky header with blur |
| Card | `card` | Carbon bg, 1px border, no shadow |
| Dialog | `dialog` | Radix primitive, dark overlay, square corners |
| Toast | `toast` | Bottom-right, green/red based on status |
| Select | `select` | Radix primitive, custom dropdown styling |

### 5.2.2 Custom Financial Components
```tsx
// components/ui/money-input.tsx
"use client";

import { Input } from "@/components/ui/input";
import { useState, useCallback } from "react";

interface MoneyInputProps {
  value: string;
  onChange: (val: string) => void;
  className?: string;
  disabled?: boolean;
}

/**
 * Neo-Brutalist Money Input
 * - Auto-formats to SGD standard (1,234.56)
 * - Enforces numeric input
 * - Visual currency indicator
 */
export function MoneyInput({ value, onChange, className, disabled }: MoneyInputProps) {
  const formatMoney = useCallback((val: string): string => {
    // Remove non-numeric chars except decimal
    const numericVal = val.replace(/[^0-9.]/g, "");
    const parts = numericVal.split(".");
    
    // Limit to 2 decimal places for display
    if (parts.length > 2) return parts[0] + "." + parts[1];
    
    // Add commas for thousands
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    
    return parts.join(".");
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    const formatted = formatMoney(raw);
    onChange(formatted);
  };

  return (
    <div className={`relative group ${className}`}>
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground font-mono text-sm">
        S$
      </span>
      <Input
        type="text"
        inputMode="decimal"
        value={value}
        onChange={handleChange}
        disabled={disabled}
        className="pl-8 font-mono tracking-tight tabular-nums 
                   focus-visible:ring-accent/50 focus-visible:ring-2
                   transition-all duration-200 border-border bg-surface
                   rounded-none h-11"
        placeholder="0.00"
      />
      {/* Subtle border glow on focus */}
      <div className="absolute inset-0 rounded-none ring-1 ring-inset 
                      ring-white/5 group-focus-within:ring-accent/20 
                      pointer-events-none transition-all duration-200" />
    </div>
  );
}
```

```tsx
// components/ui/data-table.tsx
"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface DataTableProps<T> {
  columns: Array<{ key: string; header: string; render: (item: T) => React.ReactNode }>;
   T[];
  emptyState?: React.ReactNode;
}

/**
 * Neo-Brutalist Data Table
 * - Visible grid lines
 * - Tabular number alignment
 * - Sticky header with blur backdrop
 */
export function DataTable<T>({ columns, data, emptyState }: DataTableProps<T>) {
  if (data.length === 0) {
    return emptyState || (
      <div className="p-8 text-center text-muted-foreground border border-border">
        No data available
      </div>
    );
  }

  return (
    <div className="border border-border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="border-b border-border bg-surface">
            {columns.map((col) => (
              <TableHead 
                key={col.key} 
                className="font-display font-semibold text-text-primary 
                           border-r border-border last:border-r-0 h-12"
              >
                {col.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((item, rowIndex) => (
            <TableRow 
              key={rowIndex}
              className="border-b border-border hover:bg-surface/50 
                         transition-colors duration-150"
            >
              {columns.map((col, colIndex) => (
                <TableCell 
                  key={col.key}
                  className="font-mono tabular-nums text-text-secondary
                             border-r border-border last:border-r-0 h-12"
                >
                  {col.render(item)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
```

## 5.3 Key Pages & User Flows

### 5.3.1 Dashboard (Command Center)
```tsx
// app/dashboard/page.tsx
export default async function DashboardPage() {
  const stats = await getDashboardStats();
  const recentInvoices = await getRecentInvoices();
  const complianceAlerts = await getComplianceAlerts();
  
  return (
    <div className="p-6 space-y-6">
      {/* Compliance Alert Banner */}
      {complianceAlerts.length > 0 && (
        <AlertBanner alerts={complianceAlerts} />
      )}
      
      {/* Key Metrics - Asymmetric Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard 
          label="GST Payable" 
          value={stats.gstPayable} 
          trend={stats.gstTrend}
          variant="alert"
        />
        <MetricCard 
          label="Outstanding" 
          value={stats.outstanding} 
          trend={stats.outstandingTrend}
        />
        <MetricCard 
          label="Revenue (MTD)" 
          value={stats.revenue} 
          trend={stats.revenueTrend}
          variant="accent"
        />
        <MetricCard 
          label="TP Threshold" 
          value={stats.tpUtilization} 
          subtitle={`${stats.tpAmount} / S$2M`}
          variant={stats.tpUtilization > 80 ? 'warning' : 'default'}
        />
      </div>
      
      {/* Recent Invoices Table */}
      <section>
        <h2 className="font-display text-xl mb-4">Recent Invoices</h2>
        <DataTable 
          columns={invoiceColumns} 
          data={recentInvoices}
          emptyState={<EmptyState message="No invoices yet" />}
        />
      </section>
    </div>
  );
}
```

### 5.3.2 Invoice Builder
```tsx
// app/invoices/new/page.tsx
export default function NewInvoicePage() {
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <header className="mb-6 flex justify-between items-center">
        <h1 className="font-display text-2xl">New Invoice</h1>
        <div className="flex gap-3">
          <Button variant="outline">Save Draft</Button>
          <Button 
            variant="default" 
            className="bg-accent text-void hover:bg-accent-dim"
          >
            Send via Peppol
          </Button>
        </div>
      </header>
      
      <div className="grid grid-cols-3 gap-6">
        {/* Left: Line Items */}
        <div className="col-span-2 space-y-4">
          <CustomerSelect />
          <LineItemsTable />
          <BCRSToggle />
        </div>
        
        {/* Right: Tax Breakdown */}
        <div className="col-span-1">
          <TaxBreakdownCard />
          <PeppolStatusIndicator />
        </div>
      </div>
    </div>
  );
}
```

### 5.3.3 BCRS Deposit Toggle
```tsx
// components/invoice/bcrs-toggle.tsx
"use client";

import { Switch } from "@/components/ui/switch";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface BCRSToggleProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

export function BCRSToggle({ enabled, onToggle }: BCRSToggleProps) {
  return (
    <div className="flex items-center gap-3 p-4 border border-border bg-surface">
      <Switch
        checked={enabled}
        onCheckedChange={onToggle}
        className="data-[state=checked]:bg-accent"
      />
      <div className="flex-1">
        <label className="font-display text-sm">BCRS Deposit</label>
        <p className="text-muted-foreground text-xs">
          Add S$0.10 deposit per pre-packaged drink (not subject to GST)
        </p>
      </div>
      <Tooltip>
        <TooltipTrigger>
          <InfoIcon className="w-4 h-4 text-muted-foreground" />
        </TooltipTrigger>
        <TooltipContent>
          <p className="max-w-xs">
            Under the Beverage Container Return Scheme, a 10-cent deposit 
            applies to pre-packaged drinks. This deposit is NOT subject to GST 
            and is recorded as a liability.
          </p>
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
```

## 5.4 Server Actions & API Integration

```typescript
// app/actions/invoice.ts
"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { api } from "@/lib/api";
import { invoiceSchema } from "@/shared/schemas/invoice";

export async function createInvoice(formData: FormData) {
  // Validate with Zod
  const validated = invoiceSchema.parse(Object.fromEntries(formData));
  
  try {
    const response = await api.post("/invoices/", validated);
    
    // Revalidate dashboard and invoice list
    revalidatePath("/dashboard");
    revalidatePath("/invoices");
    
    redirect(`/invoices/${response.data.id}`);
  } catch (error) {
    // Return error to form
    return { error: "Failed to create invoice" };
  }
}

export async function sendPeppol(invoiceId: string) {
  try {
    const response = await api.post(`/invoices/${invoiceId}/send_peppol/`);
    revalidatePath(`/invoices/${invoiceId}`);
    return { success: true, taskId: response.data.task_id };
  } catch (error) {
    return { error: "Failed to send via Peppol" };
  }
}
```

---

# Part 6: Security & Compliance

## 6.1 Security Architecture

| Layer | Implementation | Purpose |
|-------|---------------|---------|
| **Authentication** | Django Session + HttpOnly Cookies | Prevent XSS token theft |
| **CSRF Protection** | Django CSRF Middleware | Prevent cross-site request forgery |
| **CSP** | Django 6.0 Native Middleware | Prevent content injection attacks |
| **Password Hashing** | Argon2 (Django 6.0 Default) | Stronger than PBKDF2 |
| **Rate Limiting** | Django Ratelimit | Prevent brute force attacks |
| **Data Encryption** | PostgreSQL pgcrypto | Encrypt sensitive fields at rest |
| **Audit Logging** | Immutable AuditLog model | 5-year retention for IRAS |
| **Input Validation** | Zod (Frontend) + DRF Serializers (Backend) | Prevent injection attacks |

## 6.2 CSP Configuration (Production)

```python
# config/settings.py
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE, "https://vercel.live"],
    "style-src": [CSP.SELF, CSP.NONCE, "https://fonts.googleapis.com"],
    "img-src": [CSP.SELF, "", "https:"],
    "connect-src": [
        CSP.SELF, 
        "https://api.peppol.sg", 
        "https://api.iras.gov.sg",
        "https://api.bankfeed.sg"
    ],
    "font-src": [CSP.SELF, "https://fonts.gstatic.com"],
    "frame-ancestors": [CSP.NONE],  # Prevent clickjacking
    "base-uri": [CSP.SELF],
    "form-action": [CSP.SELF],
}

# HSTS for production
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

## 6.3 Audit Trail Implementation

```python
# apps/core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog

@receiver(post_save)
@receiver(post_delete)
def log_audit(sender, instance, **kwargs):
    """
    Automatically log all changes to critical models.
    """
    # Skip audit log entries themselves (prevent infinite loop)
    if sender == AuditLog:
        return
    
    # Only log critical models
    critical_models = [Invoice, JournalEntry, Organization, Customer]
    if sender not in critical_models:
        return
    
    AuditLog.objects.create(
        organization=instance.organization if hasattr(instance, 'organization') else None,
        user=get_current_user(),  # Thread-local storage
        action='DELETE' if kwargs.get('signal') == post_delete else 'UPDATE',
        entity_type=ContentType.objects.get_for_model(sender),
        entity_id=instance.id,
    )
```

---

# Part 7: Implementation Phases

## Phase 1: Foundation (Weeks 1-3)
| Task | Deliverable | Validation |
|------|-------------|------------|
| Initialize Django 6.0 project | Working backend with settings | `python manage.py check` passes |
| Configure PostgreSQL 16 | Database with extensions | Connection test successful |
| Set up Next.js 15 + Tailwind 4 | Frontend scaffold | `npm run build` succeeds |
| Implement Auth (HttpOnly Cookies) | Login/Logout flow | Cookies are HttpOnly, Secure |
| Configure CSP | Security headers present | CSP header in responses |
| Create core models | Migrations applied | Schema matches blueprint |

## Phase 2: Core Accounting Engine (Weeks 4-7)
| Task | Deliverable | Validation |
|------|-------------|------------|
| Chart of Accounts | Singapore COA seeded | All account classes present |
| Journal Entry System | Double-entry enforcement | Debits = Credits always |
| GST Engine | 9% calculation with precision | Matches IRAS examples |
| Invoice CRUD | Full invoice lifecycle | Draft → Sent → Paid → Void |
| Audit Logging | Immutable logs | Logs cannot be deleted |

## Phase 3: Compliance Modules (Weeks 8-10)
| Task | Deliverable | Validation |
|------|-------------|------------|
| BCRS Support | Deposit toggle, non-GST | GST calculated on net only |
| TP Threshold | S$2M monitoring | Alert triggers at threshold |
| Reverse Charge | Overseas supplier handling | Journal entries correct |
| Peppol Integration | PINT-SG XML generation | Test invoice accepted |
| CIT Rebate | 50% rebate calculation | Matches IRAS formula |

## Phase 4: Frontend Development (Weeks 11-15)
| Task | Deliverable | Validation |
|------|-------------|------------|
| Dashboard | Key metrics, alerts | Lighthouse >90 |
| Invoice Builder | Line items, tax preview | Real-time calculation |
| Reports | GST F5, P&L, Balance Sheet | Export formats correct |
| Mobile Responsive | All pages work on mobile | Touch targets >44px |
| Accessibility | WCAG AA compliance | Axe DevTools passes |

## Phase 5: Testing & Hardening (Weeks 16-18)
| Task | Deliverable | Validation |
|------|-------------|------------|
| Unit Tests | 90%+ coverage | `pytest --cov` passes |
| Integration Tests | API + Frontend flows | CI pipeline green |
| Security Audit | Penetration test | No critical vulnerabilities |
| Load Testing | 1000 concurrent users | Response time <200ms |
| Documentation | User guides, API docs | Complete and accurate |

---

# Part 8: Quality Assurance Checklist

## Pre-Delivery Validation
- [ ] All 34+ unit tests covering GST calculation edge cases pass
- [ ] 100% of PINT-SG test invoices accepted by Peppol test environment
- [ ] BCRS test: S$10 drink + S$0.10 deposit → GST on S$10 only
- [ ] Reverse Charge test: S$1000 SaaS from overseas → S$90 GST accounted
- [ ] TP threshold alert triggers correctly at S$2M
- [ ] Audit logs are immutable (delete raises exception)
- [ ] CSP headers present on all responses
- [ ] All cookies are HttpOnly and Secure
- [ ] Frontend: No layout shifts on mobile
- [ ] Frontend: All interactive elements have loading states
- [ ] Accessibility: All forms have proper labels
- [ ] Accessibility: Color contrast meets WCAG AA
- [ ] Performance: Lighthouse score >90 for all metrics
- [ ] Security: Argon2 password hashing confirmed
- [ ] Database: All monetary fields use Decimal, not Float

---

# Part 9: Deployment & Operations

## 9.1 Infrastructure (Docker)

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: ledgersg
      POSTGRES_USER: ledgersg
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ledgersg"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./apps/backend
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    environment:
      - DATABASE_URL=postgresql://ledgersg:${DB_PASSWORD}@db:5432/ledgersg
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./apps/backend:/app

  worker:
    build: ./apps/backend
    command: python manage.py run_tasks
    environment:
      - DATABASE_URL=postgresql://ledgersg:${DB_PASSWORD}@db:5432/ledgersg
    depends_on:
      - db
      - backend

  frontend:
    build: ./apps/web
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
```

## 9.2 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: pip install -r apps/backend/requirements.txt
      - run: npm ci
      - run: cd apps/backend && pytest --cov
      - run: npm test
      - run: npm run lint

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy.sh
```

---

# Part 10: Knowledge Transfer & Documentation

## 10.1 Deliverables Upon Completion
1. **Architecture Decision Record (ADR)** - Explaining all key technical choices
2. **Compliance Mapping Document** - Each feature mapped to IRAS regulation
3. **Deployment Guide** - Docker, Kubernetes, environment variables
4. **API Documentation** - OpenAPI/Swagger spec
5. **User Training Materials** - Video scripts, in-app tooltips
6. **Maintenance Runbook** - How to update tax rates, Peppol certificates
7. **Security Audit Report** - Penetration test results, remediation

## 10.2 Future Recommendations
1. **Bank Feed Integration** - Direct API connections to DBS, UOB, OCBC
2. **OCR Receipt Scanning** - AI-powered receipt data extraction
3. **Multi-Currency Support** - For businesses with overseas transactions
4. **Payroll Module** - CPF calculations, IR8A generation
5. **Mobile App** - React Native for on-the-go invoicing

---

# Conclusion

This blueprint represents a **complete, production-ready architecture** for LedgerSG. It combines:

- **Regulatory Excellence:** Full compliance with IRAS 2026 requirements (InvoiceNow, BCRS, TP, GST)
- **Technical Rigor:** Django 6.0 native features, PostgreSQL 16, Next.js 15
- **Security First:** HttpOnly cookies, CSP, Argon2, immutable audit logs
- **Design Distinction:** Neo-Brutalist aesthetic that rejects generic SaaS templates
- **Operational Clarity:** Detailed implementation phases, validation checkpoints, deployment guides

**This document serves as the single source of truth for all subsequent implementation work.**

