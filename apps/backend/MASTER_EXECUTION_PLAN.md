# LedgerSG — Django Backend Codebase Completion Plan

## Pre-Planning Analysis

Before defining a single phase, I must establish the dependency graph, validate architectural constraints against the patched v1.0.1 schema, and make explicit every design decision that governs the backend structure.

---

### Dependency Graph (Phase Execution Order)

```
Phase 0: Project Foundation
    │   (settings, middleware, base classes, decimal utils)
    │
    ▼
Phase 1: Core Module ──────────────────────────────────────┐
    │   (org, users, auth, roles, fiscal, sequences)       │
    │                                                       │
    ├──────────────┬────────────────┐                      │
    ▼              ▼                │                       │
Phase 2:      Phase 3:             │                       │
COA Module    GST Module           │                       │
    │         (tax codes,          │                       │
    │          calculator)         │                       │
    │              │               │                       │
    └──────┬───────┘               │                       │
           ▼                       │                       │
       Phase 4:                    │                       │
       Journal Module              │                       │
       (GL, entries, lines)        │                       │
           │                       │                       │
           ▼                       │                       │
       Phase 5:                    │                       │
       Invoicing Module ◄──────────┘                       │
       (contacts, documents)                               │
           │                                               │
           ├───────────────┐                               │
           ▼               ▼                               │
       Phase 6:        Phase 7:                            │
       Banking         Peppol/InvoiceNow                   │
       Module          Module                              │
           │               │                               │
           └──────┬────────┘                               │
                  ▼                                        │
              Phase 8:                                     │
              Reporting Module ◄───────────────────────────┘
                  │
                  ▼
              Phase 9:
              Integration, Testing & Hardening
```

### Governing Architectural Decisions

| Decision | Rationale |
|---|---|
| **Unmanaged Django Models** | Schema is DDL-managed (our SQL script), not Django migrations. All models use `class Meta: managed = False; db_table = 'schema.table'` |
| **Service Layer Pattern** | Views are thin controllers. All business logic lives in `services/` modules. This keeps views testable and logic reusable |
| **Repository-Optional** | Django ORM is the data access layer. No redundant repository wrappers. Services call ORM directly |
| **Decimal Context Manager** | Every financial computation is wrapped in `decimal_context()` ensuring `ROUND_HALF_UP` with 4dp |
| **RLS via Middleware** | Every request sets `SET LOCAL app.current_org_id` and `app.current_user_id` within a transaction. This is the ONLY multi-tenant enforcement |
| **Custom DB Router** | Reads go to replica (future), writes go to primary. All operations within a single `ATOMIC` transaction for RLS consistency |
| **DRF (Django REST Framework)** | Primary API framework. ViewSets for CRUD, APIViews for custom actions |
| **JWT Authentication** | `djangorestframework-simplejwt` with short-lived access tokens (15min) and HttpOnly refresh tokens |
| **Celery for Async** | Peppol transmission, PDF generation, GST threshold monitoring, email reminders |
| **Test-Driven** | Every service gets tests written FIRST (TDD). Factory pattern with `model_bakery` or custom factories |

---

## Phase 0: Project Foundation & Infrastructure

### Objective
Establish the Django project skeleton, configuration system, shared utilities, middleware pipeline, base model classes, custom database backend, and Decimal safety infrastructure. After this phase: `python manage.py check` passes, middleware pipeline is functional, and all shared utilities are independently tested.

### Dependencies
None — this is the root phase.

### Files to Create

```
ledgersg-api/
│
├── pyproject.toml
├── manage.py
├── Makefile
├── .env.example
├── docker-compose.yml
├── Dockerfile
│
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
│
├── common/
│   ├── __init__.py
│   ├── models.py
│   ├── decimal_utils.py
│   ├── currency.py
│   ├── pagination.py
│   ├── exceptions.py
│   ├── renderers.py
│   ├── throttling.py
│   ├── types.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── tenant_context.py
│   │   └── audit_context.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── backend/
│   │   │   ├── __init__.py
│   │   │   └── base.py
│   │   └── routers.py
│   └── tests/
│       ├── __init__.py
│       ├── test_decimal_utils.py
│       ├── test_currency.py
│       ├── test_middleware.py
│       └── test_pagination.py
│
└── apps/
    └── __init__.py
```

### File Specifications

---

#### `pyproject.toml`
**Purpose**: Project metadata, dependency management (PEP 621), tool configuration.

```toml
[project]
name = "ledgersg-api"
version = "1.0.0"
description = "Enterprise-grade accounting API for Singapore SMBs"
requires-python = ">=3.13"

dependencies = [
    # Core Framework
    "django>=5.2,<6.1",
    "djangorestframework>=3.15,<4.0",
    "djangorestframework-simplejwt>=5.3,<6.0",
    "django-cors-headers>=4.4,<5.0",
    "django-filter>=24.0",

    # Database
    "psycopg[binary]>=3.2,<4.0",          # Psycopg 3 (not psycopg2)
    "django-pgtrigger>=4.11,<5.0",         # Trigger management (optional helpers)

    # Async / Task Queue
    "celery[redis]>=5.4,<6.0",
    "django-celery-beat>=2.6,<3.0",
    "redis>=5.0,<6.0",

    # Decimal / Financial
    "py-moneyed>=3.0,<4.0",               # Currency-aware Decimal

    # Serialization / Validation
    "pydantic>=2.7,<3.0",                  # Internal validation (not API layer)

    # PDF Generation
    "weasyprint>=62.0",

    # XML (Peppol PINT-SG)
    "lxml>=5.2",

    # Utilities
    "python-decouple>=3.8",
    "whitenoise>=6.7",
    "gunicorn>=22.0",
    "structlog>=24.0",                      # Structured logging
    "sentry-sdk[django]>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2",
    "pytest-django>=4.8",
    "pytest-cov>=5.0",
    "pytest-xdist>=3.5",
    "model-bakery>=1.18",                   # Test fixture factories
    "factory-boy>=3.3",
    "faker>=25.0",
    "httpx>=0.27",                          # Async test client
    "ruff>=0.5",                            # Linter + formatter
    "mypy>=1.10",
    "django-stubs>=5.0",
    "djangorestframework-stubs>=3.15",
    "pre-commit>=3.7",
    "ipython>=8.25",
    "django-debug-toolbar>=4.4",
    "django-extensions>=3.2",
]

[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "S", "B", "A", "C4", "SIM", "TCH"]
ignore = ["S101"]  # Allow assert in tests

[tool.ruff.lint.isort]
known-first-party = ["apps", "common", "config"]

[tool.mypy]
python_version = "3.13"
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.django-stubs]
django_settings_module = "config.settings.development"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.testing"
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--strict-markers --tb=short -q"
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
]
```

---

#### `config/settings/base.py`
**Purpose**: Shared settings across all environments. Database configuration, installed apps, middleware pipeline, REST framework config, JWT settings, decimal context defaults, logging.

**Key design decisions**:
- `ATOMIC_REQUESTS = True` — every view runs in a single transaction (required for RLS `SET LOCAL`)
- Custom database backend that injects RLS session variables
- `DECIMAL_PLACES = 4` as a project-wide constant
- Structured logging via `structlog`
- CORS restricted to frontend origin

**Features**:
- Database connection to PostgreSQL 16 via psycopg3
- `ATOMIC_REQUESTS = True` for transaction-per-request (RLS requirement)
- `AUTH_USER_MODEL = 'core.AppUser'`
- JWT configuration: 15-minute access, 7-day refresh, HttpOnly refresh cookie
- REST framework: pagination, exception handling, permission defaults
- Celery broker configuration (Redis)
- Timezone: `Asia/Singapore`

---

#### `config/settings/development.py`
**Purpose**: Development overrides — debug mode, console email backend, CORS allow-all, debug toolbar, expanded logging.

---

#### `config/settings/production.py`
**Purpose**: Production hardening — `DEBUG=False`, HTTPS enforcement, HSTS, CSP headers, Sentry DSN, WhiteNoise static file serving, restricted CORS origins.

---

#### `config/settings/testing.py`
**Purpose**: Test-optimised settings — in-memory password hashing, disabled throttling, synchronous Celery (`CELERY_ALWAYS_EAGER`), test database prefix.

---

#### `config/urls.py`
**Purpose**: Root URL configuration. Mounts API version namespace `/api/v1/`, health check endpoint, admin (development only).

**Interfaces**:
```
GET  /api/v1/health/              → Health check (DB connectivity, Redis)
     /api/v1/auth/                → Auth module URLs
     /api/v1/organisations/       → Core module URLs
     /api/v1/{org_id}/            → Org-scoped module URLs (COA, GST, invoicing, etc.)
```

---

#### `config/celery.py`
**Purpose**: Celery application factory. Auto-discovers tasks from all `apps/` modules. Redis as broker and result backend. Beat schedule for periodic tasks (GST threshold monitoring, overdue invoice flagging).

---

#### `common/models.py`
**Purpose**: Abstract base models inherited by all app models.

**Classes**:
- `BaseModel(models.Model)` — Abstract. Adds `id` (UUID), `created_at`, `updated_at`. Sets `managed = False`.
- `TenantModel(BaseModel)` — Abstract. Adds `org_id` (UUID FK). All tenant-scoped models inherit this.
- `ImmutableModel(BaseModel)` — Abstract. Overrides `save()` to block updates after initial creation. For journal entries.

**Key design**:
```python
class TenantModel(BaseModel):
    """
    Abstract model for all multi-tenant tables.
    org_id is set automatically from the request context via middleware.
    All queries are further filtered by PostgreSQL RLS.
    """
    org = models.ForeignKey(
        'core.Organisation',
        on_delete=models.CASCADE,
        db_column='org_id',
        editable=False,
    )

    class Meta:
        abstract = True

    def save(self, **kwargs):
        if not self.org_id:
            from common.middleware.tenant_context import get_current_org_id
            self.org_id = get_current_org_id()
        super().save(**kwargs)
```

---

#### `common/decimal_utils.py`
**Purpose**: Centralised Decimal safety infrastructure. Every financial calculation in the system MUST use these utilities.

**Functions/Classes**:
- `MONEY_PRECISION = Decimal('0.0001')` — 4 decimal places
- `DISPLAY_PRECISION = Decimal('0.01')` — 2 decimal places for API responses
- `money(value) → Decimal` — Safely converts any input to a Decimal quantized to 4dp
- `display_money(value) → str` — Formats Decimal to 2dp string for JSON serialization
- `decimal_context()` — Context manager that sets `ROUND_HALF_UP` and traps overflow/invalid
- `MoneyField` — Custom DRF serializer field that enforces Decimal parsing, rejects float
- `sum_money(iterable) → Decimal` — Sum with proper quantization
- `multiply_money(a, b) → Decimal` — Product quantized to 4dp

**Critical design**:
```python
from decimal import Decimal, ROUND_HALF_UP, localcontext, InvalidOperation

MONEY_PLACES = Decimal('0.0001')

def money(value: str | int | float | Decimal) -> Decimal:
    """
    Convert any numeric input to a Decimal at 4dp.
    REJECTS float inputs in strict mode to prevent precision loss.
    """
    if isinstance(value, float):
        raise TypeError(
            f"Float {value} is not allowed for monetary values. "
            f"Use str or Decimal: money('{value}')"
        )
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        ctx.traps[InvalidOperation] = True
        return Decimal(str(value)).quantize(MONEY_PLACES)
```

---

#### `common/currency.py`
**Purpose**: Multi-currency helpers. Exchange rate lookup, conversion, FX gain/loss calculation.

**Functions**:
- `convert_to_base(amount, rate) → Decimal` — Convert foreign currency amount to SGD
- `calculate_fx_gain_loss(original_base, settlement_base) → Decimal` — For payment settlement
- `get_exchange_rate(org_id, currency_code, date) → Decimal` — Lookup from `core.exchange_rate` table

---

#### `common/pagination.py`
**Purpose**: Custom pagination classes for DRF.

**Classes**:
- `StandardPagination` — Cursor-based (for large datasets like journal entries, audit logs)
- `PageNumberPagination` — Offset-based with configurable `page_size` (invoices, contacts)

---

#### `common/exceptions.py`
**Purpose**: Custom exception hierarchy and global exception handler.

**Classes**:
- `LedgerSGException(Exception)` — Base
- `ValidationError(LedgerSGException)` — Business rule violations
- `ImmutabilityError(LedgerSGException)` — Attempt to modify immutable records
- `UnbalancedEntryError(LedgerSGException)` — Journal entry doesn't balance
- `PeriodClosedError(LedgerSGException)` — Posting to a closed fiscal period
- `GSTCalculationError(LedgerSGException)` — Tax computation failure
- `PeppolTransmissionError(LedgerSGException)` — InvoiceNow failures
- `custom_exception_handler(exc, context) → Response` — DRF exception handler

---

#### `common/renderers.py`
**Purpose**: Custom JSON renderer that handles Decimal serialization correctly (not converting to float).

**Key design**: Override `JSONRenderer` to use a custom encoder that calls `str()` on `Decimal` values instead of `float()`. This prevents precision loss in API responses.

---

#### `common/types.py`
**Purpose**: Type aliases and TypedDicts used across the project.

**Types**:
- `OrgID = UUID`
- `UserID = UUID`
- `MoneyValue = Decimal`
- `TaxCode = str`
- `GSTResult = TypedDict('GSTResult', {'net_amount': Decimal, 'gst_amount': Decimal, ...})`

---

#### `common/throttling.py`
**Purpose**: Rate limiting classes. 100 req/min for authenticated users, 20 req/min for anonymous.

---

#### `common/middleware/tenant_context.py`
**Purpose**: **THE MOST CRITICAL MIDDLEWARE IN THE SYSTEM.** Extracts `org_id` from the URL path (e.g., `/api/v1/{org_id}/invoices/`), validates user membership, and sets PostgreSQL session variables for RLS.

**Design**:
```python
"""
Tenant Context Middleware

For EVERY request to an org-scoped URL:
1. Extract org_id from URL path
2. Verify the authenticated user belongs to that org
3. Execute SET LOCAL app.current_org_id = '...' within the atomic transaction
4. Execute SET LOCAL app.current_user_id = '...'
5. Store org_id in contextvars for application-level access

Uses contextvars (NOT threading.local) per Python 3.13+ best practices
for compatibility with async contexts and ASGI.
"""
import contextvars
from uuid import UUID
from django.db import connection
from django.http import HttpRequest

# Contextvars for application-layer access
_current_org_id: contextvars.ContextVar[UUID | None] = contextvars.ContextVar(
    'current_org_id', default=None
)
_current_user_id: contextvars.ContextVar[UUID | None] = contextvars.ContextVar(
    'current_user_id', default=None
)

def get_current_org_id() -> UUID | None:
    return _current_org_id.get()

def get_current_user_id() -> UUID | None:
    return _current_user_id.get()
```

**Middleware class flow**:
1. Parse URL → extract `{org_id}` segment
2. If not org-scoped URL (e.g., `/api/v1/auth/login`), pass through
3. Query `core.user_organisation` to verify membership (with caching)
4. Load user's `role` for this org → attach to `request.org_role`
5. Within the existing atomic transaction (ATOMIC_REQUESTS=True):
   ```python
   with connection.cursor() as cursor:
       cursor.execute("SET LOCAL app.current_org_id = %s", [str(org_id)])
       cursor.execute("SET LOCAL app.current_user_id = %s", [str(user.id)])
   ```
6. Set contextvars for application-level access
7. Attach `request.org_id` and `request.org` for view convenience

---

#### `common/middleware/audit_context.py`
**Purpose**: Captures request metadata (IP address, user agent, request path) and makes it available to the audit trigger system via `SET LOCAL` session variables.

**Design**:
```python
# Sets these for the audit.log_change() trigger to read:
cursor.execute("SET LOCAL app.client_ip = %s", [ip_address])
cursor.execute("SET LOCAL app.user_agent = %s", [user_agent])
cursor.execute("SET LOCAL app.request_path = %s", [request.path])
```

---

#### `common/db/backend/base.py`
**Purpose**: Custom PostgreSQL database backend that extends `django.db.backends.postgresql`. Configures psycopg3 connection options (statement timeout, application name, search_path).

**Key feature**: Sets `search_path` to include all LedgerSG schemas:
```python
'OPTIONS': {
    'options': '-c search_path=core,coa,gst,journal,invoicing,banking,audit,public'
}
```

---

#### `common/db/routers.py`
**Purpose**: Database router for future read-replica support. Currently routes all reads and writes to the `default` database.

---

#### `Makefile`
**Purpose**: Developer convenience commands.

```makefile
dev:          # Start development server
test:         # Run test suite
test-cov:     # Run with coverage report
lint:         # Run ruff linter
format:       # Run ruff formatter
typecheck:    # Run mypy
migrate:      # Run Django migrations
celery:       # Start Celery worker
celery-beat:  # Start Celery beat scheduler
shell:        # Django shell with IPython
```

---

### Phase 0 Checklist

```
□ pyproject.toml created with all dependencies pinned
□ Django project boots: `python manage.py check` passes
□ All four settings files complete (base, dev, prod, test)
□ ATOMIC_REQUESTS = True in base settings
□ Custom DB backend with search_path configured
□ Psycopg3 connection verified to PostgreSQL 16
□ Tenant context middleware:
    □ Extracts org_id from URL path
    □ Sets SET LOCAL app.current_org_id
    □ Sets SET LOCAL app.current_user_id
    □ Uses contextvars (not threading.local)
    □ Passes through for non-org-scoped URLs
    □ Returns 403 for unauthorized org access
□ Audit context middleware captures IP, user agent, path
□ common/decimal_utils.py:
    □ money() rejects float input
    □ money() quantizes to 4dp with ROUND_HALF_UP
    □ sum_money() preserves precision
□ common/exceptions.py: all custom exceptions defined
□ common/renderers.py: Decimal serialized as string, not float
□ common/pagination.py: cursor + page-number pagination classes
□ Celery app factory configured with Redis broker
□ Docker Compose: PostgreSQL 16 + Redis containers
□ Test suite infrastructure: pytest-django configured
□ All common/ tests pass
□ Ruff lint passes with zero errors
□ Mypy typecheck passes
```

---

## Phase 1: Core Module — Organisation, Users, Auth, Roles, Fiscal

### Objective
Implement the tenant root: organisation CRUD, user authentication (JWT), role-based access control, fiscal year/period management, currency reference data, exchange rates, document sequence service. After this phase: a user can register, create an org, log in, receive JWT tokens, and the org gets a seeded Chart of Accounts and document sequences.

### Dependencies
Phase 0 (Foundation)

### Files to Create

```
apps/core/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── organisation.py
│   ├── app_user.py
│   ├── role.py
│   ├── user_organisation.py
│   ├── fiscal_year.py
│   ├── fiscal_period.py
│   ├── currency.py
│   ├── exchange_rate.py
│   ├── document_sequence.py
│   └── organisation_setting.py
├── serializers/
│   ├── __init__.py
│   ├── auth.py
│   ├── organisation.py
│   ├── user.py
│   ├── fiscal.py
│   ├── currency.py
│   └── exchange_rate.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── organisation_service.py
│   ├── fiscal_service.py
│   ├── exchange_rate_service.py
│   └── sequence_service.py
├── permissions.py
├── signals.py
├── urls.py
├── views/
│   ├── __init__.py
│   ├── auth.py
│   ├── organisation.py
│   ├── user.py
│   ├── fiscal.py
│   └── exchange_rate.py
├── admin.py
└── tests/
    ├── __init__.py
    ├── factories.py
    ├── test_models.py
    ├── test_services.py
    ├── test_views.py
    ├── test_auth.py
    ├── test_fiscal.py
    └── test_permissions.py
```

### File Specifications

---

#### `apps/core/models/organisation.py`
**Purpose**: Django ORM mapping to `core.organisation` table.

**Key fields**: `id`, `name`, `legal_name`, `uen`, `entity_type`, `gst_registered`, `gst_reg_number`, `gst_reg_date`, `gst_scheme`, `gst_filing_frequency`, `peppol_participant_id`, `invoicenow_enabled`, `fy_start_month`, `base_currency`, `timezone`, address fields, `is_active`.

**Design**: `managed = False`, `db_table = 'core"."organisation'` (quoted schema.table for PostgreSQL).

**Properties**:
- `is_gst_registered` → Boolean check with validation
- `current_fiscal_year` → Retrieves the open fiscal year
- `gst_filing_periods_per_year` → Returns 4 (quarterly), 12 (monthly), or 2 (semi-annual)

---

#### `apps/core/models/app_user.py`
**Purpose**: Custom user model extending `AbstractBaseUser`. Maps to `core.app_user`. Implements Django's authentication interface.

**Key design**: Does NOT use Django's built-in `auth_user` table. Maps directly to our `core.app_user` schema. Password hashing via Django's `make_password`/`check_password`.

**Fields**: `email` (USERNAME_FIELD), `full_name`, `phone`, `is_active`, `is_superadmin`.

---

#### `apps/core/models/role.py`
**Purpose**: Maps to `core.role`. Represents permission roles with granular boolean flags.

**Fields**: `name`, `can_manage_org`, `can_manage_users`, `can_manage_coa`, `can_create_invoices`, `can_approve_invoices`, `can_void_invoices`, `can_create_journals`, `can_manage_banking`, `can_file_gst`, `can_view_reports`, `can_export_data`, `is_system`.

---

#### `apps/core/models/user_organisation.py`
**Purpose**: Maps to `core.user_organisation`. Many-to-many join between users and orgs, carrying the role assignment.

**Fields**: `user`, `org`, `role`, `is_default`, `invited_at`, `accepted_at`.

---

#### `apps/core/models/fiscal_year.py` and `fiscal_period.py`
**Purpose**: Maps to `core.fiscal_year` and `core.fiscal_period`. Supports Singapore's flexible FY end dates.

---

#### `apps/core/models/currency.py` and `exchange_rate.py`
**Purpose**: Maps to `core.currency` (global reference) and `core.exchange_rate` (org-specific daily rates).

---

#### `apps/core/models/document_sequence.py`
**Purpose**: Maps to `core.document_sequence`. Auto-numbering configuration per org per document type.

---

#### `apps/core/models/organisation_setting.py`
**Purpose**: Maps to `core.organisation_setting`. Key-value configuration store.

---

#### `apps/core/services/auth_service.py`
**Purpose**: Authentication business logic.

**Functions**:
- `register_user(email, password, full_name) → AppUser` — Creates user, hashes password
- `authenticate(email, password) → tuple[AppUser, TokenPair]` — Validates credentials, returns JWT pair
- `refresh_token(refresh) → TokenPair` — Refreshes access token
- `change_password(user, old_password, new_password) → None`
- `get_user_organisations(user) → QuerySet[UserOrganisation]`

---

#### `apps/core/services/organisation_service.py`
**Purpose**: Organisation lifecycle management.

**Functions**:
- `create_organisation(user, data) → Organisation` — Creates org, assigns Owner role, calls `seed_default_chart_of_accounts()` via raw SQL, creates document sequences, creates first fiscal year + periods
- `update_organisation(org_id, data) → Organisation` — Validates GST consistency (if registered, must have reg number + date)
- `toggle_gst_registration(org_id, registered, reg_number, reg_date) → Organisation` — Handles GST registration status change, seeds GST accounts if newly registered
- `get_organisation_detail(org_id) → Organisation` — Full org with related settings

**Critical**: On org creation, this service calls the PostgreSQL function:
```python
with connection.cursor() as cursor:
    cursor.execute("SELECT core.seed_default_chart_of_accounts(%s, %s)", [org.id, org.gst_registered])
```

---

#### `apps/core/services/fiscal_service.py`
**Purpose**: Fiscal year and period management.

**Functions**:
- `create_fiscal_year(org_id, label, start_date, end_date) → FiscalYear` — Creates year, calls `core.generate_fiscal_periods()` stored procedure
- `close_fiscal_period(period_id, user_id) → FiscalPeriod` — Sets `is_open=False`, records `locked_at`/`locked_by`
- `close_fiscal_year(year_id, user_id) → FiscalYear` — Closes all remaining periods, sets `is_closed=True`
- `get_period_for_date(org_id, date) → FiscalPeriod` — Finds the open period containing the given date
- `validate_posting_date(org_id, date) → bool` — Checks if date falls within an open period

---

#### `apps/core/services/sequence_service.py`
**Purpose**: Thread-safe document number generation.

**Functions**:
- `next_number(org_id, document_type) → str` — Calls `core.next_document_number()` stored procedure. Returns formatted string (e.g., `INV-00001`).

**Design**: This function MUST be called within the same database transaction as the document creation to maintain gap-free numbering.

---

#### `apps/core/services/exchange_rate_service.py`
**Purpose**: Exchange rate management.

**Functions**:
- `set_rate(org_id, currency_code, date, rate, source) → ExchangeRate`
- `get_rate(org_id, currency_code, date) → Decimal` — Looks up rate, falls back to nearest prior date if exact match not found
- `convert_to_sgd(amount, currency_code, date, org_id) → Decimal`

---

#### `apps/core/permissions.py`
**Purpose**: DRF permission classes that check the user's role within the current org.

**Classes**:
- `IsAuthenticated` — Base JWT authentication check
- `IsOrgMember` — User belongs to the org in the URL path
- `HasOrgPermission(permission_field)` — Factory that creates permission classes from role fields
- `CanManageOrg = HasOrgPermission('can_manage_org')`
- `CanCreateInvoices = HasOrgPermission('can_create_invoices')`
- `CanApproveInvoices = HasOrgPermission('can_approve_invoices')`
- `CanFileGST = HasOrgPermission('can_file_gst')`
- `CanViewReports = HasOrgPermission('can_view_reports')`
- ... (one per role flag)

---

#### `apps/core/signals.py`
**Purpose**: Post-save signal on `Organisation` for initialisation tasks. On create: seed CoA, create sequences, create first fiscal year.

**Design decision**: Signals vs. explicit service call. We use the **service pattern** — `organisation_service.create_organisation()` handles all side effects explicitly. Signals are used only for decoupled concerns (e.g., sending a welcome email via Celery).

---

#### `apps/core/views/auth.py`
**Purpose**: Authentication endpoints.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register/` | `RegisterView` | Create user account |
| POST | `/api/v1/auth/login/` | `LoginView` | Authenticate, return JWT pair |
| POST | `/api/v1/auth/refresh/` | `RefreshView` | Refresh access token |
| POST | `/api/v1/auth/logout/` | `LogoutView` | Blacklist refresh token |
| GET | `/api/v1/auth/me/` | `CurrentUserView` | Return authenticated user profile |
| PATCH | `/api/v1/auth/me/` | `CurrentUserView` | Update profile |
| POST | `/api/v1/auth/change-password/` | `ChangePasswordView` | Change password |

---

#### `apps/core/views/organisation.py`
**Purpose**: Organisation management endpoints.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| GET | `/api/v1/organisations/` | `OrganisationListView` | List user's organisations |
| POST | `/api/v1/organisations/` | `OrganisationCreateView` | Create new org (seeds CoA, fiscal year) |
| GET | `/api/v1/{org_id}/` | `OrganisationDetailView` | Org detail |
| PATCH | `/api/v1/{org_id}/` | `OrganisationDetailView` | Update org settings |
| GET | `/api/v1/{org_id}/settings/` | `OrgSettingsView` | Organisation key-value settings |
| PATCH | `/api/v1/{org_id}/settings/` | `OrgSettingsView` | Update settings |

---

#### `apps/core/views/user.py`
**Purpose**: User management within an org context.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| GET | `/api/v1/{org_id}/users/` | `OrgUserListView` | List users in this org |
| POST | `/api/v1/{org_id}/users/invite/` | `InviteUserView` | Invite user to org |
| PATCH | `/api/v1/{org_id}/users/{user_id}/role/` | `UpdateUserRoleView` | Change user's role |
| DELETE | `/api/v1/{org_id}/users/{user_id}/` | `RemoveUserView` | Remove user from org |

---

#### `apps/core/views/fiscal.py`
**Purpose**: Fiscal year and period management.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| GET | `/api/v1/{org_id}/fiscal-years/` | `FiscalYearListView` | List fiscal years |
| POST | `/api/v1/{org_id}/fiscal-years/` | `FiscalYearCreateView` | Create new fiscal year |
| GET | `/api/v1/{org_id}/fiscal-years/{fy_id}/` | `FiscalYearDetailView` | Detail with periods |
| POST | `/api/v1/{org_id}/fiscal-years/{fy_id}/close/` | `CloseFiscalYearView` | Close fiscal year |
| POST | `/api/v1/{org_id}/fiscal-periods/{fp_id}/close/` | `CloseFiscalPeriodView` | Close individual period |

---

#### `apps/core/views/exchange_rate.py`
**Purpose**: Exchange rate management.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| GET | `/api/v1/{org_id}/exchange-rates/` | `ExchangeRateListView` | List rates (filterable by currency, date range) |
| POST | `/api/v1/{org_id}/exchange-rates/` | `ExchangeRateCreateView` | Set a rate for a currency + date |
| GET | `/api/v1/{org_id}/currencies/` | `CurrencyListView` | List active currencies (global reference) |

---

### Phase 1 Checklist

```
□ All 11 model files created and mapped to schema tables
□ All models use managed = False
□ AppUser extends AbstractBaseUser with email as USERNAME_FIELD
□ AUTH_USER_MODEL = 'core.AppUser' in settings
□ Organisation model enforces GST consistency constraint at Python level
□ auth_service:
    □ register_user hashes password via Django's make_password
    □ authenticate returns JWT pair (access + refresh)
    □ Token blacklisting on logout
□ organisation_service:
    □ create_organisation calls seed_default_chart_of_accounts() stored proc
    □ create_organisation creates document sequences
    □ create_organisation creates first fiscal year + generates periods
    □ Validates UEN uniqueness
    □ GST toggle seeds GST accounts (1600, 2600, 2610) if newly registered
□ fiscal_service:
    □ create_fiscal_year calls generate_fiscal_periods() stored proc
    □ close_fiscal_period sets locked_at, locked_by
    □ validate_posting_date rejects closed period dates
□ sequence_service:
    □ next_number calls core.next_document_number() stored proc
    □ Returns correctly formatted string (prefix + padded number)
□ exchange_rate_service:
    □ get_rate falls back to nearest prior date
    □ convert_to_sgd returns NUMERIC(10,4) precision
□ Permissions:
    □ IsOrgMember validates user_organisation membership
    □ HasOrgPermission checks role boolean flags
    □ All permission classes tested
□ Views:
    □ All auth endpoints functional
    □ All org CRUD endpoints functional
    □ All fiscal endpoints functional
    □ Org-scoped URLs include {org_id} parameter
□ Serializers:
    □ All monetary fields use MoneyField from decimal_utils
    □ Organisation serializer validates GST consistency
    □ Nested serializers for org detail (with fiscal years, settings)
□ Tests:
    □ factories.py with OrganisationFactory, AppUserFactory, RoleFactory
    □ test_auth: register, login, refresh, logout, change_password
    □ test_organisation: create, update, GST toggle, detail
    □ test_fiscal: create year, close period, close year
    □ test_permissions: org membership, role-based access
    □ All tests pass
□ URL configuration complete and mounted in config/urls.py
```

---

## Phase 2: Chart of Accounts Module

### Objective
Implement the Chart of Accounts: hierarchical account tree, account CRUD with type/sub-type classification, system account protection, header account logic. After this phase: users can view their seeded CoA, create/edit custom accounts, and see the hierarchical tree structure.

### Dependencies
Phase 1 (Core — for Organisation, auth, permissions)

### Files to Create

```
apps/accounting/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── account_type.py
│   ├── account_sub_type.py
│   └── account.py
├── serializers/
│   ├── __init__.py
│   └── account.py
├── services/
│   ├── __init__.py
│   └── coa_service.py
├── filters.py
├── urls.py
├── views/
│   ├── __init__.py
│   └── account.py
└── tests/
    ├── __init__.py
    ├── factories.py
    ├── test_models.py
    ├── test_coa_service.py
    └── test_views.py
```

### File Specifications

---

#### `apps/accounting/models/account.py`
**Purpose**: Maps to `coa.account`. Hierarchical chart of accounts with self-referencing `parent_id`.

**Key fields**: `org`, `code`, `name`, `description`, `account_type`, `account_sub_type`, `parent`, `currency`, `tax_code_default`, `is_system`, `is_header`, `is_active`, `is_bank`, `is_control`.

**Model methods**:
- `get_descendants() → QuerySet` — Returns all child accounts recursively (using CTE or adjacency list traversal)
- `get_ancestors() → list[Account]` — Returns path to root
- `is_postable → bool` — Returns `True` if not a header account and is active
- `balance_at(date) → Decimal` — Computes account balance from journal lines up to the given date

---

#### `apps/accounting/models/account_type.py` and `account_sub_type.py`
**Purpose**: Maps to `coa.account_type` and `coa.account_sub_type`. Global reference tables (read-only from application).

---

#### `apps/accounting/services/coa_service.py`
**Purpose**: Chart of Accounts business logic.

**Functions**:
- `get_account_tree(org_id) → list[dict]` — Returns hierarchical tree structure for UI rendering. Uses a single query with recursive CTE for performance
- `create_account(org_id, data) → Account` — Validates: code uniqueness, parent exists, not posting to header, valid account type/sub-type
- `update_account(account_id, data) → Account` — Blocks editing of system accounts. Validates code uniqueness
- `deactivate_account(account_id) → Account` — Soft-deactivate. Checks that account has zero balance and no pending transactions
- `get_account_balance(account_id, as_of_date) → Decimal` — Aggregates journal lines for this account up to the date
- `get_trial_balance(org_id, as_of_date) → list[dict]` — All accounts with their debit/credit balances
- `validate_account_for_posting(account_id) → bool` — Checks active, not header, not closed

---

#### `apps/accounting/views/account.py`
**Purpose**: Account CRUD endpoints.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| GET | `/api/v1/{org_id}/accounts/` | `AccountListView` | Flat or tree view (query param `?view=tree`) |
| POST | `/api/v1/{org_id}/accounts/` | `AccountCreateView` | Create custom account |
| GET | `/api/v1/{org_id}/accounts/{id}/` | `AccountDetailView` | Account detail with balance |
| PATCH | `/api/v1/{org_id}/accounts/{id}/` | `AccountDetailView` | Update account |
| DELETE | `/api/v1/{org_id}/accounts/{id}/` | `AccountDetailView` | Deactivate account |
| GET | `/api/v1/{org_id}/accounts/types/` | `AccountTypeListView` | List account types + sub-types |

---

### Phase 2 Checklist

```
□ Account model maps to coa.account with managed = False
□ AccountType and AccountSubType models map to reference tables
□ coa_service:
    □ get_account_tree uses recursive CTE for hierarchy
    □ create_account validates code uniqueness within org
    □ create_account rejects duplicate codes
    □ update_account blocks modification of is_system accounts
    □ deactivate_account checks zero balance
    □ get_trial_balance aggregates journal lines correctly
□ Views:
    □ Tree view returns nested JSON structure
    □ Flat view returns paginated list
    □ System accounts cannot be deleted
    □ Account types endpoint returns global reference data
□ Serializers:
    □ Account serializer includes computed balance field
    □ Nested account type/sub-type names
    □ Validates parent_id references an existing account in same org
□ Tests:
    □ test_coa_service: tree building, balance computation, validation
    □ test_views: CRUD operations, system account protection
    □ All tests pass
□ URL routes mounted under /api/v1/{org_id}/accounts/
```

---

## Phase 3: GST Module — Tax Codes & Calculator

### Objective
Implement the GST calculation engine: tax code management, rate-date-aware computation, line-level and document-level GST calculation, and the threshold monitoring service for non-registered businesses. After this phase: the GST calculation API is functional and fully tested with edge cases for all Singapore tax code scenarios.

### Dependencies
Phase 1 (Core — for Organisation, org_id context)

### Files to Create

```
apps/gst/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── tax_code.py
│   ├── gst_return.py
│   └── threshold_snapshot.py
├── serializers/
│   ├── __init__.py
│   ├── tax_code.py
│   ├── gst_calculation.py
│   └── gst_return.py
├── services/
│   ├── __init__.py
│   ├── gst_calculator.py
│   ├── gst_return_service.py
│   └── threshold_service.py
├── urls.py
├── views/
│   ├── __init__.py
│   ├── tax_code.py
│   └── calculation.py
└── tests/
    ├── __init__.py
    ├── factories.py
    ├── test_gst_calculator.py
    ├── test_threshold_service.py
    └── test_views.py
```

### File Specifications

---

#### `apps/gst/models/tax_code.py`
**Purpose**: Maps to `gst.tax_code`. Global reference data (shared across all orgs). Contains rate, effective dates, F5 box mapping.

**Key fields**: `code`, `description`, `rate` (NUMERIC 5,4), `is_input`, `is_output`, `is_claimable`, `is_reverse_charge`, `effective_from`, `effective_to`, `f5_supply_box`, `f5_purchase_box`, `f5_tax_box`, `display_order`.

**Model methods**:
- `@classmethod get_active_codes(date=None, is_input=None) → QuerySet` — Filters by active status and effective date range
- `@classmethod get_rate_for_code(code, date) → Decimal` — Looks up applicable rate for a given date

---

#### `apps/gst/models/gst_return.py`
**Purpose**: Maps to `gst.return`. Stores computed GST F5 return data with all 15 boxes.

**Key fields**: All 15 box fields as `DecimalField(max_digits=10, decimal_places=4)`, plus `status`, `computed_at`, `reviewed_by`, `filed_at`, `iras_confirmation`.

---

#### `apps/gst/models/threshold_snapshot.py`
**Purpose**: Maps to `gst.threshold_snapshot`. Monthly revenue snapshots for non-GST-registered businesses to monitor the S$1M threshold.

---

#### `apps/gst/services/gst_calculator.py`
**Purpose**: **THE FINANCIAL HEART OF THE SYSTEM.** Pure Python GST calculation engine using `Decimal` arithmetic. Mirrors the PostgreSQL `gst.calculate()` function exactly for consistency.

**This is the Python implementation already specified in the original blueprint** (Section 2.5.2). It will be refined here with additional features.

**Classes/Functions**:
- `GSTResult` — Frozen dataclass: `net_amount`, `gst_amount`, `gross_amount`, `tax_code`, `rate`
- `GSTCalculator.calculate(amount, tax_code, is_inclusive, rate_date) → GSTResult` — Core calculation
- `GSTCalculator.calculate_line(qty, unit_price, discount_pct, tax_code, is_inclusive, is_bcrs_deposit) → GSTResult` — Line-level. **If `is_bcrs_deposit=True`, GST is always 0 regardless of tax code**
- `GSTCalculator.sum_lines(results) → dict` — Sums multiple line results
- `GSTCalculator.validate_gst_consistency(org, document_lines) → list[str]` — Returns validation warnings (e.g., non-registered org using SR tax code)

**BCRS handling**:
```python
@classmethod
def calculate_line(cls, qty, unit_price, discount_pct, tax_code,
                   is_inclusive=False, is_bcrs_deposit=False) -> GSTResult:
    line_amount = (qty * unit_price * (Decimal('1') - discount_pct / Decimal('100'))
                  ).quantize(MONEY_PLACES, ROUND_HALF_UP)

    if is_bcrs_deposit:
        # BCRS deposits are NOT subject to GST per IRAS
        return GSTResult(
            net_amount=line_amount,
            gst_amount=Decimal('0').quantize(MONEY_PLACES),
            gross_amount=line_amount,
            tax_code='OS',  # Override to out-of-scope
            rate=Decimal('0'),
        )

    return cls.calculate(line_amount, tax_code, is_inclusive)
```

---

#### `apps/gst/services/gst_return_service.py`
**Purpose**: GST F5 return lifecycle management.

**Functions**:
- `compute_return(org_id, period_start, period_end) → GSTReturn` — Calls `gst.compute_f5_return()` stored procedure. Returns a `GSTReturn` model instance in `COMPUTED` status
- `review_return(return_id, user_id) → GSTReturn` — Transitions to `REVIEWED` status
- `finalize_return(return_id, user_id) → GSTReturn` — Transitions to `FILED` status, records `filed_at` and `filed_by`
- `get_return_detail(return_id) → dict` — Returns F5 data formatted for the UI with box labels
- `get_return_pdf(return_id) → bytes` — Generates a printable GST F5 report PDF

---

#### `apps/gst/services/threshold_service.py`
**Purpose**: GST registration threshold monitoring for non-GST-registered businesses.

**Functions**:
- `compute_rolling_revenue(org_id, as_of_date) → Decimal` — Computes rolling 12-month taxable turnover from approved sales invoices
- `take_snapshot(org_id) → ThresholdSnapshot` — Records current revenue vs. S$1M threshold. Determines alert level:
  - `< 80%` → NONE
  - `80-89%` → WATCH
  - `90-99%` → WARNING
  - `≥ 100%` → CRITICAL
- `check_all_orgs() → None` — Celery periodic task: runs for all non-registered orgs monthly

---

#### `apps/gst/views/tax_code.py`
**Purpose**: Tax code reference data endpoints.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| GET | `/api/v1/{org_id}/gst/tax-codes/` | `TaxCodeListView` | Active tax codes (filtered by output/input) |
| GET | `/api/v1/{org_id}/gst/tax-codes/{code}/` | `TaxCodeDetailView` | Tax code detail with rate history |

---

#### `apps/gst/views/calculation.py`
**Purpose**: GST calculation API endpoint for frontend preview.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| POST | `/api/v1/{org_id}/gst/calculate/` | `GSTCalculateView` | Calculate GST for a given amount + tax code |
| POST | `/api/v1/{org_id}/gst/calculate-lines/` | `GSTCalculateLinesView` | Calculate GST for multiple invoice lines |

---

### Phase 3 Checklist

```
□ TaxCode model maps to gst.tax_code with managed = False
□ GSTReturn model maps to gst.return with all 15 box fields
□ ThresholdSnapshot model maps to gst.threshold_snapshot
□ gst_calculator:
    □ calculate() uses Decimal with ROUND_HALF_UP
    □ calculate() handles GST-inclusive extraction (9/109 fraction)
    □ calculate() handles GST-exclusive addition
    □ calculate() returns 0 GST for ZR, ES, OS tax codes
    □ calculate_line() handles quantity × price × discount
    □ calculate_line() returns 0 GST for is_bcrs_deposit=True
    □ sum_lines() sums 4dp internal values, then rounds to 2dp
    □ validate_gst_consistency() warns on non-registered org using SR
    □ All calculations match PostgreSQL gst.calculate() output exactly
□ gst_return_service:
    □ compute_return calls gst.compute_f5_return() stored proc
    □ Status transitions enforced: DRAFT→COMPUTED→REVIEWED→FILED
    □ Cannot file a return without review
□ threshold_service:
    □ compute_rolling_revenue aggregates correctly
    □ Alert levels: NONE < 80%, WATCH 80-89%, WARNING 90-99%, CRITICAL ≥100%
    □ take_snapshot creates ThresholdSnapshot record
□ Tests:
    □ test_gst_calculator: 30+ test cases covering:
        □ Standard-rated 9% exclusive
        □ Standard-rated 9% inclusive (9/109 extraction)
        □ Zero-rated (0% output)
        □ Exempt supply
        □ Out-of-scope
        □ Blocked input tax
        □ Reverse charge
        □ BCRS deposit override
        □ Edge: zero amount
        □ Edge: large amount (near NUMERIC(10,4) max)
        □ Edge: 100% discount
        □ Historical rate (8%) for dates in 2023
        □ Historical rate (7%) for dates before 2023
    □ test_threshold_service: rolling revenue computation
    □ test_views: calculate endpoint returns correct JSON
    □ All tests pass
□ URL routes mounted under /api/v1/{org_id}/gst/
```

---

## Phase 4: Journal Module — General Ledger

### Objective
Implement the immutable double-entry general ledger: journal entry creation with balance validation, reversal entries, GL queries by account and period. After this phase: manual journal entries can be posted, balanced at the database level, and queried for reporting.

### Dependencies
Phase 2 (COA — for Account references), Phase 3 (GST — for tax code references on lines)

### Files to Create

```
apps/accounting/models/
│   (add to existing accounting app)
├── journal_entry.py
└── journal_line.py

apps/accounting/serializers/
├── journal.py                        (add)

apps/accounting/services/
├── journal_service.py                (add)

apps/accounting/views/
├── journal.py                        (add)

apps/accounting/tests/
├── test_journal_service.py           (add)
├── test_journal_views.py             (add)
```

### File Specifications

---

#### `apps/accounting/models/journal_entry.py`
**Purpose**: Maps to `journal.entry`. Immutable header for journal entries. Inherits `ImmutableModel` to block Python-level updates.

**Key fields**: `org`, `entry_number`, `entry_date`, `source_type`, `source_id`, `reference`, `narration`, `fiscal_year`, `fiscal_period`, `is_reversed`, `reversed_by`, `reversal_of`, `posted_at`, `posted_by`.

**Design**: Overrides `save()` to ONLY allow initial creation. Updates are blocked except for `is_reversed` and `reversed_by_id` fields (matching the database trigger).

```python
class JournalEntry(ImmutableModel):
    MUTABLE_FIELDS = {'is_reversed', 'reversed_by_id'}

    def save(self, **kwargs):
        if self.pk and not kwargs.get('update_fields'):
            raise ImmutabilityError("Journal entries are immutable. Create a reversal.")
        if kwargs.get('update_fields'):
            illegal = set(kwargs['update_fields']) - self.MUTABLE_FIELDS
            if illegal:
                raise ImmutabilityError(f"Cannot modify fields: {illegal}")
        super().save(**kwargs)
```

---

#### `apps/accounting/models/journal_line.py`
**Purpose**: Maps to `journal.line`. Individual debit/credit lines. Fully immutable (no updates, no deletes at application level — database trigger enforces this too).

**Key fields**: `entry`, `org`, `line_number`, `account`, `description`, `debit`, `credit`, `tax_code`, `tax_amount`, `currency`, `exchange_rate`, `base_debit`, `base_credit`.

---

#### `apps/accounting/services/journal_service.py`
**Purpose**: Journal entry creation, reversal, and querying.

**Functions**:
- `create_manual_entry(org_id, entry_date, narration, lines, reference, user_id) → JournalEntry` — Creates a journal entry header + lines in a single atomic operation.
  1. Validates `entry_date` falls in an open fiscal period
  2. Gets next entry number via `sequence_service.next_number()`
  3. Creates `JournalEntry` header
  4. Creates all `JournalLine` rows
  5. Validates balance (Python-level check before commit; DB trigger is the final safety net)
  6. Returns the complete entry with lines

- `create_system_entry(org_id, source_type, source_id, entry_date, narration, lines, user_id) → JournalEntry` — Same as manual but with `source_type` and `source_id` linking to an originating document (invoice, payment, etc.)

- `reverse_entry(entry_id, reversal_date, narration, user_id) → JournalEntry` — Creates a new entry with all debits/credits swapped. Updates original entry's `is_reversed=True` and `reversed_by_id`.

- `get_general_ledger(org_id, account_id, start_date, end_date) → QuerySet` — Returns journal lines for an account within a date range, ordered by date.

- `get_entry_detail(entry_id) → JournalEntry` — Entry with all lines prefetched.

- `validate_lines_balance(lines) → None` — Raises `UnbalancedEntryError` if sum of base_debit ≠ sum of base_credit.

**Line creation helper**:
```python
def _create_lines(self, entry: JournalEntry, lines_data: list[dict]) -> list[JournalLine]:
    """
    Creates journal lines from a list of dicts.
    Each dict: {account_id, description, debit, credit, tax_code_id, currency, exchange_rate}

    Converts transaction-currency amounts to base-currency amounts:
        base_debit  = debit  × exchange_rate (if currency != SGD)
        base_credit = credit × exchange_rate
    """
    journal_lines = []
    for i, line_data in enumerate(lines_data, 1):
        rate = line_data.get('exchange_rate', Decimal('1'))
        journal_lines.append(JournalLine(
            entry=entry,
            org_id=entry.org_id,
            line_number=i,
            account_id=line_data['account_id'],
            description=line_data.get('description', ''),
            debit=money(line_data.get('debit', 0)),
            credit=money(line_data.get('credit', 0)),
            tax_code_id=line_data.get('tax_code_id'),
            tax_amount=money(line_data.get('tax_amount', 0)),
            currency=line_data.get('currency', 'SGD'),
            exchange_rate=rate,
            base_debit=money(line_data.get('debit', 0)) * rate,
            base_credit=money(line_data.get('credit', 0)) * rate,
        ))
    JournalLine.objects.bulk_create(journal_lines)
    return journal_lines
```

---

#### `apps/accounting/views/journal.py`
**Purpose**: Journal entry endpoints.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| GET | `/api/v1/{org_id}/journal-entries/` | `JournalEntryListView` | Paginated list (filterable by date, source_type, account) |
| POST | `/api/v1/{org_id}/journal-entries/` | `JournalEntryCreateView` | Create manual journal entry |
| GET | `/api/v1/{org_id}/journal-entries/{id}/` | `JournalEntryDetailView` | Entry detail with all lines |
| POST | `/api/v1/{org_id}/journal-entries/{id}/reverse/` | `JournalEntryReverseView` | Create reversal entry |
| GET | `/api/v1/{org_id}/general-ledger/` | `GeneralLedgerView` | Ledger view by account + period |

---

### Phase 4 Checklist

```
□ JournalEntry model maps to journal.entry with managed = False
□ JournalLine model maps to journal.line with managed = False
□ JournalEntry.save() blocks updates (ImmutableModel pattern)
□ JournalLine.save() blocks updates and deletes
□ journal_service:
    □ create_manual_entry validates posting date against open fiscal period
    □ create_manual_entry gets sequential entry_number via sequence service
    □ create_manual_entry validates balance before commit
    □ create_system_entry accepts source_type + source_id
    □ reverse_entry creates swapped debit/credit entry
    □ reverse_entry updates original is_reversed + reversed_by_id
    □ Multi-currency lines: base_debit/base_credit computed from exchange_rate
    □ Deferred constraint trigger validates balance at commit time
□ Views:
    □ Manual journal entry creation (multi-line request body)
    □ Entry detail returns all lines with account names
    □ Reversal endpoint creates new entry + updates original
    □ General ledger view supports account + date range filters
□ Serializers:
    □ JournalEntrySerializer with nested JournalLineSerializer
    □ Write serializer validates: at least 2 lines, no zero entries
    □ Read serializer includes account name, tax code description
□ Tests:
    □ test_journal_service: balanced entry creation
    □ test_journal_service: unbalanced entry raises error
    □ test_journal_service: reversal creates correct opposite entry
    □ test_journal_service: closed period rejects posting
    □ test_journal_service: immutability — cannot update posted entry
    □ test_journal_service: multi-currency base conversion
    □ test_journal_views: API-level CRUD
    □ All tests pass
□ URL routes mounted under /api/v1/{org_id}/journal-entries/
```

---

## Phase 5: Invoicing Module — Contacts, Documents, Lines

### Objective
Implement the complete invoicing lifecycle: contact management, sales/purchase invoice creation with line-level GST, document approval (which auto-creates journal entries), credit/debit notes, voiding, PDF generation, document status tracking. This is the **largest and most complex phase**. After this phase: a user can create a sales invoice with multiple line items, each with GST calculated, approve it (triggering a journal entry), generate a PDF, and track payment status.

### Dependencies
Phase 1 (Core), Phase 2 (COA), Phase 3 (GST), Phase 4 (Journal)

### Files to Create

```
apps/invoicing/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── contact.py
│   ├── document.py
│   ├── document_line.py
│   └── document_attachment.py
├── serializers/
│   ├── __init__.py
│   ├── contact.py
│   ├── document.py
│   ├── document_line.py
│   └── document_write.py
├── services/
│   ├── __init__.py
│   ├── contact_service.py
│   ├── invoice_service.py
│   ├── document_lifecycle.py
│   ├── journal_posting.py
│   ├── pdf_generator.py
│   └── numbering.py
├── filters.py
├── urls.py
├── views/
│   ├── __init__.py
│   ├── contact.py
│   └── document.py
├── templates/
│   └── invoicing/
│       ├── tax_invoice.html
│       ├── plain_invoice.html
│       └── credit_note.html
└── tests/
    ├── __init__.py
    ├── factories.py
    ├── test_contact_service.py
    ├── test_invoice_service.py
    ├── test_document_lifecycle.py
    ├── test_journal_posting.py
    ├── test_pdf_generator.py
    └── test_views.py
```

### File Specifications

---

#### `apps/invoicing/models/contact.py`
**Purpose**: Maps to `invoicing.contact`. Customers and suppliers with financial defaults.

**Key fields**: `org`, `contact_type` (CUSTOMER/SUPPLIER/BOTH), `name`, `legal_name`, `uen`, `gst_reg_number`, `is_gst_registered`, `tax_code_default`, email/phone/address, `default_currency`, `payment_terms_days`, `credit_limit`, `receivable_account`, `payable_account`, `peppol_id`, `peppol_scheme_id`.

---

#### `apps/invoicing/models/document.py`
**Purpose**: Maps to `invoicing.document`. Unified model for all document types (sales invoice, purchase invoice, credit note, debit note, PO, quote).

**Key fields**: `org`, `document_type` (ENUM), `document_number`, `document_date`, `due_date`, `contact`, `currency`, `exchange_rate`, `subtotal`, `total_discount`, `total_gst`, `total_amount`, `amount_paid`, `amount_due` (GENERATED), `base_subtotal`, `base_total_gst`, `base_total_amount`, `status` (ENUM), `reference`, `internal_notes`, `customer_notes`, `is_tax_invoice`, `tax_invoice_label`, `peppol_message_id`, `invoicenow_status`, `journal_entry`, `related_document`, `approved_at`, `approved_by`, `voided_at`, `voided_by`, `void_reason`.

**Design note on `amount_due`**: This is now a GENERATED ALWAYS AS column in the schema (Patch Fix 5). In Django, map it as a regular `DecimalField` but mark it as non-editable:
```python
amount_due = models.DecimalField(
    max_digits=10, decimal_places=4,
    editable=False,
    help_text='Generated column: total_amount - amount_paid'
)
```

---

#### `apps/invoicing/models/document_line.py`
**Purpose**: Maps to `invoicing.document_line`. Line items with per-line GST computation.

**Key fields**: `document`, `org`, `line_number`, `description`, `account`, `quantity`, `unit_of_measure`, `unit_price`, `discount_pct`, `discount_amount`, `tax_code`, `tax_rate` (snapshot), `is_tax_inclusive`, `is_bcrs_deposit`, `line_amount`, `gst_amount`, `total_amount`, `base_line_amount`, `base_gst_amount`, `base_total_amount`, `item_id`, `item_code`.

---

#### `apps/invoicing/models/document_attachment.py`
**Purpose**: Maps to `invoicing.document_attachment`. File references stored in S3/MinIO.

---

#### `apps/invoicing/services/invoice_service.py`
**Purpose**: Core invoice CRUD operations.

**Functions**:
- `create_draft(org_id, document_type, data) → Document` — Creates a DRAFT document with lines. For each line:
  1. Looks up tax code + rate
  2. Calls `GSTCalculator.calculate_line()` (with `is_bcrs_deposit` flag)
  3. Snapshots the tax rate onto the line
  4. Computes base currency equivalents via exchange rate
  5. Sums all lines to compute document totals (subtotal, total_gst, total_amount)
- `update_draft(document_id, data) → Document` — Recalculates all lines and totals. Only allowed in DRAFT status.
- `add_line(document_id, line_data) → DocumentLine` — Add a line to a DRAFT document
- `remove_line(document_id, line_id) → None` — Remove a line, recalculate totals
- `recalculate_totals(document_id) → Document` — Recomputes all computed fields from lines
- `determine_tax_invoice_label(org, document_type) → str` — Returns `'Tax Invoice'` if GST-registered, else `'Invoice'`

---

#### `apps/invoicing/services/document_lifecycle.py`
**Purpose**: Document status transitions — the state machine from the blueprint.

**Functions**:
- `approve(document_id, user_id) → Document` — Transitions DRAFT → APPROVED.
  1. Validates: document has at least one line, all fields complete
  2. Freezes the document (no further edits)
  3. Calls `journal_posting.post_invoice()` to create the journal entry
  4. Sets `approved_at`, `approved_by`
  5. If org has `invoicenow_enabled`, queues Peppol transmission via Celery

- `send(document_id) → Document` — Transitions APPROVED → SENT (marks as emailed/delivered)

- `void(document_id, reason, user_id) → Document` — Transitions any approved state → VOID.
  1. Creates a reversal journal entry via `journal_service.reverse_entry()`
  2. Sets `voided_at`, `voided_by`, `void_reason`
  3. The original journal entry is marked as reversed

- `mark_overdue() → int` — Celery periodic task: finds all approved/sent/partially-paid documents past `due_date` and transitions to OVERDUE

- `validate_transition(document, target_status) → None` — Enforces valid state transitions:
  ```
  DRAFT       → APPROVED
  APPROVED    → SENT, VOID
  SENT        → PARTIALLY_PAID, PAID, OVERDUE, VOID
  PARTIALLY_PAID → PAID, OVERDUE, VOID
  OVERDUE     → PARTIALLY_PAID, PAID, VOID
  ```

---

#### `apps/invoicing/services/journal_posting.py`
**Purpose**: Creates the double-entry journal entry when an invoice is approved.

**Functions**:
- `post_sales_invoice(document) → JournalEntry` — Creates journal:
  ```
  DR  Accounts Receivable (1200)      [total_amount]
      CR  Revenue Account (per line)   [line_amount per line]
      CR  GST Output Tax (2600)        [gst_amount per line]
  ```
  For multi-line invoices with different revenue accounts, each line gets its own credit entry.

- `post_purchase_invoice(document) → JournalEntry` — Creates journal:
  ```
  DR  Expense/COGS Account (per line)  [line_amount per line]
  DR  GST Input Tax (1600)             [gst_amount per line, if claimable]
      CR  Accounts Payable (2100)      [total_amount]
  ```
  For blocked input tax (`BL`, `TX-E`): GST amount is added to the expense, NOT debited to GST Input Tax.

- `post_credit_note(document) → JournalEntry` — Reversal of the original invoice posting pattern.

- `_build_journal_lines(document) → list[dict]` — Constructs the line list for journal_service, handling:
  - Line-level account assignment
  - BCRS deposit lines → debit/credit to Liability account (2650), NOT revenue
  - Multi-currency conversion
  - Tax code claimability

**BCRS posting logic**:
```python
for line in document.lines.all():
    if line.is_bcrs_deposit:
        # BCRS deposits are liabilities, not revenue
        journal_lines.append({
            'account_id': bcrs_liability_account_id,  # 2650
            'credit': line.line_amount,
            'description': f'BCRS deposit - {line.description}',
        })
    else:
        journal_lines.append({
            'account_id': line.account_id,
            'credit': line.line_amount,
            'description': line.description,
            'tax_code_id': line.tax_code_id,
            'tax_amount': line.gst_amount,
        })
```

---

#### `apps/invoicing/services/pdf_generator.py`
**Purpose**: Generates PDF invoices using WeasyPrint from HTML templates.

**Functions**:
- `generate_invoice_pdf(document_id) → bytes` — Renders the appropriate template (Tax Invoice vs. Invoice vs. Credit Note), returns PDF bytes
- `get_template_context(document) → dict` — Builds the full template context including: org details, contact details, line items with GST, totals, payment terms, bank details, PayNow QR code (if available)

**Template selection logic**:
- GST-registered org + sales invoice → `tax_invoice.html` (includes "Tax Invoice" label, GST reg number, GST breakdown)
- Non-GST-registered org + sales invoice → `plain_invoice.html` (no "Tax Invoice" label, no GST reg number, no separate GST line)
- Credit note → `credit_note.html`

---

#### `apps/invoicing/services/numbering.py`
**Purpose**: Invoice-specific numbering wrapper that delegates to `core.sequence_service`.

**Functions**:
- `get_next_invoice_number(org_id, document_type) → str` — Maps document type to sequence type and calls `sequence_service.next_number()`

---

#### `apps/invoicing/filters.py`
**Purpose**: Django-filter filterset classes for document queries.

**Classes**:
- `DocumentFilter` — Filters: `status`, `document_type`, `contact_id`, `date_from`, `date_to`, `amount_min`, `amount_max`, `overdue` (boolean), `search` (text search on number/reference/contact name)

---

#### `apps/invoicing/views/contact.py`
**Purpose**: Contact CRUD endpoints.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| GET | `/api/v1/{org_id}/contacts/` | `ContactListView` | List contacts (filterable by type, search) |
| POST | `/api/v1/{org_id}/contacts/` | `ContactCreateView` | Create contact |
| GET | `/api/v1/{org_id}/contacts/{id}/` | `ContactDetailView` | Contact detail with transaction history |
| PATCH | `/api/v1/{org_id}/contacts/{id}/` | `ContactDetailView` | Update contact |
| DELETE | `/api/v1/{org_id}/contacts/{id}/` | `ContactDetailView` | Deactivate contact |

---

#### `apps/invoicing/views/document.py`
**Purpose**: Invoice/document lifecycle endpoints.

**Endpoints**:
| Method | Path | View | Description |
|---|---|---|---|
| GET | `/api/v1/{org_id}/invoices/` | `InvoiceListView` | List all invoices (filterable) |
| POST | `/api/v1/{org_id}/invoices/` | `InvoiceCreateView` | Create draft invoice with lines |
| GET | `/api/v1/{org_id}/invoices/{id}/` | `InvoiceDetailView` | Full invoice detail |
| PATCH | `/api/v1/{org_id}/invoices/{id}/` | `InvoiceUpdateView` | Update draft invoice |
| POST | `/api/v1/{org_id}/invoices/{id}/approve/` | `InvoiceApproveView` | Approve → journal entry |
| POST | `/api/v1/{org_id}/invoices/{id}/void/` | `InvoiceVoidView` | Void → reversal entry |
| GET | `/api/v1/{org_id}/invoices/{id}/pdf/` | `InvoicePDFView` | Generate/download PDF |
| POST | `/api/v1/{org_id}/invoices/{id}/send/` | `InvoiceSendView` | Send via email |
| POST | `/api/v1/{org_id}/invoices/{id}/send-invoicenow/` | `InvoiceNowSendView` | Transmit via Peppol |
| GET | `/api/v1/{org_id}/purchases/` | `PurchaseListView` | List purchase invoices |
| POST | `/api/v1/{org_id}/purchases/` | `PurchaseCreateView` | Create purchase invoice |
| GET | `/api/v1/{org_id}/purchases/{id}/` | `PurchaseDetailView` | Purchase invoice detail |
| PATCH | `/api/v1/{org_id}/purchases/{id}/` | `PurchaseUpdateView` | Update draft purchase |
| POST | `/api/v1/{org_id}/purchases/{id}/approve/` | `PurchaseApproveView` | Approve purchase |
| POST | `/api/v1/{org_id}/credit-notes/` | `CreditNoteCreateView` | Create credit note linked to invoice |

---

### Phase 5 Checklist

```
□ Contact model maps to invoicing.contact with managed = False
□ Document model maps to invoicing.document with managed = False
□ Document model handles amount_due as generated column (non-editable)
□ DocumentLine model includes is_bcrs_deposit field
□ DocumentAttachment model maps to invoicing.document_attachment
□ contact_service:
    □ Create/update contacts with validation
    □ Deactivation checks no outstanding invoices
    □ Search with trigram matching
□ invoice_service:
    □ create_draft computes GST per line via GSTCalculator
    □ create_draft snapshots tax_rate on each line
    □ create_draft computes base currency equivalents
    □ create_draft sums line amounts to document totals
    □ update_draft recalculates all computed fields
    □ BCRS deposit lines get 0 GST regardless of tax code
    □ Non-GST-registered orgs default all lines to OS tax code
□ document_lifecycle:
    □ approve creates journal entry via journal_posting
    □ approve freezes document for editing
    □ approve queues InvoiceNow transmission if enabled
    □ void creates reversal journal entry
    □ void requires reason text
    □ State machine transitions enforced
    □ mark_overdue Celery task identifies past-due documents
□ journal_posting:
    □ post_sales_invoice creates correct DR AR / CR Revenue / CR GST Output
    □ post_purchase_invoice creates correct DR Expense / DR GST Input / CR AP
    □ Blocked input tax (BL, TX-E) absorbed into expense, not GST Input
    □ BCRS lines posted to BCRS Deposit Liability account
    □ Multi-line invoices create multi-line journal entries
    □ Multi-currency invoices convert to SGD base amounts
    □ Journal entry balances (validated by DB trigger)
□ pdf_generator:
    □ Tax Invoice template includes: GST reg number, "Tax Invoice" label, GST breakdown
    □ Plain Invoice template omits GST reg number and separate GST line
    □ Credit Note template references original invoice number
    □ PDF renders correctly via WeasyPrint
□ Views:
    □ All invoice CRUD endpoints functional
    □ All purchase CRUD endpoints functional
    □ Approve endpoint returns updated document with journal entry reference
    □ Void endpoint returns updated document with void reason
    □ PDF endpoint returns binary PDF response
    □ Pagination and filtering work correctly
□ Serializers:
    □ DocumentWriteSerializer handles nested line items
    □ DocumentReadSerializer includes computed totals, line details
    □ MoneyField used for all monetary fields
    □ Validates: at least one line for non-quote documents
□ Tests:
    □ factories.py: ContactFactory, DocumentFactory, DocumentLineFactory
    □ test_invoice_service: create draft, update, GST calculation accuracy
    □ test_document_lifecycle: full approve→send→pay→void lifecycle
    □ test_journal_posting: correct journal entries for all document types
    □ test_journal_posting: BCRS deposit posted to liability
    □ test_journal_posting: blocked input tax absorbed into expense
    □ test_pdf_generator: PDF generation (template rendering, not pixel-perfect)
    □ test_views: API-level document CRUD + lifecycle actions
    □ All tests pass
□ URL routes mounted under /api/v1/{org_id}/invoices/ and /purchases/
```

---

## Phase 6: Banking Module — Accounts, Payments, Reconciliation

### Objective
Implement bank account management, payment recording (received from customers, made to suppliers), payment-to-invoice allocation, FX gain/loss calculation on settlement, and bank statement import + reconciliation. After this phase: users can record payments against invoices, the AR/AP balances update, and bank transactions can be imported and matched.

### Dependencies
Phase 4 (Journal), Phase 5 (Invoicing)

### Files to Create

```
apps/banking/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── bank_account.py
│   ├── payment.py
│   ├── payment_allocation.py
│   └── bank_transaction.py
├── serializers/
│   ├── __init__.py
│   ├── bank_account.py
│   ├── payment.py
│   ├── allocation.py
│   └── bank_transaction.py
├── services/
│   ├── __init__.py
│   ├── bank_account_service.py
│   ├── payment_service.py
│   ├── allocation_service.py
│   ├── reconciliation_service.py
│   └── bank_import_service.py
├── filters.py
├── urls.py
├── views/
│   ├── __init__.py
│   ├── bank_account.py
│   ├── payment.py
│   └── reconciliation.py
└── tests/
    ├── __init__.py
    ├── factories.py
    ├── test_payment_service.py
    ├── test_allocation_service.py
    ├── test_reconciliation_service.py
    └── test_views.py
```

### Key Service Specifications

---

#### `apps/banking/services/payment_service.py`
**Functions**:
- `receive_payment(org_id, data) → Payment` — Records payment from customer. Creates journal:
  ```
  DR  Bank Account (1100)       [amount]
      CR  Accounts Receivable   [amount]
  ```
  If multi-currency: FX gain/loss computed and posted:
  ```
  DR  FX Gain/Loss (7500/8100)  [difference]
  ```

- `make_payment(org_id, data) → Payment` — Records payment to supplier. Creates journal:
  ```
  DR  Accounts Payable (2100)   [amount]
      CR  Bank Account (1100)   [amount]
  ```

- `void_payment(payment_id, user_id) → Payment` — Reverses the payment journal entry, deallocates from invoices.

---

#### `apps/banking/services/allocation_service.py`
**Functions**:
- `allocate_payment(payment_id, allocations) → list[PaymentAllocation]` — Distributes payment across multiple invoices. Updates each invoice's `amount_paid`. If `amount_paid == total_amount`, transitions document to `PAID` status.
- `validate_allocation(payment, allocations) → None` — Ensures total allocated ≤ payment amount.

---

#### `apps/banking/services/reconciliation_service.py`
**Functions**:
- `get_unreconciled_transactions(bank_account_id) → QuerySet` — Returns imported bank transactions not yet matched.
- `suggest_matches(transaction_id) → list[dict]` — Fuzzy matching: compares transaction amount/date/description against unreconciled payments and invoices. Scores potential matches.
- `reconcile(transaction_id, match_type, match_id) → BankTransaction` — Marks transaction as reconciled and links to payment or journal entry.
- `create_from_transaction(transaction_id, data) → Payment | JournalEntry` — Creates a new payment or journal entry from an unreconciled bank transaction.

---

#### API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/{org_id}/bank-accounts/` | List bank accounts |
| POST | `/{org_id}/bank-accounts/` | Create bank account |
| GET | `/{org_id}/bank-accounts/{id}/` | Bank account detail with balance |
| PATCH | `/{org_id}/bank-accounts/{id}/` | Update bank account |
| GET | `/{org_id}/payments/` | List payments (filterable) |
| POST | `/{org_id}/payments/receive/` | Receive payment from customer |
| POST | `/{org_id}/payments/make/` | Make payment to supplier |
| GET | `/{org_id}/payments/{id}/` | Payment detail with allocations |
| POST | `/{org_id}/payments/{id}/allocate/` | Allocate payment to invoices |
| POST | `/{org_id}/payments/{id}/void/` | Void payment |
| POST | `/{org_id}/bank-accounts/{id}/import/` | Import bank statement (CSV/OFX) |
| GET | `/{org_id}/bank-accounts/{id}/transactions/` | List imported transactions |
| POST | `/{org_id}/bank-transactions/{id}/reconcile/` | Reconcile transaction |
| GET | `/{org_id}/bank-transactions/{id}/suggest-matches/` | Get match suggestions |

---

### Phase 6 Checklist

```
□ BankAccount model maps to banking.bank_account with PayNow fields
□ Payment model maps to banking.payment with FX gain/loss field
□ PaymentAllocation model maps to banking.payment_allocation
□ BankTransaction model maps to banking.bank_transaction
□ payment_service:
    □ receive_payment creates correct journal entry (DR Bank, CR AR)
    □ make_payment creates correct journal entry (DR AP, CR Bank)
    □ Multi-currency: FX gain/loss computed at settlement rate
    □ void_payment reverses journal entry and deallocates
□ allocation_service:
    □ allocate_payment distributes across multiple invoices
    □ Updates invoice amount_paid (triggers generated amount_due column)
    □ Transitions invoice to PAID when fully allocated
    □ Validates total allocated ≤ payment amount
    □ Validates allocated ≤ invoice amount_due for each invoice
□ reconciliation_service:
    □ suggest_matches returns scored match candidates
    □ reconcile links transaction to payment or journal entry
    □ Import CSV bank statement
□ Tests:
    □ test_payment_service: receive, make, void, FX gain/loss
    □ test_allocation_service: single and split allocation
    □ test_allocation_service: partial payment doesn't mark as PAID
    □ test_allocation_service: full allocation marks as PAID
    □ test_reconciliation_service: match suggestion accuracy
    □ All tests pass
□ URL routes mounted under /api/v1/{org_id}/bank-accounts/, /payments/
```

---

## Phase 7: Peppol / InvoiceNow Module

### Objective
Implement PINT-SG XML generation, Peppol Access Point integration, InvoiceNow transmission workflow (async via Celery), transmission logging and retry, and incoming invoice reception. After this phase: approved sales invoices can be transmitted to IRAS via the InvoiceNow Peppol network.

### Dependencies
Phase 5 (Invoicing — for document data)

### Files to Create

```
apps/peppol/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   └── transmission_log.py
├── serializers/
│   ├── __init__.py
│   └── transmission.py
├── services/
│   ├── __init__.py
│   ├── pint_sg_builder.py
│   ├── access_point_client.py
│   ├── transmission_service.py
│   └── incoming_service.py
├── tasks.py
├── urls.py
├── views/
│   ├── __init__.py
│   ├── transmission.py
│   └── settings.py
├── schemas/
│   └── pint_sg_invoice.xsd
└── tests/
    ├── __init__.py
    ├── test_pint_sg_builder.py
    ├── test_transmission_service.py
    └── test_views.py
```

### Key Service Specifications

---

#### `apps/peppol/models/transmission_log.py`
**Purpose**: Maps to `gst.peppol_transmission_log` (created in Patch v1.0.1). Immutable log of every transmission attempt.

---

#### `apps/peppol/services/pint_sg_builder.py`
**Purpose**: Generates PINT-SG compliant UBL 2.1 XML from an approved `Document`. This is the refined version of the builder from the blueprint (Section 2.5.3), using `lxml` instead of `xml.etree` for better namespace handling and XSD validation.

**Functions**:
- `build_invoice_xml(document) → bytes` — Generates complete XML
- `validate_xml(xml_bytes) → list[str]` — Validates against PINT-SG XSD. Returns list of validation errors (empty if valid)

---

#### `apps/peppol/services/access_point_client.py`
**Purpose**: HTTP client for communicating with an IMDA-accredited Peppol Access Point.

**Functions**:
- `transmit(xml_bytes, sender_id, receiver_id) → TransmitResult` — Sends XML to AP. Returns status + message ID
- `check_status(message_id) → str` — Polls AP for delivery status
- `lookup_participant(peppol_id) → dict | None` — Queries Peppol SMP directory

---

#### `apps/peppol/services/transmission_service.py`
**Purpose**: Orchestrates the full InvoiceNow transmission workflow.

**Functions**:
- `queue_transmission(document_id) → None` — Enqueues Celery task
- `execute_transmission(document_id) → TransmissionLog` — The actual transmission:
  1. Build PINT-SG XML
  2. Validate XML
  3. Transmit via Access Point
  4. Log attempt in `gst.peppol_transmission_log`
  5. Update `invoicing.document.invoicenow_status`
  6. Retry on failure (max 3 attempts, exponential backoff)

---

#### `apps/peppol/tasks.py`
**Purpose**: Celery tasks for async Peppol operations.

**Tasks**:
- `transmit_invoice_task(document_id)` — Async execution of transmission_service.execute_transmission
- `check_delivery_status_task(log_id)` — Polls AP for delivery confirmation
- `process_incoming_invoice_task(xml_bytes)` — Parses incoming Peppol invoice and creates purchase invoice draft

---

#### API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/{org_id}/invoices/{id}/send-invoicenow/` | Trigger InvoiceNow transmission |
| GET | `/{org_id}/invoices/{id}/invoicenow-status/` | Get transmission status + log |
| GET | `/{org_id}/peppol/transmission-log/` | List all transmission logs |
| GET | `/{org_id}/peppol/settings/` | Peppol configuration |
| PATCH | `/{org_id}/peppol/settings/` | Update Peppol configuration |

---

### Phase 7 Checklist

```
□ TransmissionLog model maps to gst.peppol_transmission_log
□ pint_sg_builder:
    □ Generates valid UBL 2.1 XML
    □ Includes CustomizationID for PINT-SG
    □ Supplier party includes UEN (schemeID 0195) and GST reg number
    □ Customer party includes Peppol ID
    □ Tax totals with GST scheme ID
    □ All invoice lines with tax categories
    □ Handles zero-rated, exempt, and out-of-scope lines
    □ BCRS deposit lines excluded from tax totals
    □ XML validates against PINT-SG XSD
□ access_point_client:
    □ HTTP client with timeout and retry
    □ Authentication with AP credentials
    □ Error handling for network failures
□ transmission_service:
    □ Full workflow: build → validate → transmit → log → update status
    □ Retry logic: max 3 attempts with exponential backoff
    □ Failure creates TransmissionLog with error details
    □ Success updates document.invoicenow_status to TRANSMITTED
□ Celery tasks:
    □ transmit_invoice_task is idempotent (safe to retry)
    □ check_delivery_status_task polls and updates status
□ Tests:
    □ test_pint_sg_builder: XML generation for all document types
    □ test_pint_sg_builder: XML validation against XSD
    □ test_transmission_service: successful transmission flow
    □ test_transmission_service: failed transmission + retry
    □ test_transmission_service: mock AP client
    □ All tests pass
□ URL routes mounted under /api/v1/{org_id}/peppol/
```

---

## Phase 8: Reporting Module

### Objective
Implement financial reporting: Profit & Loss statement, Balance Sheet, Trial Balance, GST F5 return view, Aged Receivables/Payables, Dashboard KPIs. After this phase: users can generate all core financial reports for any period.

### Dependencies
Phase 4 (Journal — for GL data), Phase 5 (Invoicing — for document data), Phase 6 (Banking — for payment data)

### Files to Create

```
apps/reporting/
├── __init__.py
├── apps.py
├── services/
│   ├── __init__.py
│   ├── profit_loss.py
│   ├── balance_sheet.py
│   ├── trial_balance.py
│   ├── gst_report.py
│   ├── aging_report.py
│   └── dashboard.py
├── serializers/
│   ├── __init__.py
│   └── reports.py
├── urls.py
├── views/
│   ├── __init__.py
│   └── reports.py
└── tests/
    ├── __init__.py
    ├── test_profit_loss.py
    ├── test_balance_sheet.py
    ├── test_trial_balance.py
    ├── test_aging_report.py
    └── test_dashboard.py
```

### Key Service Specifications

---

#### `apps/reporting/services/profit_loss.py`
**Functions**:
- `generate(org_id, start_date, end_date, comparative=False) → dict` — P&L statement. Aggregates journal lines by account for Revenue (4000s), COGS (5000s), Expenses (6000s), Other Income (7000s), Other Expenses (8000s). If `comparative=True`, includes prior period for comparison.
- Returns: structured dict with sections, line items, subtotals, and net profit/loss.

---

#### `apps/reporting/services/balance_sheet.py`
**Functions**:
- `generate(org_id, as_of_date, comparative=False) → dict` — Balance Sheet. Aggregates journal lines by account for Assets (1000s), Liabilities (2000s), Equity (3000s). Computes current year earnings from P&L.
- Validates: Assets = Liabilities + Equity (accounting equation).

---

#### `apps/reporting/services/trial_balance.py`
**Functions**:
- `generate(org_id, as_of_date) → dict` — Trial Balance. All accounts with debit/credit balances. Total debits must equal total credits.

---

#### `apps/reporting/services/gst_report.py`
**Functions**:
- `get_return_list(org_id) → QuerySet` — List GST returns with status
- `get_return_detail(return_id) → dict` — Full F5 data with box labels and explanations
- `generate_f5_pdf(return_id) → bytes` — PDF formatted per IRAS F5 layout
- `get_tax_transaction_detail(org_id, period_start, period_end, box_number) → QuerySet` — Drill-down: shows individual transactions contributing to a specific F5 box

---

#### `apps/reporting/services/aging_report.py`
**Functions**:
- `aged_receivables(org_id, as_of_date) → dict` — AR aging: Current, 1-30 days, 31-60, 61-90, 90+ days. Grouped by contact.
- `aged_payables(org_id, as_of_date) → dict` — AP aging with same structure.

---

#### `apps/reporting/services/dashboard.py`
**Functions**:
- `get_kpis(org_id) → dict` — Dashboard metrics:
  - Total revenue (current month/quarter/year)
  - Total expenses
  - Net profit
  - GST payable (current quarter)
  - Outstanding receivables
  - Outstanding payables
  - Overdue invoice count + amount
  - Cash balance (bank accounts total)
  - GST threshold percentage (for non-registered orgs)

---

#### API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/{org_id}/reports/profit-loss/` | P&L (query: start_date, end_date) |
| GET | `/{org_id}/reports/balance-sheet/` | Balance Sheet (query: as_of_date) |
| GET | `/{org_id}/reports/trial-balance/` | Trial Balance (query: as_of_date) |
| GET | `/{org_id}/reports/aged-receivables/` | AR aging (query: as_of_date) |
| GET | `/{org_id}/reports/aged-payables/` | AP aging (query: as_of_date) |
| GET | `/{org_id}/gst/returns/` | List GST returns |
| POST | `/{org_id}/gst/returns/compute/` | Compute new return |
| GET | `/{org_id}/gst/returns/{id}/` | Return detail (F5 format) |
| POST | `/{org_id}/gst/returns/{id}/review/` | Mark as reviewed |
| POST | `/{org_id}/gst/returns/{id}/file/` | Mark as filed |
| GET | `/{org_id}/gst/returns/{id}/pdf/` | Download F5 PDF |
| GET | `/{org_id}/gst/returns/{id}/transactions/` | Drill-down transactions |
| GET | `/{org_id}/dashboard/` | Dashboard KPIs |

---

### Phase 8 Checklist

```
□ profit_loss:
    □ Aggregates journal lines by account type correctly
    □ Revenue - COGS = Gross Profit
    □ Gross Profit - Expenses + Other Income - Other Expenses = Net Profit
    □ Comparative mode shows prior period
    □ Respects fiscal period boundaries
□ balance_sheet:
    □ Assets = Liabilities + Equity (validates accounting equation)
    □ Current year earnings computed from P&L data
    □ Comparative mode
□ trial_balance:
    □ Total debits = Total credits (balanced)
    □ All accounts with non-zero balances included
□ gst_report:
    □ F5 return detail includes all 15 boxes with labels
    □ Drill-down shows individual transactions per box
    □ PDF generates per IRAS F5 layout
    □ Return status lifecycle: COMPUTED → REVIEWED → FILED
□ aging_report:
    □ Correct bucket calculation (Current, 1-30, 31-60, 61-90, 90+)
    □ Grouped by contact with subtotals
    □ Only includes outstanding (not fully paid) documents
□ dashboard:
    □ All KPIs computed correctly
    □ GST threshold percentage for non-registered orgs
    □ Response under 500ms for orgs with < 10,000 transactions
□ Tests:
    □ test_profit_loss: correct aggregation with known journal data
    □ test_balance_sheet: accounting equation holds
    □ test_trial_balance: balanced after posting test transactions
    □ test_aging_report: correct bucket assignment
    □ All tests pass
□ URL routes mounted under /api/v1/{org_id}/reports/ and /gst/
```

---

## Phase 9: Integration, Testing & Hardening

### Objective
End-to-end integration testing, performance optimisation, security hardening, API documentation, and deployment configuration. After this phase: the API is production-ready.

### Dependencies
All prior phases

### Files to Create/Update

```
apps/audit/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   └── event_log.py
├── serializers/
│   └── event_log.py
├── views/
│   └── audit_log.py
├── urls.py
└── tests/
    └── test_audit_log.py

tests/
├── integration/
│   ├── __init__.py
│   ├── test_invoice_lifecycle.py
│   ├── test_payment_allocation.py
│   ├── test_gst_return_computation.py
│   ├── test_peppol_transmission.py
│   ├── test_multi_currency.py
│   ├── test_multi_tenant_isolation.py
│   └── test_fiscal_period_controls.py
├── performance/
│   ├── test_gst_computation_load.py
│   └── test_report_generation_load.py
└── security/
    ├── test_rls_isolation.py
    ├── test_jwt_security.py
    └── test_permission_enforcement.py

docs/
├── api/
│   └── openapi.yaml
├── deployment/
│   ├── docker.md
│   └── aws.md
└── runbook/
    ├── gst_return_filing.md
    └── troubleshooting.md
```

### Key Test Specifications

---

#### `tests/integration/test_invoice_lifecycle.py`
**Covers**: Create draft → add lines → approve → journal entry created → send → receive payment → allocate → mark PAID. Full end-to-end.

---

#### `tests/integration/test_gst_return_computation.py`
**Covers**: Create multiple invoices with various tax codes → compute F5 return → validate all 15 boxes match expected values. Include BCRS deposit lines to verify exclusion.

---

#### `tests/integration/test_multi_tenant_isolation.py`
**Covers**: Two orgs created. Org A creates invoices. Org B cannot see Org A's data. Tests RLS enforcement at the database level.

---

#### `tests/security/test_rls_isolation.py`
**Covers**: Direct database queries with different `app.current_org_id` session variables return different data sets. Verifies RLS policies on all tenant-scoped tables.

---

#### Audit Log Views

| Method | Path | Description |
|---|---|---|
| GET | `/{org_id}/audit-log/` | Paginated audit log (uses `audit.org_event_log` view) |
| GET | `/{org_id}/audit-log/{entity_type}/{entity_id}/` | Audit history for specific entity |

---

### Phase 9 Checklist

```
□ Audit event_log model maps to audit.event_log (read-only from app)
□ Audit view endpoint uses audit.org_event_log (org-scoped view)
□ Integration tests:
    □ Full invoice lifecycle (draft → approve → pay → reconcile)
    □ GST F5 return computation matches expected box values
    □ Multi-currency invoice with FX gain/loss
    □ Peppol transmission (mocked AP)
    □ Credit note → reversal journal entry
    □ Multi-tenant isolation
    □ Fiscal period controls (reject posting to closed period)
□ Performance tests:
    □ GST computation for 1000 invoice lines < 2 seconds
    □ P&L report for org with 50,000 journal lines < 3 seconds
    □ Dashboard KPIs < 500ms
□ Security tests:
    □ RLS isolation: Org A cannot see Org B data
    □ JWT: expired token returns 401
    □ JWT: invalid token returns 401
    □ Permissions: Viewer cannot approve invoices
    □ Permissions: Bookkeeper cannot file GST
    □ Immutability: Cannot modify posted journal entry via API
    □ Audit: all financial mutations create audit.event_log entries
□ API documentation:
    □ OpenAPI 3.1 spec generated (drf-spectacular or manual)
    □ All endpoints documented with request/response examples
□ Deployment:
    □ Docker Compose with PostgreSQL 16 + Redis + Celery + API
    □ Gunicorn configuration with appropriate worker count
    □ Health check endpoint verifies DB + Redis connectivity
    □ Environment variable documentation (.env.example complete)
□ All tests pass (unit + integration + security)
□ Ruff lint: zero errors
□ Mypy typecheck: zero errors
□ Test coverage > 90% on services layer
```

---

## Consolidated File Inventory

| Phase | New Files | Modified Files | Total |
|---|---|---|---|
| Phase 0: Foundation | 28 | 0 | 28 |
| Phase 1: Core | 32 | 2 | 34 |
| Phase 2: COA | 12 | 0 | 12 |
| Phase 3: GST | 16 | 0 | 16 |
| Phase 4: Journal | 8 | 2 | 10 |
| Phase 5: Invoicing | 24 | 0 | 24 |
| Phase 6: Banking | 18 | 0 | 18 |
| Phase 7: Peppol | 14 | 1 | 15 |
| Phase 8: Reporting | 14 | 0 | 14 |
| Phase 9: Integration | 18 | 3 | 21 |
| **TOTAL** | **184** | **8** | **192** |

---

## Consolidated API Endpoint Summary

| Module | Endpoints | Auth Required | Org-Scoped |
|---|---|---|---|
| Auth | 7 | Partial | No |
| Organisation | 6 | Yes | Yes |
| Users (in org) | 4 | Yes | Yes |
| Fiscal Years | 5 | Yes | Yes |
| Exchange Rates | 3 | Yes | Yes |
| Accounts (COA) | 6 | Yes | Yes |
| GST Tax Codes | 2 | Yes | Yes |
| GST Calculation | 2 | Yes | Yes |
| GST Returns | 7 | Yes | Yes |
| Journal Entries | 5 | Yes | Yes |
| Contacts | 5 | Yes | Yes |
| Sales Invoices | 9 | Yes | Yes |
| Purchases | 5 | Yes | Yes |
| Credit Notes | 1 | Yes | Yes |
| Bank Accounts | 5 | Yes | Yes |
| Payments | 6 | Yes | Yes |
| Bank Transactions | 3 | Yes | Yes |
| Peppol | 5 | Yes | Yes |
| Reports | 7 | Yes | Yes |
| Dashboard | 1 | Yes | Yes |
| Audit Log | 2 | Yes | Yes |
| Health | 1 | No | No |
| **TOTAL** | **97** | | |

---

## Plan Self-Validation

I now critique my own plan against the requirements and identify any gaps or concerns.

### ✅ Validated: Schema Alignment

| Schema Table | Django Model | Phase | Status |
|---|---|---|---|
| `core.organisation` | `apps.core.models.Organisation` | 1 | ✅ |
| `core.app_user` | `apps.core.models.AppUser` | 1 | ✅ |
| `core.role` | `apps.core.models.Role` | 1 | ✅ |
| `core.user_organisation` | `apps.core.models.UserOrganisation` | 1 | ✅ |
| `core.fiscal_year` | `apps.core.models.FiscalYear` | 1 | ✅ |
| `core.fiscal_period` | `apps.core.models.FiscalPeriod` | 1 | ✅ |
| `core.currency` | `apps.core.models.Currency` | 1 | ✅ |
| `core.exchange_rate` | `apps.core.models.ExchangeRate` | 1 | ✅ |
| `core.document_sequence` | `apps.core.models.DocumentSequence` | 1 | ✅ |
| `core.organisation_setting` | `apps.core.models.OrganisationSetting` | 1 | ✅ |
| `coa.account_type` | `apps.accounting.models.AccountType` | 2 | ✅ |
| `coa.account_sub_type` | `apps.accounting.models.AccountSubType` | 2 | ✅ |
| `coa.account` | `apps.accounting.models.Account` | 2 | ✅ |
| `gst.tax_code` | `apps.gst.models.TaxCode` | 3 | ✅ |
| `gst.return` | `apps.gst.models.GSTReturn` | 3 | ✅ |
| `gst.threshold_snapshot` | `apps.gst.models.ThresholdSnapshot` | 3 | ✅ |
| `gst.peppol_transmission_log` | `apps.peppol.models.TransmissionLog` | 7 | ✅ |
| `journal.entry` | `apps.accounting.models.JournalEntry` | 4 | ✅ |
| `journal.line` | `apps.accounting.models.JournalLine` | 4 | ✅ |
| `invoicing.contact` | `apps.invoicing.models.Contact` | 5 | ✅ |
| `invoicing.document` | `apps.invoicing.models.Document` | 5 | ✅ |
| `invoicing.document_line` | `apps.invoicing.models.DocumentLine` | 5 | ✅ |
| `invoicing.document_attachment` | `apps.invoicing.models.DocumentAttachment` | 5 | ✅ |
| `banking.bank_account` | `apps.banking.models.BankAccount` | 6 | ✅ |
| `banking.payment` | `apps.banking.models.Payment` | 6 | ✅ |
| `banking.payment_allocation` | `apps.banking.models.PaymentAllocation` | 6 | ✅ |
| `banking.bank_transaction` | `apps.banking.models.BankTransaction` | 6 | ✅ |
| `audit.event_log` | `apps.audit.models.EventLog` | 9 | ✅ |

**28 schema tables → 28 Django models. Complete coverage.**

### ✅ Validated: Patch v1.0.1 Changes Addressed

| Patch Fix | Plan Coverage | Status |
|---|---|---|
| BCRS `is_bcrs_deposit` on `document_line` | DocumentLine model (Phase 5), GSTCalculator (Phase 3), journal_posting (Phase 5), F5 compute (Phase 8) | ✅ |
| `gst.calculate()` → STABLE | Python calculator is independent; no Python dependency on PG function volatility | ✅ |
| Journal balance trigger (deferred) | journal_service validates in Python; DB trigger is safety net | ✅ |
| `audit.org_event_log` view | Audit views use the org-scoped view (Phase 9) | ✅ |
| `amount_due` generated column | Document model maps as non-editable DecimalField (Phase 5) | ✅ |
| Peppol `transmission_log` | TransmissionLog model in Peppol module (Phase 7) | ✅ |
| Fiscal period `locked_at`/`locked_by` | FiscalPeriod model includes these fields (Phase 1) | ✅ |

### ⚠️ Self-Identified Concern: `managed = False` and Migrations

**Concern**: With `managed = False` on all models, Django's migration system won't create or alter any tables. The schema is entirely managed by our SQL script. This means:
1. `python manage.py migrate` will only create Django internal tables (auth, sessions, contenttypes, admin)
2. Any schema changes require updating the SQL script and running it manually (or via a migration framework like `pgmigrate` or `sqitch`)
3. Django's `inspectdb` command can generate initial model stubs, but they'll need manual refinement

**Mitigation**: This is by design. The SQL-first approach ensures fiscal integrity (constraints, triggers, stored procedures are in SQL, not Python). Document the migration workflow clearly: SQL changes go through a review process separate from Django migrations.

### ⚠️ Self-Identified Concern: `db_table` Quoting for Cross-Schema References

**Concern**: Django's `db_table` with schema-qualified names requires careful quoting. The format `'schema"."table'` works with PostgreSQL but can be fragile.

**Mitigation**: Set `search_path` in the database backend to include all LedgerSG schemas. Then use simple `db_table = 'table_name'` without schema prefix, relying on `search_path` resolution. This is simpler and more robust:
```python
# In database OPTIONS:
'OPTIONS': {'options': '-c search_path=core,coa,gst,journal,invoicing,banking,audit,public'}
```
With this approach, `db_table = 'organisation'` resolves to `core.organisation` because `core` is first in the search path. **However**, table names must be unique across all schemas — which they are in our design (no two schemas have a table with the same name).

### ⚠️ Self-Identified Concern: Celery Task Idempotency

**Concern**: The Peppol transmission task and payment allocation must be idempotent. If Celery retries a task (due to worker crash), the operation must not create duplicate journal entries or send duplicate InvoiceNow transmissions.

**Mitigation**: Each task checks for existing results before proceeding:
- `transmit_invoice_task`: checks `document.invoicenow_status` — if already TRANSMITTED, skip
- `receive_payment`: uses the payment_number as an idempotency key — if a payment with this number already exists, return it instead of creating a duplicate

### ✅ Validated: Decimal Precision Chain

```
PostgreSQL (NUMERIC(10,4)) ←→ Django (DecimalField(max_digits=10, decimal_places=4))
                                    ↕
                           Python (decimal.Decimal, ROUND_HALF_UP, 4dp)
                                    ↕
                           DRF API (MoneyField → string serialization "123.4500")
                                    ↕
                           Frontend (Decimal.js, ROUND_HALF_UP, 4dp)
```

No floating-point conversion anywhere in the chain. All monetary values are transmitted as strings in JSON.

### ✅ Validated: RLS Enforcement Chain

```
1. Request arrives → JWT authenticated → user_id known
2. URL parsed → org_id extracted from path
3. Tenant middleware:
   a. Verifies user_organisation membership
   b. SET LOCAL app.current_org_id = '{org_id}'
   c. SET LOCAL app.current_user_id = '{user_id}'
   d. contextvars set for Python-level access
4. View executes within ATOMIC transaction
5. Every Django ORM query → PostgreSQL → RLS policy evaluates:
   org_id = core.current_org_id()
6. Transaction commits → SET LOCAL variables expire
```

The RLS enforcement is not bypassable from the application layer as long as `ATOMIC_REQUESTS = True` and the middleware runs before every view.

### ✅ Validated: Stored Procedure Call Points

| Stored Procedure | Called From | Phase |
|---|---|---|
| `core.seed_default_chart_of_accounts()` | `organisation_service.create_organisation()` | 1 |
| `core.generate_fiscal_periods()` | `fiscal_service.create_fiscal_year()` | 1 |
| `core.next_document_number()` | `sequence_service.next_number()` | 1 |
| `gst.calculate()` | Not called from Python — Python uses its own `GSTCalculator` | 3 |
| `gst.calculate_line()` | Not called from Python — Python uses its own `GSTCalculator` | 3 |
| `gst.compute_f5_return()` | `gst_return_service.compute_return()` | 8 |
| `journal.validate_balance()` | Called by DB trigger; Python also validates pre-commit | 4 |

**Design note**: The GST calculation stored procedures exist for database-level use (e.g., ad-hoc SQL queries, reports). The Python `GSTCalculator` is the authoritative calculation engine for the application, ensuring identical logic runs in both layers but the application layer doesn't depend on PostgreSQL function calls for every invoice line.

---

## Execution Timeline Estimate

| Phase | Estimated Duration | Cumulative |
|---|---|---|
| Phase 0: Foundation | 1 week | Week 1 |
| Phase 1: Core | 2 weeks | Week 3 |
| Phase 2: COA | 1 week | Week 4 |
| Phase 3: GST | 1.5 weeks | Week 5-6 |
| Phase 4: Journal | 1.5 weeks | Week 7 |
| Phase 5: Invoicing | 3 weeks | Week 10 |
| Phase 6: Banking | 2 weeks | Week 12 |
| Phase 7: Peppol | 2 weeks | Week 14 |
| Phase 8: Reporting | 2 weeks | Week 16 |
| Phase 9: Integration | 2 weeks | Week 18 |
| **TOTAL** | **18 weeks** | |

Phase 5 (Invoicing) is the critical path — it is the largest phase with the most complex business logic (GST calculation per line, journal posting, lifecycle state machine, PDF generation). It should receive the most thorough review and testing attention.

---

**This plan is ready for execution.** Each phase is independently implementable, fully specified with file lists, features, interfaces, and checklists. Shall I proceed with Phase 0 implementation?
