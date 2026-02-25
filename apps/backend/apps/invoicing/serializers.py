"""
Invoicing serializers for LedgerSG.

Serializers for Contact and InvoiceDocument models.
"""

from rest_framework import serializers
from decimal import Decimal

from apps.core.models import Contact, InvoiceDocument, InvoiceLine


class ContactListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for contact list views."""
    
    class Meta:
        model = Contact
        fields = [
            "id", "name", "company_name", "email", "phone",
            "uen", "is_customer", "is_supplier", "is_active"
        ]


class ContactDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for contact views."""
    
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Contact
        fields = [
            "id", "name", "company_name", "email", "phone",
            "address_line1", "address_line2", "city", "postal_code", "country",
            "full_address",
            "uen", "peppol_id",
            "is_customer", "is_supplier", "is_active",
            "payment_terms_days",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_full_address(self, obj: Contact) -> str:
        """Get formatted full address."""
        parts = [
            obj.address_line1,
            obj.address_line2,
            obj.city,
            obj.postal_code,
            obj.country
        ]
        return ", ".join(filter(None, parts))


class ContactCreateSerializer(serializers.Serializer):
    """Serializer for creating a contact."""
    
    name = serializers.CharField(max_length=255)
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    address_line1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    country = serializers.CharField(max_length=2, default="SG")
    uen = serializers.CharField(max_length=20, required=False, allow_blank=True)
    peppol_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    is_customer = serializers.BooleanField(default=True)
    is_supplier = serializers.BooleanField(default=False)
    payment_terms_days = serializers.IntegerField(min_value=0, max_value=365, default=30)
    
    def validate(self, data):
        """Validate contact data."""
        if not data.get("is_customer") and not data.get("is_supplier"):
            raise serializers.ValidationError(
                "Contact must be a customer, supplier, or both."
            )
        return data


class ContactUpdateSerializer(serializers.Serializer):
    """Serializer for updating a contact."""
    
    name = serializers.CharField(max_length=255, required=False)
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    address_line1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    country = serializers.CharField(max_length=2, required=False)
    uen = serializers.CharField(max_length=20, required=False, allow_blank=True)
    peppol_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    is_customer = serializers.BooleanField(required=False)
    is_supplier = serializers.BooleanField(required=False)
    payment_terms_days = serializers.IntegerField(min_value=0, max_value=365, required=False)
    is_active = serializers.BooleanField(required=False)


class InvoiceLineSerializer(serializers.ModelSerializer):
    """Serializer for invoice lines."""
    
    account_code = serializers.CharField(source="account.code", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True)
    tax_code = serializers.CharField(source="tax_code.code", read_only=True)
    tax_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceLine
        fields = [
            "id", "account_id", "account_code", "account_name",
            "description", "quantity", "unit_price", "amount",
            "tax_code_id", "tax_code", "tax_rate", "gst_amount",
            "is_bcrs_deposit", "is_voided"
        ]
        read_only_fields = ["amount", "gst_amount"]
    
    def get_tax_rate(self, obj: InvoiceLine) -> str:
        """Get tax rate as percentage."""
        if obj.tax_code and obj.tax_code.rate is not None:
            return f"{obj.tax_code.rate * 100:.0f}%"
        return "0%"


class InvoiceLineCreateSerializer(serializers.Serializer):
    """Serializer for creating invoice lines."""
    
    account_id = serializers.UUIDField()
    description = serializers.CharField(max_length=500)
    quantity = serializers.DecimalField(max_digits=15, decimal_places=4, default=1)
    unit_price = serializers.DecimalField(max_digits=15, decimal_places=4)
    tax_code_id = serializers.UUIDField()
    is_bcrs_deposit = serializers.BooleanField(default=False)


class InvoiceDocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document list views."""
    
    contact_name = serializers.CharField(source="contact.name", read_only=True)
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceDocument
        fields = [
            "id", "document_type", "document_number",
            "contact_id", "contact_name",
            "issue_date", "due_date", "status", "status_display",
            "total", "currency"
        ]
    
    def get_status_display(self, obj: InvoiceDocument) -> str:
        """Get human-readable status."""
        return obj.status.replace("_", " ").title()


class InvoiceDocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for document views."""
    
    contact = ContactListSerializer(read_only=True)
    lines = InvoiceLineSerializer(many=True, read_only=True)
    status_history = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceDocument
        fields = [
            "id", "document_type", "document_number",
            "contact", "contact_snapshot",
            "issue_date", "due_date",
            "reference", "notes",
            "status", "lines",
            "subtotal", "gst_total", "total", "currency",
            "journal_entry_id", "peppol_status",
            "approved_at", "voided_at",
            "status_history",
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "document_number", "subtotal", "gst_total", "total",
            "created_at", "updated_at"
        ]
    
    def get_status_history(self, obj: InvoiceDocument) -> list:
        """Get status change history."""
        history = []
        if obj.approved_at:
            history.append({
                "status": "APPROVED",
                "date": obj.approved_at.isoformat() if obj.approved_at else None,
                "by": str(obj.approved_by_id) if obj.approved_by_id else None
            })
        if obj.voided_at:
            history.append({
                "status": "VOIDED",
                "date": obj.voided_at.isoformat() if obj.voided_at else None,
                "by": str(obj.voided_by_id) if obj.voided_by_id else None
            })
        return history


class InvoiceDocumentCreateSerializer(serializers.Serializer):
    """Serializer for creating invoice documents."""
    
    document_type = serializers.ChoiceField(choices=["INVOICE", "QUOTE", "CREDIT_NOTE", "DEBIT_NOTE"])
    contact_id = serializers.UUIDField()
    issue_date = serializers.DateField()
    due_date = serializers.DateField(required=False, allow_null=True)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    lines = InvoiceLineCreateSerializer(many=True, min_length=1)


class InvoiceDocumentUpdateSerializer(serializers.Serializer):
    """Serializer for updating documents."""
    
    due_date = serializers.DateField(required=False)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class StatusTransitionSerializer(serializers.Serializer):
    """Serializer for status transitions."""
    
    status = serializers.ChoiceField(choices=[
        "DRAFT", "SENT", "APPROVED", "PAID_PARTIAL", "PAID", "VOIDED"
    ])


class QuoteConversionSerializer(serializers.Serializer):
    """Serializer for quote to invoice conversion."""
    
    quote_id = serializers.UUIDField()


class DocumentSummarySerializer(serializers.Serializer):
    """Serializer for document summary statistics."""
    
    total_count = serializers.IntegerField()
    by_status = serializers.DictField(child=serializers.IntegerField())
    by_type = serializers.DictField(child=serializers.IntegerField())
    total_outstanding = serializers.DecimalField(max_digits=15, decimal_places=2)
    overdue_count = serializers.IntegerField()
