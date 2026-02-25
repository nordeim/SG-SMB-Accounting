"""
Custom exception hierarchy for LedgerSG.

Provides structured error handling and API responses.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class LedgerSGException(Exception):
    """Base exception for all LedgerSG errors."""
    
    default_message = "An error occurred"
    default_code = "error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(self, message=None, code=None, details=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(LedgerSGException):
    """Business rule validation error."""
    
    default_message = "Validation failed"
    default_code = "validation_error"
    status_code = status.HTTP_400_BAD_REQUEST


class ImmutabilityError(LedgerSGException):
    """Attempt to modify an immutable record."""
    
    default_message = "This record cannot be modified"
    default_code = "immutable_record"
    status_code = status.HTTP_409_CONFLICT


class UnbalancedEntryError(LedgerSGException):
    """Journal entry debits != credits."""
    
    default_message = "Journal entry is not balanced"
    default_code = "unbalanced_entry"
    status_code = status.HTTP_400_BAD_REQUEST


class PeriodClosedError(LedgerSGException):
    """Posting to a closed fiscal period."""
    
    default_message = "Cannot post to a closed fiscal period"
    default_code = "period_closed"
    status_code = status.HTTP_400_BAD_REQUEST


class GSTCalculationError(LedgerSGException):
    """Tax computation failure."""
    
    default_message = "GST calculation failed"
    default_code = "gst_calculation_error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class PeppolTransmissionError(LedgerSGException):
    """InvoiceNow transmission failure."""
    
    default_message = "InvoiceNow transmission failed"
    default_code = "peppol_error"
    status_code = status.HTTP_502_BAD_GATEWAY


class UnauthorizedOrgAccess(LedgerSGException):
    """User attempted to access an organization they don't belong to."""
    
    default_message = "You do not have access to this organization"
    default_code = "unauthorized_org_access"
    status_code = status.HTTP_403_FORBIDDEN


class PermissionDenied(LedgerSGException):
    """User lacks permission for the requested action."""
    
    default_message = "Permission denied"
    default_code = "permission_denied"
    status_code = status.HTTP_403_FORBIDDEN


class ResourceNotFound(LedgerSGException):
    """Requested resource does not exist."""
    
    default_message = "Resource not found"
    default_code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND


class DuplicateResource(LedgerSGException):
    """Attempt to create a resource that already exists."""
    
    default_message = "Resource already exists"
    default_code = "duplicate_resource"
    status_code = status.HTTP_409_CONFLICT


class InsufficientFunds(LedgerSGException):
    """Account has insufficient funds for the operation."""
    
    default_message = "Insufficient funds"
    default_code = "insufficient_funds"
    status_code = status.HTTP_400_BAD_REQUEST


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler for LedgerSG exceptions.
    
    Converts LedgerSGException instances to standardized API responses.
    Falls back to DRF's default handler for other exceptions.
    """
    # Handle LedgerSG exceptions
    if isinstance(exc, LedgerSGException):
        data = {
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        }
        return Response(data, status=exc.status_code)
    
    # Handle Django validation errors
    if isinstance(exc, ValidationError):
        data = {
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        }
        return Response(data, status=exc.status_code)
    
    # Fall back to DRF's default exception handler
    response = exception_handler(exc, context)
    
    # If DRF handled it, return as-is
    if response is not None:
        return response
    
    # Unhandled exception - return generic 500
    return Response(
        {
            "error": {
                "code": "internal_error",
                "message": "An internal server error occurred",
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
