"""
Custom JSON renderer for LedgerSG API.

Handles Decimal serialization correctly (converts to string, not float)
to prevent precision loss in API responses.
"""

import json
from datetime import datetime, date
from decimal import Decimal

from rest_framework.renderers import JSONRenderer


class DecimalSafeJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles Decimal and datetime values correctly.
    
    Converts Decimal to string to preserve precision.
    Converts datetime to ISO format string.
    """
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert Decimal to string to preserve precision
            return str(obj)
        if isinstance(obj, datetime):
            # Convert datetime to ISO format
            return obj.isoformat()
        if isinstance(obj, date):
            # Convert date to ISO format
            return obj.isoformat()
        return super().default(obj)


class DecimalSafeJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that uses DecimalSafeJSONEncoder.
    
    Ensures all Decimal values in API responses are serialized as strings,
    preventing floating-point precision loss.
    """
    
    encoder_class = DecimalSafeJSONEncoder
