"""
Core URL configuration.

Routes for authentication (non-org-scoped) and organisation management.
"""

from django.urls import path, include

from apps.core.views.organisations import (
    OrganisationDetailView,
    GSTRegistrationView,
    FiscalYearListView,
    OrganisationSummaryView,
)


# Non-org-scoped URLs
urlpatterns = [
    path("auth/", include("apps.core.urls.auth")),
    path("organisations/", include("apps.core.urls.organisation")),
    path("users/", include("apps.core.urls.user")),
    path("fiscal/", include("apps.core.urls.fiscal")),
]

# Org-scoped URLs (mounted under api/v1/<uuid:org_id>/ in config/urls.py)
# DO NOT include org_id in these patterns - it's already in the URL prefix
org_scoped_urlpatterns = [
    # Organisation detail - mounted at api/v1/{org_id}/
    path("", OrganisationDetailView.as_view(), name="org-detail"),
    
    # GST registration - mounted at api/v1/{org_id}/gst/
    path("gst/", GSTRegistrationView.as_view(), name="org-gst"),
    
    # Fiscal years - mounted at api/v1/{org_id}/fiscal-years/
    path("fiscal-years/", FiscalYearListView.as_view(), name="org-fiscal-years"),
    
    # Organisation summary - mounted at api/v1/{org_id}/summary/
    path("summary/", OrganisationSummaryView.as_view(), name="org-summary"),
]
