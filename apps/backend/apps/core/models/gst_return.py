"""
GSTReturn model for LedgerSG.

Maps to gst.return table.
"""

from django.db import models
from common.models import TenantModel


class GSTReturn(TenantModel):
    """GST Return (F5/F7/F8) model for IRAS filing."""
    
    RETURN_TYPES = [
        ("F5", "GST F5 (Standard)"),
        ("F7", "GST F7 (Correction)"),
        ("F8", "GST F8 (Final)"),
    ]
    
    return_type = models.CharField(
        max_length=5, choices=RETURN_TYPES, default="F5",
        db_column="return_type"
    )
    period_start = models.DateField(db_column="period_start")
    period_end = models.DateField(db_column="period_end")
    filing_due_date = models.DateField(db_column="filing_due_date")
    
    # F5 Boxes
    box1_std_rated_supplies = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="box1_std_rated_supplies"
    )
    box2_zero_rated_supplies = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="box2_zero_rated_supplies"
    )
    box3_exempt_supplies = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="box3_exempt_supplies"
    )
    box4_total_supplies = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="box4_total_supplies"
    )
    box5_total_taxable_purchases = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="box5_total_taxable_purchases"
    )
    box6_output_tax = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="box6_output_tax"
    )
    box7_input_tax_claimable = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="box7_input_tax_claimable"
    )
    box8_net_gst = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="box8_net_gst"
    )
    box9_imports_under_schemes = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="box9_imports_under_schemes"
    )
    box10_tourist_refund = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="box10_tourist_refund"
    )
    
    status = models.CharField(
        max_length=20, default="DRAFT", db_column="status"
    )
    filed_at = models.DateTimeField(null=True, blank=True, db_column="filed_at")
    filed_by = models.ForeignKey(
        "AppUser", on_delete=models.SET_NULL, null=True, blank=True,
        db_column="filed_by"
    )
    filing_reference = models.CharField(
        max_length=100, blank=True, db_column="filing_reference"
    )
    
    class Meta:
        managed = False
        db_table = 'gst"."return'
