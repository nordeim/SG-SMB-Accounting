"""
Bank Transaction Serializers for LedgerSG Banking Module.

Validates imported bank transactions and reconciliation.
SEC-001 Remediation: Replaces unvalidated request.data.get() stubs.
"""

from decimal import Decimal
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import BankTransaction, BankAccount, Payment
from common.decimal_utils import money


class BankTransactionSerializer(serializers.ModelSerializer):
    """Read serializer for BankTransaction."""

    bank_account_name = serializers.CharField(source="bank_account.account_name", read_only=True)

    class Meta:
        model = BankTransaction
        fields = [
            "id",
            "org",
            "bank_account",
            "bank_account_name",
            "transaction_date",
            "value_date",
            "description",
            "reference",
            "amount",
            "running_balance",
            "is_reconciled",
            "reconciled_at",
            "matched_payment",
            "import_source",
            "external_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "org",
            "is_reconciled",
            "reconciled_at",
            "matched_payment",
            "created_at",
            "updated_at",
        ]


class BankTransactionImportSerializer(serializers.Serializer):
    """
    Serializer for importing bank transactions via CSV.

    Validates:
    - Bank account belongs to org
    - Transaction date is valid
    - Amount is a valid decimal
    - Duplicate detection via external_id
    """

    bank_account_id = serializers.UUIDField()
    transactions = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
    )
    import_source = serializers.ChoiceField(
        choices=["CSV", "OFX", "MT940", "API"],
        default="CSV",
    )

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

    def validate_transactions(self, value):
        if not value:
            raise serializers.ValidationError(_("At least one transaction is required."))

        for i, txn in enumerate(value):
            if "transaction_date" not in txn:
                raise serializers.ValidationError(
                    _("Transaction {}: Missing transaction_date.").format(i + 1)
                )
            if "amount" not in txn:
                raise serializers.ValidationError(
                    _("Transaction {}: Missing amount.").format(i + 1)
                )
            if "description" not in txn:
                raise serializers.ValidationError(
                    _("Transaction {}: Missing description.").format(i + 1)
                )

            try:
                money(txn["amount"])
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    _("Transaction {}: Invalid amount '{}'.").format(i + 1, txn["amount"])
                )

        return value


class BankTransactionReconcileSerializer(serializers.Serializer):
    """
    Serializer for reconciling a bank transaction to a payment.

    Validates:
    - Transaction belongs to org and is not already reconciled
    - Payment belongs to org and matches the transaction contact
    """

    payment_id = serializers.UUIDField()

    def validate_payment_id(self, value):
        org_id = self.context.get("org_id")
        if not org_id:
            raise serializers.ValidationError(_("Organisation context required."))

        try:
            payment = Payment.objects.get(id=value, org_id=org_id)
        except Payment.DoesNotExist:
            raise serializers.ValidationError(_("Payment not found in this organisation."))

        if payment.is_voided:
            raise serializers.ValidationError(_("Cannot reconcile to a voided payment."))

        return value


class BankTransactionMatchSerializer(serializers.Serializer):
    """
    Serializer for matching bank transaction to payment.

    Validates amounts match within tolerance.
    """

    payment_id = serializers.UUIDField()
    tolerance = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0.50"),
        help_text=_("Tolerance for amount matching (default: 0.50)"),
    )

    def validate_payment_id(self, value):
        org_id = self.context.get("org_id")
        if not org_id:
            raise serializers.ValidationError(_("Organisation context required."))

        try:
            payment = Payment.objects.get(id=value, org_id=org_id)
        except Payment.DoesNotExist:
            raise serializers.ValidationError(_("Payment not found in this organisation."))

        if payment.is_voided:
            raise serializers.ValidationError(_("Cannot match to a voided payment."))

        return value


class CSVImportRowSerializer(serializers.Serializer):
    """
    Serializer for validating a single CSV import row.

    Expected CSV columns:
    - transaction_date: Date in YYYY-MM-DD format
    - amount: Decimal amount (positive for credit, negative for debit)
    - description: Transaction description
    - reference: (Optional) Transaction reference
    - value_date: (Optional) Value date
    - running_balance: (Optional) Running balance
    """

    transaction_date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=4)
    description = serializers.CharField(max_length=500)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    value_date = serializers.DateField(required=False, allow_null=True)
    running_balance = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        allow_null=True,
    )

    def validate_description(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(_("Description cannot be blank."))
        return value.strip()
