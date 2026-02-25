# LedgerSG Backend — Current Status

## Overview

**Phase**: Phase 0 - Project Foundation (In Progress)

## Completed Components

### ✅ Configuration
| File | Status | Description |
|------|--------|-------------|
| `pyproject.toml` | ✅ | Dependencies, tool config (ruff, mypy, pytest) |
| `config/settings/base.py` | ✅ | Base settings with RLS, JWT, DB config |
| `config/settings/development.py` | ✅ | Dev overrides (debug, CORS) |
| `config/settings/production.py` | ✅ | Production hardening (HSTS, HTTPS) |
| `config/settings/testing.py` | ✅ | Test optimizations (fast passwords) |
| `config/urls.py` | ✅ | URL routing with health check |
| `config/wsgi.py` | ✅ | WSGI entry point |
| `config/asgi.py` | ✅ | ASGI entry point |
| `config/celery.py` | ✅ | Celery app factory |

### ✅ Common Utilities
| File | Status | Description |
|------|--------|-------------|
| `common/decimal_utils.py` | ✅ | Money precision (4dp), GST calc, Money class |
| `common/models.py` | ✅ | BaseModel, TenantModel, ImmutableModel |
| `common/exceptions.py` | ✅ | Custom exception hierarchy + DRF handler |
| `common/renderers.py` | ✅ | Decimal-safe JSON renderer |
| `common/pagination.py` | ✅ | Standard, Large, Cursor pagination |
| `common/middleware/tenant_context.py` | ✅ | **Critical**: RLS session variables |
| `common/middleware/audit_context.py` | ✅ | Request metadata capture |
| `common/db/backend/base.py` | ✅ | Custom PostgreSQL backend |
| `common/db/routers.py` | ✅ | Database router |

### ✅ Infrastructure
| File | Status | Description |
|------|--------|-------------|
| `docker-compose.yml` | ✅ | PostgreSQL 16, Redis, API, Celery |
| `Dockerfile` | ✅ | Production container |
| `Makefile` | ✅ | Dev commands (dev, test, lint, format) |
| `manage.py` | ✅ | Django management |
| `.env.example` | ✅ | Environment template |
| `README.md` | ✅ | Backend documentation |

## Phase 0 Progress

| Task | Status |
|------|--------|
| Project structure | ✅ 100% |
| Dependencies | ✅ 100% |
| Settings (base/dev/prod/test) | ✅ 100% |
| Decimal utilities | ✅ 100% |
| Base models | ✅ 100% |
| Middleware (tenant, audit) | ✅ 100% |
| Custom DB backend | ✅ 100% |
| Docker setup | ✅ 100% |
| Exceptions & handlers | ✅ 100% |
| Pagination & renderers | ✅ 100% |

## Next Steps (Phase 0 Completion)

1. Create `apps/core/` module (Phase 1 start)
2. Create test stubs for common utilities
3. Set up pre-commit hooks
4. Verify `python manage.py check` passes
5. Run database schema

## Phase 1 Preview (Core Module)

| Component | Files |
|-----------|-------|
| Models | `organisation.py`, `app_user.py`, `role.py`, `user_organisation.py` |
| Services | `auth_service.py`, `organisation_service.py` |
| Views | `auth.py`, `organisation.py` |
| Tests | `test_auth.py`, `test_organisation.py` |

---

**Updated**: 2026-02-24  
**Status**: Phase 0 Foundation - Core Infrastructure Complete
