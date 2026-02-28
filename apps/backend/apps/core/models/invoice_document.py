"""
InvoiceDocument model for LedgerSG.

Maps to invoicing.document table.
"""

from django.db import models
from common.models import TenantModel


class InvoiceDocument(TenantModel):
    """Invoice document model."""
    
    # SQL ENUM: invoicing.doc_type
    DOCUMENT_TYPES = [
        ("SALES_INVOICE", "Sales Invoice"),
        ("SALES_CREDIT_NOTE", "Sales Credit Note"),
        ("SALES_DEBIT_NOTE", "Sales Debit Note"),
        ("SALES_QUOTE", "Sales Quote"),
        ("PURCHASE_INVOICE", "Purchase Invoice"),
        ("PURCHASE_CREDIT_NOTE", "Purchase Credit Note"),
        ("PURCHASE_DEBIT_NOTE", "Purchase Debit Note"),
        ("PURCHASE_ORDER", "Purchase Order"),
    ]
    
    # SQL ENUM: invoicing.doc_status
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("APPROVED", "Approved"),
        ("SENT", "Sent"),
        ("PARTIALLY_PAID", "Partially Paid"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
        ("VOID", "Void"),  # SQL uses "VOID" not "VOIDED"
    ]
    
    document_type = models.CharField(
        max_length=20, db_column="document_type",
        choices=DOCUMENT_TYPES
    )
    # Document number (sequence)
    document_number = models.CharField(
        max_length=50, db_column="document_number"
    )
    # CRITICAL FIX: Changed from CASCADE to RESTRICT to match SQL
    contact = models.ForeignKey(
        "Contact", on_delete=models.RESTRICT,
        db_column="contact_id"
    )
    issue_date = models.DateField(db_column="document_date")
    due_date = models.DateField(db_column="due_date")
    status = models.CharField(
        max_length=20, default="DRAFT",
        db_column="status",
        choices=STATUS_CHOICES
    )
    
    # Currency & Exchange Rate
    currency = models.CharField(max_length=3, default="SGD", db_column="currency")
    exchange_rate = models.DecimalField(
        max_digits=12, decimal_places=6, default=1.000000,
        db_column="exchange_rate"
    )
    
    # Monetary Fields
    total_excl = models.DecimalField(
        max_digits=19, decimal_places=4,
        default=0, db_column="subtotal"
    )
    total_discount = models.DecimalField(
        max_digits=10, decimal_places=4, default=0,
        db_column="total_discount"
    )
    gst_total = models.DecimalField(
        max_digits=19, decimal_places=4,
        default=0, db_column="total_gst"
    )
    total_incl = models.DecimalField(
        max_digits=19, decimal_places=4,
        default=0, db_column="total_amount"
    )
    amount_paid = models.DecimalField(
        max_digits=10, decimal_places=4, default=0,
        db_column="amount_paid"
    )
    # Note: amount_due is GENERATED ALWAYS in SQL, not stored
    
    # Base Currency Equivalents
    base_subtotal = models.DecimalField(
        max_digits=10, decimal_places=4, default=0,
        db_column="base_subtotal"
    )
    base_total_gst = models.DecimalField(
        max_digits=10, decimal_places=4, default=0,
        db_column="base_total_gst"
    )
    base_total_amount = models.DecimalField(
        max_digits=10, decimal_places=4, default=0,
        db_column="base_total_amount"
    )
    
    # Notes & References
    notes = models.TextField(blank=True, db_column="customer_notes")
    internal_notes = models.TextField(blank=True, db_column="internal_notes")
    reference = models.CharField(
        max_length=100, blank=True, db_column="reference"
    )
    
    # Tax Invoice Compliance
    is_tax_invoice = models.BooleanField(default=False, db_column="is_tax_invoice")
    tax_invoice_label = models.CharField(
        max_length=50, blank=True, db_column="tax_invoice_label"
    )
    
    # InvoiceNow / Peppol
    peppol_message_id = models.UUIDField(null=True, blank=True, db_column="peppol_message_id")
    invoicenow_status = models.CharField(
        max_length=20, default="NOT_APPLICABLE",
        db_column="invoicenow_status",
        choices=[
            ("NOT_APPLICABLE", "Not Applicable"),
            ("PENDING", "Pending"),
            ("QUEUED", "Queued"),
            ("TRANSMITTED", "Transmitted"),
            ("DELIVERED", "Delivered"),
            ("FAILED", "Failed"),
            ("REJECTED", "Rejected"),
        ]
    )
    invoicenow_sent_at = models.DateTimeField(null=True, blank=True, db_column="invoicenow_sent_at")
    invoicenow_error = models.TextField(blank=True, db_column="invoicenow_error")
    
    # Workflow & Linkage
    journal_entry = models.ForeignKey(
        "JournalEntry", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="journal_entry_id"
    )
    related_document = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="related_document_id",
        related_name="related_documents"
    )
    
    # Audit Fields
    approved_at = models.DateTimeField(null=True, blank=True, db_column="approved_at")
    approved_by = models.ForeignKey(
        "AppUser", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="approved_by",
        related_name="approved_documents"
    )
    voided_at = models.DateTimeField(null=True, blank=True, db_column="voided_at")
    voided_by = models.ForeignKey(
        "AppUser", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="voided_by",
        related_name="voided_documents"
    )
    void_reason = models.TextField(blank=True, db_column="void_reason")
    
    class Meta:
        managed = False
        db_table = 'invoicing"."document'

    def generate_sequence(self) -> str:
        """Generate sequence number using DocumentService."""
        from apps.invoicing.services import DocumentService
        return DocumentService._get_next_document_number(self.org_id, self.document_type)
