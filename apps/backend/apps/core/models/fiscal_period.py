"""
FiscalPeriod model for LedgerSG.

Represents a fiscal period (month) within a fiscal year.
Maps to core.fiscal_period table.
"""

from django.db import models

from common.models import TenantModel


class FiscalPeriod(TenantModel):
    """
    Fiscal period (usually a month) within a fiscal year.
    
    Maps to core.fiscal_period table.
    """
    
    fiscal_year = models.ForeignKey(
        "FiscalYear",
        on_delete=models.CASCADE,
        db_column="fiscal_year_id",
        related_name="periods",
    )
    
    label = models.CharField(
        max_length=50,
        db_column="label",
        help_text="e.g., 'Jan 2024'",
    )
    period_number = models.IntegerField(
        db_column="period_number",
        help_text="1-12 for monthly periods",
    )
    start_date = models.DateField(
        db_column="start_date",
    )
    end_date = models.DateField(
        db_column="end_date",
    )
    
    # Status
    is_open = models.BooleanField(
        default=True,
        db_column="is_open",
    )
    
    # Audit
    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column="locked_at",
    )
    locked_by = models.UUIDField(
        null=True,
        blank=True,
        db_column="locked_by",
    )
    
    class Meta:
        managed = False
        db_table = 'core"."fiscal_period'
        verbose_name = "fiscal period"
        verbose_name_plural = "fiscal periods"
        ordering = ["-start_date"]
    
    def __str__(self) -> str:
        return f"{self.label} ({self.org.name})"
    
    @property
    def is_locked(self) -> bool:
        """Check if period is locked."""
        return not self.is_open
