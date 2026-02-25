"""
Common view utilities for LedgerSG.

Response wrappers and view helpers used across all apps.
"""

from functools import wraps
from typing import Callable, Any

from rest_framework.response import Response
from rest_framework import status

from common.exceptions import ValidationError, ResourceNotFound, DuplicateResource


def wrap_response(func: Callable) -> Callable:
    """
    Decorator that wraps view methods to handle common exceptions
    and standardize response format.
    
    Handles:
    - ValidationError -> 400 Bad Request
    - ResourceNotFound -> 404 Not Found
    - DuplicateResource -> 409 Conflict
    - Generic exceptions -> 500 Internal Server Error
    
    Usage:
        @wrap_response
        def get(self, request, org_id):
            # Your view logic
            return Response(data)
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Response:
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return Response(
                {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except ResourceNotFound as e:
            return Response(
                {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except DuplicateResource as e:
            return Response(
                {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                    }
                },
                status=status.HTTP_409_CONFLICT
            )
        except Exception as e:
            # Log the error in production
            return Response(
                {
                    "error": {
                        "code": "internal_error",
                        "message": "An internal error occurred",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return wrapper
