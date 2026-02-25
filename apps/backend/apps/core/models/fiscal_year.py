"""
FiscalYear model for LedgerSG.

Represents a fiscal year for an organisation.
Maps to core.fiscal_year table.
"""

from django.db import models

from common.models import BaseModel, TenantModel


class FiscalYear(BaseModel, TenantModel):
    """
    Fiscal year for an organisation.
    
    Maps to core.fiscal_year table.
    Supports Singapore's flexible FY end dates.
    """
    
    label = models.CharField(
        max_length=50,
        db_column="label",
        help_text="e.g., 'FY2024'",
    )
    start_date = models.DateField(
        db_column="start_date",
    )
    end_date = models.DateField(
        db_column="end_date",
    )
    
    # Status
    is_closed = models.BooleanField(
        default=False,
        db_column="is_closed",
    )
    
    # Audit
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column="closed_at",
    )
    closed_by = models.UUIDField(
        null=True,
        blank=True,
        db_column="closed_by",
    )
    
    class Meta:
        managed = False
        db_table = 'core"."fiscal_year'
        verbose_name = "fiscal year"
        verbose_name_plural = "fiscal years"
        ordering = ["-start_date"]
    
    def __str__(self) -> str:
        return f"{self.label} ({self.org.name})"
