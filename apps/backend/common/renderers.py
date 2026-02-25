"""
Custom JSON renderer for LedgerSG API.

Handles Decimal serialization correctly (converts to string, not float)
to prevent precision loss in API responses.
"""

import json
from decimal import Decimal

from rest_framework.renderers import JSONRenderer


class DecimalSafeJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles Decimal values correctly.
    
    Converts Decimal to string instead of float to preserve precision.
    """
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert Decimal to string to preserve precision
            return str(obj)
        return super().default(obj)


class DecimalSafeJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that uses DecimalSafeJSONEncoder.
    
    Ensures all Decimal values in API responses are serialized as strings,
    preventing floating-point precision loss.
    """
    
    encoder_class = DecimalSafeJSONEncoder
