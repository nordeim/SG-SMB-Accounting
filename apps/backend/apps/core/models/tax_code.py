"""
TaxCode model for LedgerSG.

Maps to gst.tax_code table.
"""

from django.db import models
from decimal import Decimal
from common.models import TenantModel


class TaxCode(TenantModel):
    """Tax code model for GST calculation."""
    
    code = models.CharField(max_length=20, db_column="code")
    name = models.CharField(max_length=255, db_column="name")
    rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        null=True, blank=True,
        db_column="rate"
    )
    is_gst_charged = models.BooleanField(default=True, db_column="is_gst_charged")
    box_mapping = models.CharField(
        max_length=20, null=True, blank=True,
        db_column="box_mapping"
    )
    is_system = models.BooleanField(default=False, db_column="is_system")
    is_active = models.BooleanField(default=True, db_column="is_active")
    effective_from = models.DateField(null=True, db_column="effective_from")
    effective_to = models.DateField(null=True, db_column="effective_to")
    
    class Meta:
        managed = False
        db_table = 'gst"."tax_code'
        unique_together = [["org", "code"]]
