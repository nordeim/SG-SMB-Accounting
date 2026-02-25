# LedgerSG Backend — Current Status

## Overview

**Phase**: Phase 1 - Core Module (In Progress)

## Completed Components

### ✅ Phase 0: Foundation (Complete)
| Component | Files | Status |
|-----------|-------|--------|
| Configuration | 9 settings files | ✅ 100% |
| Common Utils | decimal_utils, models, exceptions | ✅ 100% |
| Middleware | tenant_context, audit_context | ✅ 100% |
| DB Backend | custom PostgreSQL backend | ✅ 100% |
| Docker | docker-compose, Dockerfile | ✅ 100% |
| Tests | test_decimal_utils | ✅ 100% |

### 🚧 Phase 1: Core Module (In Progress)
| Component | Files | Status |
|-----------|-------|--------|
| Models | app_user, organisation, role, user_organisation, fiscal_year, fiscal_period | ✅ Complete |
| Serializers | auth serializers | ✅ Complete |
| Services | auth_service | ✅ Complete |
| Views | auth views | ✅ Complete |
| URLs | auth URLs | ✅ Complete |
| Organisation Service | Pending | 🚧 Next |
| Organisation Views | Pending | 🚧 Next |
| Permissions | Permission classes | 🚧 Pending |
| Tests | Core tests | 🚧 Pending |

### Phase 1 Files Created

```
apps/core/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── app_user.py          ✅ Custom user model
│   ├── organisation.py      ✅ Organisation model
│   ├── role.py              ✅ Role/permissions model
│   ├── user_organisation.py ✅ User-org join model
│   ├── fiscal_year.py       ✅ Fiscal year model
│   └── fiscal_period.py     ✅ Fiscal period model
├── serializers/
│   ├── __init__.py
│   └── auth.py              ✅ Auth serializers
├── services/
│   ├── __init__.py
│   └── auth_service.py      ✅ Auth service
├── views/
│   ├── __init__.py
│   └── auth.py              ✅ Auth views
├── tests/
│   └── __init__.py
└── urls/
    ├── __init__.py
    ├── auth.py              ✅ Auth URLs
    ├── organisation.py      ✅ Placeholder
    ├── user.py              ✅ Placeholder
    ├── fiscal.py            ✅ Placeholder
    └── settings.py          ✅ Placeholder
```

### Auth API Endpoints

| Method | Path | View | Status |
|--------|------|------|--------|
| POST | `/api/v1/auth/register/` | `register_view` | ✅ |
| POST | `/api/v1/auth/login/` | `login_view` | ✅ |
| POST | `/api/v1/auth/refresh/` | `refresh_view` | ✅ |
| POST | `/api/v1/auth/logout/` | `logout_view` | ✅ |
| GET | `/api/v1/auth/me/` | `me_view` | ✅ |
| PATCH | `/api/v1/auth/me/` | `me_view` | ✅ |
| POST | `/api/v1/auth/change-password/` | `change_password_view` | ✅ |
| GET | `/api/v1/auth/organisations/` | `my_organisations_view` | ✅ |

## Next Steps

### Complete Phase 1
1. Create organisation service (seed CoA, create sequences)
2. Create organisation views
3. Create permission classes (IsOrgMember, HasOrgPermission)
4. Create organisation tests
5. Create auth tests

### Phase 2-9
- Phase 2: COA Module
- Phase 3: GST Module
- Phase 4: Journal Module
- Phase 5: Invoicing Module
- Phase 6: Banking Module
- Phase 7: Peppol/InvoiceNow
- Phase 8: Reporting
- Phase 9: Integration & Testing

---

**Updated**: 2026-02-24  
**Status**: Phase 1 Core Module - Auth Complete, Organisation Pending
