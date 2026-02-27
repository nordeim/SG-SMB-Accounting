"""
InvoiceLine model for LedgerSG.

Maps to invoicing.document_line table.
"""

from django.db import models
from common.models import BaseModel


class InvoiceLine(BaseModel):
    """Individual line items on an invoice."""
    
    document = models.ForeignKey(
        "InvoiceDocument", on_delete=models.CASCADE,
        db_column="document_id",
        related_name="lines"
    )
    org = models.ForeignKey(
        "Organisation", on_delete=models.CASCADE,
        db_column="org_id"
    )
    line_number = models.SmallIntegerField(db_column="line_number")
    description = models.CharField(max_length=500, db_column="description")
    account = models.ForeignKey(
        "Account", on_delete=models.CASCADE,
        db_column="account_id"
    )
    
    quantity = models.DecimalField(
        max_digits=19, decimal_places=4, default=1,
        db_column="quantity"
    )
    unit_price = models.DecimalField(
        max_digits=19, decimal_places=4,
        db_column="unit_price"
    )
    discount_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        db_column="discount_pct"
    )
    discount_amount = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="discount_amount"
    )
    
    tax_code = models.ForeignKey(
        "TaxCode", on_delete=models.CASCADE,
        db_column="tax_code_id"
    )
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        db_column="tax_rate"
    )
    is_tax_inclusive = models.BooleanField(
        default=False, db_column="is_tax_inclusive"
    )
    
    line_amount = models.DecimalField(
        max_digits=19, decimal_places=4,
        db_column="line_amount"
    )
    gst_amount = models.DecimalField(
        max_digits=19, decimal_places=4,
        db_column="gst_amount"
    )
    total_amount = models.DecimalField(
        max_digits=19, decimal_places=4,
        db_column="total_amount"
    )
    
    base_line_amount = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="base_line_amount"
    )
    base_gst_amount = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="base_gst_amount"
    )
    base_total_amount = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="base_total_amount"
    )
    
    is_bcrs_deposit = models.BooleanField(
        default=False, db_column="is_bcrs_deposit"
    )
    
    class Meta:
        managed = False
        db_table = 'invoicing"."document_line'
        unique_together = [["document", "line_number"]]
