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


urlpatterns = [
    # Health check
    path("health/", health_check, name="health"),
    
    # API v1
    path("api/v1/", api_root, name="api-root"),
    path("api/v1/health/", health_check, name="api-health"),
    
    # Auth module
    path("api/v1/auth/", include("apps.core.urls.auth")),
    
    # Organisation module (non-org-scoped)
    path("api/v1/organisations/", include("apps.core.urls.organisation")),
    
    # Org-scoped modules (handled by tenant middleware)
    path("api/v1/<uuid:org_id>/", include([
        # Core
        path("users/", include("apps.core.urls.user")),
        path("fiscal/", include("apps.core.urls.fiscal")),
        path("settings/", include("apps.core.urls.settings")),
        
        # COA
        path("accounts/", include("apps.coa.urls")),
        
        # GST
        path("tax-codes/", include("apps.gst.urls.tax_code")),
        path("gst-returns/", include("apps.gst.urls.return")),
        
        # Journal
        path("journal-entries/", include("apps.journal.urls")),
        
        # Invoicing
        path("contacts/", include("apps.invoicing.urls.contact")),
        path("invoices/", include("apps.invoicing.urls.document")),
        path("quotes/", include("apps.invoicing.urls.quote")),
        
        # Banking
        path("bank-accounts/", include("apps.banking.urls.account")),
        path("payments/", include("apps.banking.urls.payment")),
        
        # Peppol
        path("peppol/", include("apps.peppol.urls")),
        
        # Reporting
        path("reports/", include("apps.reporting.urls")),
    ])),
    
    # Admin (development only in production)
    path("admin/", admin.site.urls),
]
