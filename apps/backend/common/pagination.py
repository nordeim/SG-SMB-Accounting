"""
Custom pagination classes for LedgerSG API.
"""

from rest_framework.pagination import (
    PageNumberPagination,
    CursorPagination,
)


class StandardPagination(PageNumberPagination):
    """
    Standard page-number pagination for most endpoints.
    
    Supports configurable page_size via query parameter.
    """
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
    page_query_param = "page"


class LargeResultPagination(PageNumberPagination):
    """
    Pagination for endpoints that return large results.
    
    e.g., journal entries, audit logs
    """
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500
    page_query_param = "page"


class CursorPagination(CursorPagination):
    """
    Cursor-based pagination for large datasets.
    
    Use for: journal entries, audit logs, invoice lines
    Provides consistent performance regardless of dataset size.
    """
    page_size = 100
    cursor_query_param = "cursor"
    ordering = "-created_at"


class SmallResultPagination(PageNumberPagination):
    """
    Pagination for endpoints with small result sets.
    
    e.g., dropdown options, settings
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"
