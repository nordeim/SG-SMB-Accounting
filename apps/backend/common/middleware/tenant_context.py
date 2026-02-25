"""
Tenant Context Middleware

THE MOST CRITICAL MIDDLEWARE IN THE SYSTEM.

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
import uuid
from typing import Optional

from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.core.cache import cache

from common.exceptions import UnauthorizedOrgAccess


# Contextvars for application-layer access
_current_org_id: contextvars.ContextVar[Optional[uuid.UUID]] = contextvars.ContextVar(
    'current_org_id', default=None
)
_current_user_id: contextvars.ContextVar[Optional[uuid.UUID]] = contextvars.ContextVar(
    'current_user_id', default=None
)


def get_current_org_id() -> Optional[uuid.UUID]:
    """Get the current organization ID from context."""
    return _current_org_id.get()


def get_current_user_id() -> Optional[uuid.UUID]:
    """Get the current user ID from context."""
    return _current_user_id.get()


class TenantContextMiddleware:
    """
    Middleware that extracts org_id from URL and sets RLS session variables.
    
    Must be placed AFTER AuthenticationMiddleware in MIDDLEWARE list.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip for non-org-scoped URLs
        if not self._is_org_scoped(request.path):
            return self.get_response(request)
        
        # Skip for unauthenticated users (let view handle auth)
        if not request.user or not request.user.is_authenticated:
            return self.get_response(request)
        
        try:
            # Extract org_id from URL
            org_id = self._extract_org_id(request.path)
            
            if not org_id:
                # No org_id in URL, let view handle it
                return self.get_response(request)
            
            # Verify user belongs to this org
            if not self._verify_org_membership(request.user, org_id):
                return JsonResponse(
                    {
                        "error": {
                            "code": "unauthorized_org_access",
                            "message": "You do not have access to this organization",
                        }
                    },
                    status=403
                )
            
            # Get user's role for this org
            org_role = self._get_org_role(request.user, org_id)
            
            # Set RLS session variables within the atomic transaction
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET LOCAL app.current_org_id = %s",
                    [str(org_id)]
                )
                cursor.execute(
                    "SET LOCAL app.current_user_id = %s",
                    [str(request.user.id)]
                )
            
            # Set contextvars for application-level access
            _current_org_id.set(org_id)
            _current_user_id.set(request.user.id)
            
            # Attach to request for view convenience
            request.org_id = org_id
            request.org_role = org_role
            
            # Proceed with the request
            response = self.get_response(request)
            
            return response
            
        except UnauthorizedOrgAccess as e:
            return JsonResponse(
                {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                    }
                },
                status=e.status_code
            )
        except Exception as e:
            # Log the error and return generic response
            # In production, this should be logged to Sentry
            return JsonResponse(
                {
                    "error": {
                        "code": "tenant_context_error",
                        "message": "Failed to set tenant context",
                    }
                },
                status=500
            )
    
    def _is_org_scoped(self, path: str) -> bool:
        """
        Check if the URL path is org-scoped.
        
        Org-scoped URLs have the pattern: /api/v1/{org_id}/...
        """
        # Skip non-API paths
        if not path.startswith("/api/v1/"):
            return False
        
        # Skip auth and non-org paths
        skip_prefixes = [
            "/api/v1/health/",
            "/api/v1/auth/",
            "/api/v1/organisations/",
        ]
        for prefix in skip_prefixes:
            if path.startswith(prefix):
                return False
        
        return True
    
    def _extract_org_id(self, path: str) -> Optional[uuid.UUID]:
        """
        Extract org_id UUID from URL path.
        
        URL pattern: /api/v1/{org_id}/...
        """
        try:
            # Remove prefix and split
            parts = path.replace("/api/v1/", "").split("/")
            if not parts:
                return None
            
            # First part should be the org_id
            org_id_str = parts[0]
            return uuid.UUID(org_id_str)
        except (ValueError, IndexError):
            return None
    
    def _verify_org_membership(self, user, org_id: uuid.UUID) -> bool:
        """
        Verify that the user belongs to the organization.
        
        Uses cache to minimize database queries.
        """
        # Superadmins can access any org
        if getattr(user, 'is_superadmin', False):
            return True
        
        # Check cache first
        cache_key = f"user_org:{user.id}:{org_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Query database
        try:
            from apps.core.models import UserOrganisation
            is_member = UserOrganisation.objects.filter(
                user=user,
                org_id=org_id,
                accepted_at__isnull=False,  # Must have accepted invitation
            ).exists()
            
            # Cache for 5 minutes
            cache.set(cache_key, is_member, 300)
            
            return is_member
        except Exception:
            # If we can't verify, deny access (fail secure)
            return False
    
    def _get_org_role(self, user, org_id: uuid.UUID) -> Optional[dict]:
        """
        Get the user's role for this organization.
        
        Returns role dict with permission flags.
        """
        try:
            from apps.core.models import UserOrganisation
            user_org = UserOrganisation.objects.select_related('role').get(
                user=user,
                org_id=org_id,
            )
            
            role = user_org.role
            return {
                'id': role.id,
                'name': role.name,
                'can_manage_org': role.can_manage_org,
                'can_manage_users': role.can_manage_users,
                'can_manage_coa': role.can_manage_coa,
                'can_create_invoices': role.can_create_invoices,
                'can_approve_invoices': role.can_approve_invoices,
                'can_void_invoices': role.can_void_invoices,
                'can_create_journals': role.can_create_journals,
                'can_manage_banking': role.can_manage_banking,
                'can_file_gst': role.can_file_gst,
                'can_view_reports': role.can_view_reports,
                'can_export_data': role.can_export_data,
            }
        except Exception:
            return None
