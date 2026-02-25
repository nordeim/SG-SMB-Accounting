"""
Audit Context Middleware

Captures request metadata (IP address, user agent, request path) and makes it 
available to the audit trigger system via SET LOCAL session variables.
"""

from django.db import connection
from django.http import HttpRequest, HttpResponse


class AuditContextMiddleware:
    """
    Middleware that captures audit-related request metadata.
    
    Sets session variables that the audit.log_change() trigger can read.
    Must be placed AFTER TenantContextMiddleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Only capture for API requests
        if not request.path.startswith("/api/"):
            return self.get_response(request)
        
        # Extract request metadata
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]  # Limit length
        request_path = request.path[:500]
        
        # Set session variables for audit triggers
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.client_ip = %s", [ip_address])
                cursor.execute("SET LOCAL app.user_agent = %s", [user_agent])
                cursor.execute("SET LOCAL app.request_path = %s", [request_path])
        except Exception:
            # Fail silently - audit logging should not break the request
            pass
        
        # Proceed with the request
        response = self.get_response(request)
        
        return response
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Get the client IP address from the request.
        
        Checks X-Forwarded-For header first (for proxies), then REMOTE_ADDR.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Get the first IP in the chain (client IP)
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")
        
        # Limit length and validate
        ip = ip[:45]  # IPv6 max length
        
        # Basic validation - return empty if invalid
        if not ip or " " in ip:
            return ""
        
        return ip
