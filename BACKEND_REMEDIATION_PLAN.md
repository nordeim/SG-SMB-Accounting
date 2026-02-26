# LedgerSG Backend API Remediation Plan

## Executive Summary

Based on comprehensive codebase audit, the backend has **53 implemented endpoints** but has critical routing issues preventing tests from passing. This plan outlines the fixes needed to achieve full test compliance.

---

## Critical Issues Identified

### Issue 1: URL Routing Mismatch (Blocking)
**Problem:** 
- `apps/core/urls.py` uses `<str:org_id>/` prefix for org-scoped URLs
- `config/urls.py` already prefixes with `<uuid:org_id>/`
- Result: Double org_id in URL path `/api/v1/{org_id}/{org_id}/`

**Fix Required:**
- Remove `<str:org_id>/` prefix from `apps/core/urls.py` org-scoped patterns
- The org_id is already provided by `config/urls.py`

### Issue 2: View Type Mismatch (Blocking)
**Problem:**
- `apps/core/views/auth.py` uses function-based views (`@api_view` decorator)
- `apps/core/urls.py` tries to call `.as_view()` on them (for class-based views)

**Fix Required:**
- Remove `.as_view()` from function-based view references
- Or convert function views to class-based views

### Issue 3: Missing URL Pattern for `/auth/me/`
**Problem:**
- Tests use `/api/v1/auth/me/` for profile
- URL config has `/api/v1/auth/profile/`

**Fix Required:**
- Add `path("auth/me/", ...)` alias or change test

---

## Implementation Phases

### Phase 4: Fix URL Routing Issues (Critical)
**Files to Modify:**
1. `apps/core/urls.py` - Fix view references and org-scoped prefixes
2. Test file endpoint references if needed

**Changes:**
```python
# apps/core/urls.py
# Change from:
path("<str:org_id>/", OrganisationDetailView.as_view(), ...)
# To:
path("", OrganisationDetailView.as_view(), ...)  # org_id already in prefix

# Change from:
path("auth/register/", RegisterView.as_view(), ...)
# To:
path("auth/register/", register_view, ...)  # function view, no .as_view()
```

### Phase 5: Core Module Fixes
**Current State:** 14 endpoints defined, 6 working in tests

**Working:**
- Auth endpoints (register, login, logout, refresh, change-password)

**Broken/Missing:**
1. `/api/v1/auth/me/` - GET/PATCH profile (currently at `/auth/profile/`)
2. `/api/v1/organisations/` - GET/POST (exists but routing broken)
3. `/api/v1/{org_id}/` - GET/PATCH/DELETE organisation detail
4. `/api/v1/{org_id}/fiscal-years/` - GET fiscal years
5. `/api/v1/{org_id}/summary/` - GET dashboard summary

**Implementation Notes:**
- Views exist in `apps/core/views/organisations.py`
- Serializers exist
- Services exist
- Just need URL routing fixes

### Phase 6: COA Module Fixes
**Current State:** 8 endpoints defined in `apps/coa/urls.py`

**Expected by Tests:**
1. GET `/api/v1/{org_id}/accounts/` - List accounts
2. POST `/api/v1/{org_id}/accounts/` - Create account
3. GET `/api/v1/{org_id}/accounts/search/?q=` - Search accounts
4. GET `/api/v1/{org_id}/accounts/types/` - Account types
5. GET `/api/v1/{org_id}/accounts/hierarchy/` - Account hierarchy
6. GET `/api/v1/{org_id}/accounts/trial-balance/` - Trial balance

**Status:** Views exist, URLs configured, but getting 403 errors
**Root Cause:** Permission/RLS issues - org context not set

### Phase 7: GST Module Fixes
**Current State:** 11 endpoints defined

**Expected by Tests:**
1. GET `/api/v1/{org_id}/gst/tax-codes/` - List tax codes ✓ (working)
2. GET `/api/v1/{org_id}/gst/tax-codes/iras-info/` - IRAS info ✓ (working)
3. POST `/api/v1/{org_id}/gst/calculate/` - Calculate GST
4. POST `/api/v1/{org_id}/gst/calculate/document/` - Calculate doc GST
5. GET `/api/v1/{org_id}/gst/returns/` - List returns
6. GET `/api/v1/{org_id}/gst/returns/deadlines/` - GST deadlines

**Status:** Views exist, URLs configured, getting 404 errors
**Root Cause:** URL pattern mismatch in routing

### Phase 8: Invoicing Module Fixes
**Current State:** 12 endpoints defined

**Expected by Tests:**
1. GET `/api/v1/{org_id}/invoicing/contacts/` - List contacts
2. POST `/api/v1/{org_id}/invoicing/contacts/` - Create contact
3. GET `/api/v1/{org_id}/invoicing/documents/` - List documents
4. GET `/api/v1/{org_id}/invoicing/documents/summary/` - Doc summary
5. GET `/api/v1/{org_id}/invoicing/documents/status-transitions/` - Transitions

**Status:** Views exist, URLs configured, getting 404 errors
**Root Cause:** URL pattern mismatch

### Phase 9: Journal Module Fixes
**Current State:** 8 endpoints defined

**Expected by Tests:**
1. GET `/api/v1/{org_id}/journal-entries/entries/` - List entries
2. GET `/api/v1/{org_id}/journal-entries/entries/types/` - Entry types
3. POST `/api/v1/{org_id}/journal-entries/entries/validate/` - Validate
4. GET `/api/v1/{org_id}/journal-entries/trial-balance/` - Trial balance

**Status:** Views exist, URLs configured, getting 404 errors
**Root Cause:** URL pattern mismatch

---

## Detailed Fix Instructions

### Fix 1: Update apps/core/urls.py

```python
"""
URL configuration for core app.
"""
from django.urls import path

from apps.core.views.auth import (
    register_view,
    login_view,
    logout_view,
    refresh_view,
    me_view,
    change_password_view,
    my_organisations_view,
)

from apps.core.views.organisations import (
    OrganisationListCreateView,
    OrganisationDetailView,
    GSTRegistrationView,
    FiscalYearListView,
    OrganisationSummaryView,
)

app_name = "core"

# Non-org-scoped URLs (authentication)
auth_urlpatterns = [
    path("auth/register/", register_view, name="auth-register"),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/logout/", logout_view, name="auth-logout"),
    path("auth/refresh/", refresh_view, name="auth-refresh"),
    path("auth/me/", me_view, name="auth-me"),  # Changed from auth/profile/
    path("auth/profile/", me_view, name="auth-profile"),  # Keep alias
    path("auth/change-password/", change_password_view, name="auth-change-password"),
]

# Non-org-scoped organisation management
org_urlpatterns = [
    path("organisations/", OrganisationListCreateView.as_view(), name="org-list-create"),
]

# These are mounted under api/v1/<uuid:org_id>/ in config/urls.py
# So we DON'T prefix with org_id here
org_scoped_urlpatterns = [
    # Organisation details - mounted at api/v1/{org_id}/
    path("", OrganisationDetailView.as_view(), name="org-detail"),
    
    # GST registration - mounted at api/v1/{org_id}/gst/
    path("gst/", GSTRegistrationView.as_view(), name="org-gst"),
    
    # Fiscal years - mounted at api/v1/{org_id}/fiscal-years/
    path("fiscal-years/", FiscalYearListView.as_view(), name="org-fiscal-years"),
    
    # Organisation summary - mounted at api/v1/{org_id}/summary/
    path("summary/", OrganisationSummaryView.as_view(), name="org-summary"),
]

# Export all URL patterns
urlpatterns = auth_urlpatterns + org_urlpatterns + org_scoped_urlpatterns
```

### Fix 2: Update config/urls.py

The current config/urls.py is correct in its approach. The issue is in apps/core/urls.py.

### Fix 3: Ensure All App URLs Are Included

Verify all app URL modules are properly included:

```python
# config/urls.py org_scoped_urlpatterns
org_scoped_urlpatterns = [
    path("accounts/", include("apps.coa.urls")),
    path("journal-entries/", include("apps.journal.urls")),
    path("gst/", include("apps.gst.urls")),
    path("invoicing/", include("apps.invoicing.urls")),
    # banking, peppol, reporting are empty placeholders
]
```

Then in `apps/core/urls.py`, the org_scoped patterns should NOT have org_id prefix:
```python
org_scoped_urlpatterns = [
    path("", OrganisationDetailView.as_view(), name="org-detail"),
    path("gst/", GSTRegistrationView.as_view(), name="org-gst"),
    path("fiscal-years/", FiscalYearListView.as_view(), name="org-fiscal-years"),
    path("summary/", OrganisationSummaryView.as_view(), name="org-summary"),
]
```

### Fix 4: Fix COA 403 Errors

The 403 errors in COA module suggest permission issues. Check:
1. TenantContextMiddleware is setting org_id
2. RLS policies are correct
3. User has proper role permissions

---

## Test Validation Matrix

| Test Category | Current Status | After Phase 4 | After All Phases |
|--------------|----------------|---------------|------------------|
| Authentication | 9/9 passing | 9/9 | 9/9 |
| Health Check | 1/1 passing | 1/1 | 1/1 |
| Security | 2/3 passing | 2/3 | 3/3 |
| Organisation | 0/6 passing | 6/6 | 6/6 |
| Chart of Accounts | 0/6 passing | 0/6 | 6/6 |
| GST | 1/6 passing | 2/6 | 6/6 |
| Invoicing | 0/5 passing | 0/5 | 5/5 |
| Journal | 0/5 passing | 0/5 | 5/5 |
| **TOTAL** | **13/41** | **18/41** | **41/41** |

---

## Risk Assessment

### High Risk
- **Database Schema Mismatches**: If model fields don't match schema constraints
- **RLS Policy Issues**: May cause unexpected 403 errors

### Medium Risk
- **URL Pattern Conflicts**: Need careful testing of nested includes
- **Permission Logic**: Role-based access control needs validation

### Low Risk
- **Missing Optional Features**: Non-critical endpoints can be deferred

---

## Success Criteria

1. All 41 tests pass
2. No 404 errors for implemented endpoints
3. No 500 errors
4. Proper permission enforcement (403 where expected)
5. Response format matches test expectations
