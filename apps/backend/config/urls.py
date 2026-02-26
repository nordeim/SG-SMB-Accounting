"""
LedgerSG API URL Configuration.

Root URL configuration. Mounts API version namespace /api/v1/, 
health check endpoint, admin (development only).
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint.
    
    Returns:
        200 OK if database and services are healthy
        503 Service Unavailable if any dependency is down
    """
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0",
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }, status=503)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    """
    API root endpoint.
    
    Returns available API endpoints.
    """
    return JsonResponse({
        "name": "LedgerSG API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/v1/health/",
            "auth": "/api/v1/auth/",
            "organisations": "/api/v1/organisations/",
            "docs": "https://docs.ledgersg.sg/api",
        },
    })


# Org-scoped URLs - will be expanded as modules are built
org_scoped_urlpatterns = []

# Core module org-scoped URLs (org detail, gst, fiscal-years, summary)
try:
    from apps.core.urls import org_scoped_urlpatterns as core_org_urls
    # Include core org-scoped URLs at root of org_id path
    org_scoped_urlpatterns.append(path("", include(core_org_urls)))
except ImportError:
    pass

# Try to include app URLs if they exist
try:
    from apps.coa import urls as coa_urls
    org_scoped_urlpatterns.append(path("accounts/", include("apps.coa.urls")))
except ImportError:
    pass

try:
    org_scoped_urlpatterns.append(path("journal-entries/", include("apps.journal.urls")))
except ImportError:
    pass

try:
    org_scoped_urlpatterns.append(path("peppol/", include("apps.peppol.urls")))
except ImportError:
    pass

try:
    org_scoped_urlpatterns.append(path("reports/", include("apps.reporting.urls")))
except ImportError:
    pass

try:
    from apps.gst import urls as gst_urls
    org_scoped_urlpatterns.append(path("gst/", include("apps.gst.urls")))
except ImportError:
    pass

try:
    from apps.invoicing import urls as invoicing_urls
    org_scoped_urlpatterns.append(path("invoicing/", include("apps.invoicing.urls")))
except ImportError:
    pass


urlpatterns = [
    # Health check
    path("health/", health_check, name="health"),
    
    # API v1
    path("api/v1/", api_root, name="api-root"),
    path("api/v1/health/", health_check, name="api-health"),
    
    # Core module (auth + organisations)
    path("api/v1/", include("apps.core.urls")),
    
    # Org-scoped modules (handled by tenant middleware)
    path("api/v1/<uuid:org_id>/", include(org_scoped_urlpatterns)),
    
    # Admin (development only in production)
    path("admin/", admin.site.urls),
]
