"""
InvoiceDocument model for LedgerSG.

Maps to invoicing.document table.
"""

from django.db import models
from common.models import TenantModel, SequenceModel


class InvoiceDocument(SequenceModel):
    """Invoice document model."""
    
    DOCUMENT_TYPES = [
        ("INVOICE", "Invoice"),
        ("QUOTE", "Quote"),
        ("CREDIT_NOTE", "Credit Note"),
    ]
    
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("ISSUED", "Issued"),
        ("PAID", "Paid"),
        ("VOID", "Void"),
    ]
    
    document_type = models.CharField(
        max_length=20, db_column="document_type"
    )
    sequence_number = models.CharField(
        max_length=50, db_column="sequence_number"
    )
    contact = models.ForeignKey(
        "Contact", on_delete=models.CASCADE,
        db_column="contact_id"
    )
    issue_date = models.DateField(db_column="issue_date")
    due_date = models.DateField(db_column="due_date")
    status = models.CharField(
        max_length=20, default="DRAFT",
        db_column="status"
    )
    total_excl = models.DecimalField(
        max_digits=19, decimal_places=4,
        default=0, db_column="total_excl"
    )
    gst_total = models.DecimalField(
        max_digits=19, decimal_places=4,
        default=0, db_column="gst_total"
    )
    total_incl = models.DecimalField(
        max_digits=19, decimal_places=4,
        default=0, db_column="total_incl"
    )
    
    class Meta:
        managed = False
        db_table = 'invoicing"."document'
