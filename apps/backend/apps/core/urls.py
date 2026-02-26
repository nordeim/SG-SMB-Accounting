"""
URL configuration for core app.

Routes for authentication (non-org-scoped) and organisation management.
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
    path("auth/me/", me_view, name="auth-me"),
    path("auth/profile/", me_view, name="auth-profile"),  # Alias for compatibility
    path("auth/change-password/", change_password_view, name="auth-change-password"),
    path("auth/organisations/", my_organisations_view, name="auth-organisations"),
]

# Non-org-scoped organisation management
org_urlpatterns = [
    path("organisations/", OrganisationListCreateView.as_view(), name="org-list-create"),
]

# Org-scoped URLs (mounted under api/v1/<uuid:org_id>/ in config/urls.py)
# DO NOT include org_id in these patterns - it's already in the URL prefix
org_detail_urlpatterns = [
    # Organisation detail - mounted at api/v1/{org_id}/
    path("", OrganisationDetailView.as_view(), name="org-detail"),
    
    # GST registration - mounted at api/v1/{org_id}/gst/
    path("gst/", GSTRegistrationView.as_view(), name="org-gst"),
    
    # Fiscal years - mounted at api/v1/{org_id}/fiscal-years/
    path("fiscal-years/", FiscalYearListView.as_view(), name="org-fiscal-years"),
    
    # Organisation summary - mounted at api/v1/{org_id}/summary/
    path("summary/", OrganisationSummaryView.as_view(), name="org-summary"),
]

# Export all URL patterns for non-org-scoped URLs
urlpatterns = auth_urlpatterns + org_urlpatterns

# Export org-scoped patterns separately for config/urls.py
org_scoped_urlpatterns = org_detail_urlpatterns
