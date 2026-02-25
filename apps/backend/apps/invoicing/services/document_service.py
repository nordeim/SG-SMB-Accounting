"""
Document service for LedgerSG Invoicing module.

Handles invoices, quotes, credit notes, debit notes including:
- Document creation with line items
- GST calculation per line
- Document sequencing
- Status workflow management
- Journal posting on approval
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import date, timedelta

from django.db import connection, transaction

from apps.core.models import InvoiceDocument, InvoiceLine, Contact, Account
from apps.gst.services import TaxCodeService, GSTCalculationService
from common.exceptions import ValidationError, DuplicateResource, ResourceNotFound
from common.decimal_utils import money, sum_money


# Document type definitions
DOCUMENT_TYPES = {
    "INVOICE": {"prefix": "INV", "next_status": "SENT"},
    "CREDIT_NOTE": {"prefix": "CN", "next_status": "APPROVED"},
    "DEBIT_NOTE": {"prefix": "DN", "next_status": "APPROVED"},
    "QUOTE": {"prefix": "QUO", "next_status": "SENT"},
}

# Valid status transitions
STATUS_TRANSITIONS = {
    "DRAFT": ["SENT", "VOIDED"],
    "SENT": ["APPROVED", "VOIDED"],
    "APPROVED": ["PAID_PARTIAL", "PAID", "VOIDED"],
    "PAID_PARTIAL": ["PAID", "VOIDED"],
    "PAID": ["VOIDED"],
    "VOIDED": [],
}


class DocumentService:
    """Service class for invoice document operations."""
    
    @staticmethod
    def list_documents(
        org_id: UUID,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        contact_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None
    ) -> List[InvoiceDocument]:
        """
        List invoice documents.
        
        Args:
            org_id: Organisation ID
            document_type: Filter by type (INVOICE, QUOTE, etc.)
            status: Filter by status
            contact_id: Filter by contact
            date_from: Filter from date
            date_to: Filter to date
            search: Search document number
            
        Returns:
            List of InvoiceDocument instances
        """
        queryset = InvoiceDocument.objects.filter(org_id=org_id)
        
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if contact_id:
            queryset = queryset.filter(contact_id=contact_id)
        
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)
        
        if search:
            queryset = queryset.filter(document_number__icontains=search)
        
        return list(queryset.order_by("-issue_date", "-document_number"))
    
    @staticmethod
    def get_document(org_id: UUID, document_id: UUID) -> InvoiceDocument:
        """
        Get document by ID.
        
        Args:
            org_id: Organisation ID
            document_id: Document ID
            
        Returns:
            InvoiceDocument instance
        """
        try:
            return InvoiceDocument.objects.get(id=document_id, org_id=org_id)
        except InvoiceDocument.DoesNotExist:
            raise ResourceNotFound(f"Document {document_id} not found")
    
    @staticmethod
    def create_document(
        org_id: UUID,
        document_type: str,
        contact_id: UUID,
        issue_date: date,
        due_date: Optional[date] = None,
        reference: str = "",
        notes: str = "",
        lines: List[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> InvoiceDocument:
        """
        Create a new invoice document with lines.
        
        Args:
            org_id: Organisation ID
            document_type: Type (INVOICE, QUOTE, CREDIT_NOTE, DEBIT_NOTE)
            contact_id: Contact ID
            issue_date: Issue date
            due_date: Due date (default: issue_date + contact payment terms)
            reference: Customer reference
            notes: Internal notes
            lines: List of line items
            user_id: Creating user ID
            
        Returns:
            Created InvoiceDocument instance
        """
        if document_type not in DOCUMENT_TYPES:
            valid_types = ", ".join(DOCUMENT_TYPES.keys())
            raise ValidationError(f"Invalid document type. Valid: {valid_types}")
        
        # Get contact
        try:
            contact = Contact.objects.get(id=contact_id, org_id=org_id)
        except Contact.DoesNotExist:
            raise ResourceNotFound(f"Contact {contact_id} not found")
        
        # Calculate due date if not provided
        if due_date is None:
            due_date = issue_date + timedelta(days=contact.payment_terms_days)
        
        # Get next document number
        document_number = DocumentService._get_next_document_number(org_id, document_type)
        
        with transaction.atomic():
            # Create document
            document = InvoiceDocument.objects.create(
                org_id=org_id,
                document_type=document_type,
                document_number=document_number,
                contact=contact,
                contact_snapshot={
                    "name": contact.name,
                    "company_name": contact.company_name,
                    "email": contact.email,
                    "phone": contact.phone,
                    "address": {
                        "line1": contact.address_line1,
                        "line2": contact.address_line2,
                        "city": contact.city,
                        "postal_code": contact.postal_code,
                        "country": contact.country,
                    },
                    "uen": contact.uen,
                    "peppol_id": contact.peppol_id,
                },
                issue_date=issue_date,
                due_date=due_date,
                reference=reference,
                notes=notes,
                status="DRAFT",
                created_by_id=user_id,
            )
            
            # Add lines
            if lines:
                DocumentService._add_lines(org_id, document, lines)
                DocumentService._recalculate_totals(document)
        
        return document
    
    @staticmethod
    def update_document(
        org_id: UUID,
        document_id: UUID,
        **updates
    ) -> InvoiceDocument:
        """
        Update document (only in DRAFT status).
        
        Args:
            org_id: Organisation ID
            document_id: Document ID
            **updates: Fields to update
            
        Returns:
            Updated InvoiceDocument instance
        """
        document = DocumentService.get_document(org_id, document_id)
        
        if document.status != "DRAFT":
            raise ValidationError(f"Cannot update document in status '{document.status}'. Only DRAFT documents can be modified.")
        
        allowed_fields = ["due_date", "reference", "notes"]
        
        for key, value in updates.items():
            if key in allowed_fields and hasattr(document, key):
                setattr(document, key, value)
        
        document.save()
        return document
    
    @staticmethod
    def add_line(
        org_id: UUID,
        document_id: UUID,
        account_id: UUID,
        description: str,
        quantity: Decimal,
        unit_price: Decimal,
        tax_code_id: UUID,
        is_bcrs_deposit: bool = False,
        **kwargs
    ) -> InvoiceLine:
        """
        Add a line to a document.
        
        Args:
            org_id: Organisation ID
            document_id: Document ID
            account_id: Revenue account ID
            description: Line description
            quantity: Quantity
            unit_price: Unit price
            tax_code_id: Tax code ID
            is_bcrs_deposit: Whether BCRS deposit
            **kwargs: Additional fields
            
        Returns:
            Created InvoiceLine instance
        """
        document = DocumentService.get_document(org_id, document_id)
        
        if document.status != "DRAFT":
            raise ValidationError("Can only add lines to DRAFT documents.")
        
        # Validate account
        try:
            account = Account.objects.get(id=account_id, org_id=org_id)
        except Account.DoesNotExist:
            raise ResourceNotFound(f"Account {account_id} not found")
        
        # Calculate line totals
        quantity = Decimal(str(quantity))
        unit_price = money(unit_price)
        amount = (quantity * unit_price).quantize(Decimal("0.01"))
        
        # Get tax code and calculate GST
        tax_code = TaxCodeService.get_tax_code(org_id, tax_code_id)
        gst_result = GSTCalculationService.calculate_line_gst(
            amount=amount,
            rate=tax_code.rate or Decimal("0.00"),
            is_bcrs_deposit=is_bcrs_deposit
        )
        
        line = InvoiceLine.objects.create(
            invoice=document,
            account=account,
            description=description.strip(),
            quantity=quantity,
            unit_price=unit_price,
            amount=amount,
            tax_code=tax_code,
            gst_amount=gst_result["gst_amount"],
            is_bcrs_deposit=is_bcrs_deposit,
            **kwargs
        )
        
        # Recalculate document totals
        DocumentService._recalculate_totals(document)
        
        return line
    
    @staticmethod
    def remove_line(org_id: UUID, document_id: UUID, line_id: UUID) -> None:
        """
        Remove a line from a document.
        
        Args:
            org_id: Organisation ID
            document_id: Document ID
            line_id: Line ID
        """
        document = DocumentService.get_document(org_id, document_id)
        
        if document.status != "DRAFT":
            raise ValidationError("Can only remove lines from DRAFT documents.")
        
        try:
            line = InvoiceLine.objects.get(id=line_id, invoice=document)
            line.delete()
        except InvoiceLine.DoesNotExist:
            raise ResourceNotFound(f"Line {line_id} not found")
        
        # Recalculate totals
        DocumentService._recalculate_totals(document)
    
    @staticmethod
    def transition_status(
        org_id: UUID,
        document_id: UUID,
        new_status: str,
        user_id: Optional[UUID] = None
    ) -> InvoiceDocument:
        """
        Transition document status.
        
        Args:
            org_id: Organisation ID
            document_id: Document ID
            new_status: Target status
            user_id: User making the transition
            
        Returns:
            Updated InvoiceDocument instance
        """
        document = DocumentService.get_document(org_id, document_id)
        
        # Validate transition
        valid_transitions = STATUS_TRANSITIONS.get(document.status, [])
        if new_status not in valid_transitions:
            raise ValidationError(
                f"Cannot transition from '{document.status}' to '{new_status}'. "
                f"Valid transitions: {', '.join(valid_transitions) or 'none'}"
            )
        
        with transaction.atomic():
            old_status = document.status
            document.status = new_status
            
            # Status-specific actions
            if new_status == "APPROVED":
                document.approved_at = timezone.now()
                document.approved_by_id = user_id
                
                # Post journal entry (for invoices/credit notes)
                if document.document_type in ["INVOICE", "CREDIT_NOTE", "DEBIT_NOTE"]:
                    DocumentService._post_journal_entry(org_id, document)
            
            elif new_status == "VOIDED":
                document.voided_at = timezone.now()
                document.voided_by_id = user_id
                
                # Reverse journal entry if posted
                if document.journal_entry_id:
                    DocumentService._reverse_journal_entry(org_id, document)
            
            document.save()
        
        return document
    
    @staticmethod
    def convert_quote_to_invoice(org_id: UUID, quote_id: UUID, user_id: Optional[UUID] = None) -> InvoiceDocument:
        """
        Convert a quote to an invoice.
        
        Args:
            org_id: Organisation ID
            quote_id: Quote document ID
            user_id: User converting
            
        Returns:
            Created InvoiceDocument instance
        """
        quote = DocumentService.get_document(org_id, quote_id)
        
        if quote.document_type != "QUOTE":
            raise ValidationError("Only quotes can be converted to invoices.")
        
        if quote.status not in ["DRAFT", "SENT"]:
            raise ValidationError(f"Cannot convert quote in status '{quote.status}'.")
        
        with transaction.atomic():
            # Get lines from quote
            lines = []
            for line in quote.lines.filter(is_voided=False):
                lines.append({
                    "account_id": line.account_id,
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "tax_code_id": line.tax_code_id,
                    "is_bcrs_deposit": line.is_bcrs_deposit,
                })
            
            # Create invoice
            invoice = DocumentService.create_document(
                org_id=org_id,
                document_type="INVOICE",
                contact_id=quote.contact_id,
                issue_date=date.today(),
                due_date=date.today() + timedelta(days=quote.contact.payment_terms_days),
                reference=f"Quote {quote.document_number}",
                notes=quote.notes,
                lines=lines,
                user_id=user_id
            )
            
            # Mark quote as converted
            quote.status = "CONVERTED"
            quote.converted_to_id = invoice.id
            quote.save()
        
        return invoice
    
    @staticmethod
    def _get_next_document_number(org_id: UUID, document_type: str) -> str:
        """
        Get next document number from sequence.
        
        Args:
            org_id: Organisation ID
            document_type: Document type
            
        Returns:
            Next document number (e.g., "INV-00042")
        """
        prefix = DOCUMENT_TYPES[document_type]["prefix"]
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT core.get_next_document_number(%s, %s)",
                [str(org_id), document_type]
            )
            next_num = cursor.fetchone()[0]
        
        return f"{prefix}-{next_num:05d}"
    
    @staticmethod
    def _add_lines(org_id: UUID, document: InvoiceDocument, lines: List[Dict[str, Any]]) -> None:
        """
        Add multiple lines to a document.
        
        Args:
            org_id: Organisation ID
            document: InvoiceDocument instance
            lines: List of line dictionaries
        """
        for line_data in lines:
            account_id = line_data.get("account_id")
            if not account_id:
                raise ValidationError("Line must have an account_id.")
            
            DocumentService.add_line(
                org_id=org_id,
                document_id=document.id,
                account_id=UUID(str(account_id)),
                description=line_data.get("description", ""),
                quantity=Decimal(str(line_data.get("quantity", 1))),
                unit_price=money(line_data.get("unit_price", 0)),
                tax_code_id=UUID(str(line_data.get("tax_code_id"))),
                is_bcrs_deposit=line_data.get("is_bcrs_deposit", False)
            )
    
    @staticmethod
    def _recalculate_totals(document: InvoiceDocument) -> None:
        """
        Recalculate document totals from lines.
        
        Args:
            document: InvoiceDocument instance
        """
        lines = document.lines.filter(is_voided=False)
        
        subtotal = sum_money(line.amount for line in lines)
        gst_total = sum_money(line.gst_amount for line in lines)
        total = subtotal + gst_total
        
        document.subtotal = subtotal
        document.gst_total = gst_total
        document.total = total
        document.save()
    
    @staticmethod
    def _post_journal_entry(org_id: UUID, document: InvoiceDocument) -> None:
        """
        Post journal entry for approved document.
        
        This is a placeholder - full implementation in Journal module.
        
        Args:
            org_id: Organisation ID
            document: InvoiceDocument instance
        """
        # TODO: Implement in Journal module
        # For now, just mark as posted
        pass
    
    @staticmethod
    def _reverse_journal_entry(org_id: UUID, document: InvoiceDocument) -> None:
        """
        Reverse journal entry for voided document.
        
        This is a placeholder - full implementation in Journal module.
        
        Args:
            org_id: Organisation ID
            document: InvoiceDocument instance
        """
        # TODO: Implement in Journal module
        pass


# Import at end to avoid circular imports
from django.utils import timezone
from django.db import models
