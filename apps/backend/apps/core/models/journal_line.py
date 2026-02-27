"""
JournalLine model for LedgerSG.

Maps to journal.line table.
"""

from django.db import models
from common.models import ImmutableModel


class JournalLine(ImmutableModel):
    """Individual debit/credit line within a journal entry."""
    
    entry = models.ForeignKey(
        "JournalEntry", on_delete=models.CASCADE,
        db_column="entry_id",
        related_name="lines"
    )
    org = models.ForeignKey(
        "Organisation", on_delete=models.CASCADE,
        db_column="org_id"
    )
    line_number = models.SmallIntegerField(db_column="line_number")
    account = models.ForeignKey(
        "Account", on_delete=models.CASCADE,
        db_column="account_id"
    )
    description = models.CharField(
        max_length=500, blank=True, db_column="description"
    )
    
    debit = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="debit"
    )
    credit = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="credit"
    )
    
    tax_code = models.ForeignKey(
        "TaxCode", null=True, blank=True,
        on_delete=models.SET_NULL,
        db_column="tax_code_id"
    )
    tax_amount = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="tax_amount"
    )
    
    currency = models.CharField(
        max_length=3, default="SGD", db_column="currency"
    )
    exchange_rate = models.DecimalField(
        max_digits=19, decimal_places=6, default=1,
        db_column="exchange_rate"
    )
    
    base_debit = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="base_debit"
    )
    base_credit = models.DecimalField(
        max_digits=19, decimal_places=4, default=0,
        db_column="base_credit"
    )
    
    class Meta:
        managed = False
        db_table = 'journal"."line'
        unique_together = [["entry", "line_number"]]
