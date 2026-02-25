# LedgerSG Backend API

Enterprise-grade accounting API for Singapore SMBs.

## Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL 16+
- Redis 7+
- Docker (optional)

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
# Edit .env with your settings
```

### Database Setup

```bash
# Start PostgreSQL and Redis (Docker)
docker-compose up -d db redis

# Or use local PostgreSQL/Redis

# Run the schema script (only once)
psql -U ledgersg -d ledgersg_dev < database_schema.sql
```

### Run Development Server

```bash
# Start API server
make dev

# Or with Docker
docker-compose up -d api
```

The API will be available at `http://localhost:8000`

## Development Commands

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Run linter
make lint

# Format code
make format

# Type checking
make typecheck

# Django shell
make shell

# Run migrations
make migrate
```

## Project Structure

```
apps/backend/
├── config/                 # Django configuration
│   ├── settings/          # base, dev, prod, test
│   ├── urls.py            # URL routing
│   ├── wsgi.py            # WSGI entry
│   └── celery.py          # Celery configuration
├── common/                # Shared utilities
│   ├── models.py          # Base model classes
│   ├── decimal_utils.py   # Financial precision utilities
│   ├── middleware/        # Tenant & audit middleware
│   ├── db/                # Custom DB backend
│   └── exceptions.py      # Custom exceptions
├── apps/                  # Business modules
│   ├── core/              # Auth, Org, Users, Fiscal
│   ├── coa/               # Chart of Accounts
│   ├── gst/               # GST tax codes & calculations
│   ├── journal/           # General Ledger
│   ├── invoicing/         # Contacts, Invoices
│   ├── banking/           # Bank accounts, payments
│   ├── peppol/            # InvoiceNow integration
│   └── reporting/         # Reports
└── database_schema.sql    # PostgreSQL schema v1.0.1
```

## Architecture

### Design Principles

1. **Unmanaged Models**: Django models use `managed = False` — schema is DDL-managed
2. **Service Layer**: Business logic in `services/`, thin views as controllers
3. **RLS Security**: Row-Level Security via PostgreSQL session variables
4. **Decimal Precision**: All money as `NUMERIC(10,4)` with `ROUND_HALF_UP`
5. **Atomic Requests**: Every view in single transaction for RLS

### Database Schema

- **core**: Organisation, users, roles, fiscal
- **coa**: Chart of Accounts
- **gst**: Tax codes, rates, F5 returns
- **journal**: General Ledger (immutable)
- **invoicing**: Contacts, invoices, documents
- **banking**: Bank accounts, payments
- **audit**: Immutable audit trail

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health/` | Health check |
| `POST /api/v1/auth/register/` | User registration |
| `POST /api/v1/auth/login/` | User login (JWT) |
| `GET /api/v1/organisations/` | List organisations |
| `GET /api/v1/{org_id}/invoices/` | List invoices |

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest apps/core/tests/test_auth.py

# Run with coverage
pytest --cov=apps --cov-report=html
```

## License

AGPL-3.0
