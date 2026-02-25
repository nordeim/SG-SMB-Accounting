"""
Organisation model for LedgerSG.

Represents a tenant (company/business entity).
Maps to core.organisation table.
"""

from django.db import models

from common.models import BaseModel


class Organisation(BaseModel):
    """
    Organisation (tenant) model.
    
    Maps to core.organisation table.
    Each organisation has its own Chart of Accounts, invoices, etc.
    """
    
    # Basic info
    name = models.CharField(
        max_length=255,
        db_column="name",
    )
    legal_name = models.CharField(
        max_length=255,
        blank=True,
        db_column="legal_name",
    )
    
    # Singapore-specific identifiers
    uen = models.CharField(
        max_length=20,
        blank=True,
        db_column="uen",
        verbose_name="UEN (Unique Entity Number)",
    )
    entity_type = models.CharField(
        max_length=50,
        blank=True,
        db_column="entity_type",
        choices=[
            ("SOLE_PROPRIETORSHIP", "Sole Proprietorship"),
            ("PARTNERSHIP", "Partnership"),
            ("PRIVATE_LIMITED", "Private Limited Company"),
            ("PUBLIC_LIMITED", "Public Limited Company"),
            ("LIMITED_LIABILITY_PARTNERSHIP", "Limited Liability Partnership"),
            ("NON_PROFIT", "Non-Profit Organisation"),
        ],
    )
    
    # GST registration
    gst_registered = models.BooleanField(
        default=False,
        db_column="gst_registered",
    )
    gst_reg_number = models.CharField(
        max_length=50,
        blank=True,
        db_column="gst_reg_number",
    )
    gst_reg_date = models.DateField(
        null=True,
        blank=True,
        db_column="gst_reg_date",
    )
    gst_scheme = models.CharField(
        max_length=50,
        blank=True,
        db_column="gst_scheme",
        choices=[
            ("STANDARD", "Standard GST"),
            ("CASH_ACCOUNTING", "Cash Accounting"),
            ("SECOND_HAND", "Second-Hand Goods"),
            ("TOURIST_REFUND", "Tourist Refund"),
        ],
    )
    gst_filing_frequency = models.CharField(
        max_length=20,
        default="QUARTERLY",
        db_column="gst_filing_frequency",
        choices=[
            ("MONTHLY", "Monthly"),
            ("QUARTERLY", "Quarterly"),
            ("SEMI_ANNUAL", "Semi-Annual"),
        ],
    )
    
    # InvoiceNow / Peppol
    peppol_participant_id = models.CharField(
        max_length=100,
        blank=True,
        db_column="peppol_participant_id",
    )
    invoicenow_enabled = models.BooleanField(
        default=False,
        db_column="invoicenow_enabled",
    )
    
    # Fiscal settings
    fy_start_month = models.IntegerField(
        default=1,
        db_column="fy_start_month",
        help_text="Month when fiscal year starts (1-12)",
    )
    base_currency = models.CharField(
        max_length=3,
        default="SGD",
        db_column="base_currency",
    )
    timezone = models.CharField(
        max_length=50,
        default="Asia/Singapore",
        db_column="timezone",
    )
    
    # Address
    address_line_1 = models.CharField(
        max_length=255,
        blank=True,
        db_column="address_line_1",
    )
    address_line_2 = models.CharField(
        max_length=255,
        blank=True,
        db_column="address_line_2",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        db_column="city",
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        db_column="postal_code",
    )
    country = models.CharField(
        max_length=2,
        default="SG",
        db_column="country",
    )
    
    # Contact
    contact_email = models.EmailField(
        blank=True,
        db_column="contact_email",
    )
    contact_phone = models.CharField(
        max_length=50,
        blank=True,
        db_column="contact_phone",
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        db_column="is_active",
    )
    
    # Soft delete
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column="deleted_at",
    )
    deleted_by = models.UUIDField(
        null=True,
        blank=True,
        db_column="deleted_by",
    )
    
    class Meta:
        managed = False
        db_table = 'core"."organisation'
        verbose_name = "organisation"
        verbose_name_plural = "organisations"
    
    def __str__(self) -> str:
        return self.name
    
    @property
    def is_gst_registered(self) -> bool:
        """Check if org is GST registered with valid registration."""
        return self.gst_registered and bool(self.gst_reg_number)
    
    @property
    def current_fiscal_year(self):
        """Get the current open fiscal year."""
        from .fiscal_year import FiscalYear
        return FiscalYear.objects.filter(
            org=self,
            is_closed=False,
        ).order_by("start_date").first()
    
    @property
    def gst_filing_periods_per_year(self) -> int:
        """Return number of GST filing periods per year."""
        mapping = {
            "MONTHLY": 12,
            "QUARTERLY": 4,
            "SEMI_ANNUAL": 2,
        }
        return mapping.get(self.gst_filing_frequency, 4)
