"""
Payment Serializers for LedgerSG Banking Module.

Validates all payment data before persistence.
SEC-001 Remediation: Replaces unvalidated request.data.get() stubs.
"""

from decimal import Decimal
from uuid import UUID
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from apps.core.models import Payment, BankAccount, Contact, InvoiceDocument
from common.decimal_utils import money


class PaymentSerializer(serializers.ModelSerializer):
    """Read serializer for Payment."""

    contact_name = serializers.CharField(source="contact.name", read_only=True)
    bank_account_name = serializers.CharField(source="bank_account.account_name", read_only=True)
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "org",
            "payment_type",
            "payment_number",
            "payment_date",
            "contact",
            "contact_name",
            "bank_account",
            "bank_account_name",
            "currency",
            "exchange_rate",
            "amount",
            "base_amount",
            "fx_gain_loss",
            "payment_method",
            "payment_method_display",
            "payment_reference",
            "journal_entry",
            "is_reconciled",
            "is_voided",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "org",
            "payment_number",
            "base_amount",
            "fx_gain_loss",
            "journal_entry",
            "is_reconciled",
            "is_voided",
            "created_at",
            "updated_at",
        ]


class PaymentAllocationInputSerializer(serializers.Serializer):
    """Serializer for payment allocation input."""

    document_id = serializers.UUIDField()
    allocated_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        min_value=Decimal("0.0001"),
    )

    def validate_document_id(self, value):
        org_id = self.context.get("org_id")
        if not org_id:
            raise serializers.ValidationError(_("Organisation context required."))

        try:
            document = InvoiceDocument.objects.get(id=value, org_id=org_id)
        except InvoiceDocument.DoesNotExist:
            raise serializers.ValidationError(_("Document not found in this organisation."))

        if document.status != "APPROVED":
            raise serializers.ValidationError(_("Document must be APPROVED before allocation."))

        return value


class PaymentReceiveSerializer(serializers.Serializer):
    """
    Serializer for receiving payments from customers.

    Validates:
    - Contact is a customer (is_customer=True)
    - Bank account belongs to org
    - Allocations don't exceed payment amount
    - Multi-currency exchange rate validation
    """

    contact_id = serializers.UUIDField()
    bank_account_id = serializers.UUIDField()
    payment_date = serializers.DateField()
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        min_value=Decimal("0.0001"),
    )
    currency = serializers.CharField(max_length=3, default="SGD")
    exchange_rate = serializers.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal("1.000000"),
        min_value=Decimal("0.000001"),
    )
    payment_method = serializers.ChoiceField(
        choices=[
            "BANK_TRANSFER",
            "CHEQUE",
            "CASH",
            "PAYNOW",
            "CREDIT_CARD",
            "GIRO",
            "OTHER",
        ]
    )
    payment_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    allocations = PaymentAllocationInputSerializer(many=True, required=False)

    def validate_currency(self, value):
        if not value or len(value) != 3:
            raise serializers.ValidationError(_("Currency must be a 3-letter code."))
        return value.upper()

    def validate_contact_id(self, value):
        org_id = self.context.get("org_id")
        if not org_id:
            raise serializers.ValidationError(_("Organisation context required."))

        try:
            contact = Contact.objects.get(id=value, org_id=org_id)
        except Contact.DoesNotExist:
            raise serializers.ValidationError(_("Contact not found in this organisation."))

        if not contact.is_customer:
            raise serializers.ValidationError(
                _("Contact must be a customer for received payments.")
            )

        return value

    def validate_bank_account_id(self, value):
        org_id = self.context.get("org_id")
        if not org_id:
            raise serializers.ValidationError(_("Organisation context required."))

        try:
            bank_account = BankAccount.objects.get(id=value, org_id=org_id)
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError(_("Bank account not found in this organisation."))

        if not bank_account.is_active:
            raise serializers.ValidationError(_("Bank account is not active."))

        return value

    def validate(self, data):
        allocations = data.get("allocations", [])

        if allocations:
            total_allocated = sum(money(alloc.get("allocated_amount", 0)) for alloc in allocations)
            payment_amount = money(data["amount"])

            if total_allocated > payment_amount:
                raise serializers.ValidationError(
                    {"allocations": _("Total allocations cannot exceed payment amount.")}
                )

            document_ids = [alloc["document_id"] for alloc in allocations]
            if len(document_ids) != len(set(document_ids)):
                raise serializers.ValidationError(
                    {"allocations": _("Cannot allocate to the same document multiple times.")}
                )

        return data


class PaymentMakeSerializer(serializers.Serializer):
    """
    Serializer for making payments to suppliers.

    Validates:
    - Contact is a supplier (is_supplier=True)
    - Bank account belongs to org
    - Allocations don't exceed payment amount
    """

    contact_id = serializers.UUIDField()
    bank_account_id = serializers.UUIDField()
    payment_date = serializers.DateField()
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        min_value=Decimal("0.0001"),
    )
    currency = serializers.CharField(max_length=3, default="SGD")
    exchange_rate = serializers.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal("1.000000"),
        min_value=Decimal("0.000001"),
    )
    payment_method = serializers.ChoiceField(
        choices=[
            "BANK_TRANSFER",
            "CHEQUE",
            "CASH",
            "PAYNOW",
            "CREDIT_CARD",
            "GIRO",
            "OTHER",
        ]
    )
    payment_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    allocations = PaymentAllocationInputSerializer(many=True, required=False)

    def validate_currency(self, value):
        if not value or len(value) != 3:
            raise serializers.ValidationError(_("Currency must be a 3-letter code."))
        return value.upper()

    def validate_contact_id(self, value):
        org_id = self.context.get("org_id")
        if not org_id:
            raise serializers.ValidationError(_("Organisation context required."))

        try:
            contact = Contact.objects.get(id=value, org_id=org_id)
        except Contact.DoesNotExist:
            raise serializers.ValidationError(_("Contact not found in this organisation."))

        if not contact.is_supplier:
            raise serializers.ValidationError(_("Contact must be a supplier for payments made."))

        return value

    def validate_bank_account_id(self, value):
        org_id = self.context.get("org_id")
        if not org_id:
            raise serializers.ValidationError(_("Organisation context required."))

        try:
            bank_account = BankAccount.objects.get(id=value, org_id=org_id)
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError(_("Bank account not found in this organisation."))

        if not bank_account.is_active:
            raise serializers.ValidationError(_("Bank account is not active."))

        return value

    def validate(self, data):
        allocations = data.get("allocations", [])

        if allocations:
            total_allocated = sum(money(alloc.get("allocated_amount", 0)) for alloc in allocations)
            payment_amount = money(data["amount"])

            if total_allocated > payment_amount:
                raise serializers.ValidationError(
                    {"allocations": _("Total allocations cannot exceed payment amount.")}
                )

            document_ids = [alloc["document_id"] for alloc in allocations]
            if len(document_ids) != len(set(document_ids)):
                raise serializers.ValidationError(
                    {"allocations": _("Cannot allocate to the same document multiple times.")}
                )

        return data


class PaymentVoidSerializer(serializers.Serializer):
    """Serializer for voiding a payment."""

    reason = serializers.CharField(max_length=500, required=True)

    def validate_reason(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(_("Void reason cannot be blank."))
        return value.strip()
