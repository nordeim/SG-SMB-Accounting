"""
InvoiceDocument model for LedgerSG.

Maps to invoicing.document table.
"""

from django.db import models
from common.models import TenantModel, SequenceModel


class InvoiceDocument(TenantModel, SequenceModel):
    """Invoice document model."""
    
    DOCUMENT_TYPES = [
        ("SALES_INVOICE", "Invoice"),
        ("SALES_QUOTE", "Quote"),
        ("SALES_CREDIT_NOTE", "Credit Note"),
    ]
    
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SENT", "Sent"),
        ("APPROVED", "Approved"),
        ("PARTIALLY_PAID", "Partially Paid"),
        ("PAID", "Paid"),
        ("VOID", "Void"),
    ]
    
    document_type = models.CharField(
        max_length=20, db_column="document_type"
    )
    sequence_number = models.CharField(
        max_length=50, db_column="document_number"
    )
    contact = models.ForeignKey(
        "Contact", on_delete=models.CASCADE,
        db_column="contact_id"
    )
    issue_date = models.DateField(db_column="document_date")
    due_date = models.DateField(db_column="due_date")
    status = models.CharField(
        max_length=20, default="DRAFT",
        db_column="status"
    )
    
    total_excl = models.DecimalField(
        max_digits=19, decimal_places=4,
        default=0, db_column="subtotal"
    )
    gst_total = models.DecimalField(
        max_digits=19, decimal_places=4,
        default=0, db_column="total_gst"
    )
    total_incl = models.DecimalField(
        max_digits=19, decimal_places=4,
        default=0, db_column="total_amount"
    )
    
    notes = models.TextField(
        blank=True, db_column="customer_notes"
    )
    reference = models.CharField(
        max_length=100, blank=True, db_column="reference"
    )
    
    class Meta:
        managed = False
        db_table = 'invoicing"."document'

    def generate_sequence(self) -> str:
        """Generate sequence number using DocumentService."""
        from apps.invoicing.services import DocumentService
        return DocumentService._get_next_document_number(self.org_id, self.document_type)
