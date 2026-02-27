"""
JournalEntry model for LedgerSG.

Maps to journal.entry table.
"""

from django.db import models
from common.models import ImmutableModel


class JournalEntry(ImmutableModel):
    """Journal entry header model."""
    
    org = models.ForeignKey(
        "Organisation", on_delete=models.CASCADE,
        db_column="org_id"
    )
    entry_number = models.BigIntegerField(db_column="entry_number")
    entry_date = models.DateField(db_column="entry_date")
    
    SOURCE_TYPES = [
        ("MANUAL", "Manual"),
        ("SALES_INVOICE", "Sales Invoice"),
        ("PURCHASE_INVOICE", "Purchase Invoice"),
        # ... and others from schema
    ]
    
    source_type = models.CharField(
        max_length=30, db_column="source_type"
    )
    source_id = models.UUIDField(
        null=True, blank=True, db_column="source_id"
    )
    
    reference = models.CharField(
        max_length=100, blank=True, db_column="reference"
    )
    narration = models.TextField(db_column="narration")
    
    fiscal_year = models.ForeignKey(
        "FiscalYear", on_delete=models.CASCADE,
        db_column="fiscal_year_id"
    )
    fiscal_period = models.ForeignKey(
        "FiscalPeriod", on_delete=models.CASCADE,
        db_column="fiscal_period_id"
    )
    
    is_reversed = models.BooleanField(
        default=False, db_column="is_reversed"
    )
    reversed_by = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL,
        db_column="reversed_by_id",
        related_name="reversal_of"
    )
    reversal_of_entry = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL,
        db_column="reversal_of_id",
        related_name="reversal_entry"
    )
    
    posted_at = models.DateTimeField(
        auto_now_add=True, db_column="posted_at"
    )
    posted_by = models.ForeignKey(
        "AppUser", on_delete=models.CASCADE,
        db_column="posted_by"
    )
    
    class Meta:
        managed = False
        db_table = 'journal"."entry'
        unique_together = [["org", "entry_number"]]
