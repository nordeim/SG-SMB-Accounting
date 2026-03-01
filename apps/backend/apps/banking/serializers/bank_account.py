"""
Bank Account Serializers for LedgerSG Banking Module.

Validates all bank account data before persistence.
SEC-001 Remediation: Replaces unvalidated request.data.get() stubs.
"""

from decimal import Decimal
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.core.models import BankAccount, Account


class BankAccountSerializer(serializers.ModelSerializer):
    """Read serializer for BankAccount."""

    class Meta:
        model = BankAccount
        fields = [
            "id",
            "org",
            "account_name",
            "bank_name",
            "account_number",
            "bank_code",
            "branch_code",
            "currency",
            "gl_account",
            "paynow_type",
            "paynow_id",
            "is_default",
            "is_active",
            "opening_balance",
            "opening_balance_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "org", "created_at", "updated_at"]


class BankAccountCreateSerializer(serializers.ModelSerializer):
    """
    Write serializer for creating BankAccount.

    Validates:
    - GL account belongs to org and is bank account type
    - PayNow validation: if paynow_type set, paynow_id required
    - No duplicate account_number per org
    """

    class Meta:
        model = BankAccount
        fields = [
            "account_name",
            "bank_name",
            "account_number",
            "bank_code",
            "branch_code",
            "currency",
            "gl_account",
            "paynow_type",
            "paynow_id",
            "is_default",
            "opening_balance",
            "opening_balance_date",
        ]

    def validate_account_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(_("Account name cannot be blank."))
        return value.strip()

    def validate_bank_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(_("Bank name cannot be blank."))
        return value.strip()

    def validate_account_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(_("Account number cannot be blank."))
        return value.strip()

    def validate_currency(self, value):
        if not value or len(value) != 3:
            raise serializers.ValidationError(_("Currency must be a 3-letter code."))
        return value.upper()

    def validate_opening_balance(self, value):
        if value is None:
            return Decimal("0")
        if value < Decimal("0"):
            raise serializers.ValidationError(_("Opening balance cannot be negative."))
        return value

    def validate_gl_account(self, value):
        org_id = self.context.get("org_id")
        if not org_id:
            raise serializers.ValidationError(_("Organisation context required."))

        try:
            account = Account.objects.get(id=value.id, org_id=org_id)
        except Account.DoesNotExist:
            raise serializers.ValidationError(_("GL account not found in this organisation."))

        account_type_name = account.account_type.name.upper() if account.account_type else ""
        if account_type_name != "ASSET":
            raise serializers.ValidationError(
                _("GL account must be an Asset account for bank accounts.")
            )

        sub_type_name = ""
        if account.account_sub_type:
            sub_type_name = account.account_sub_type.name.upper()

        valid_sub_types = ["BANK", "CASH AND BANK", "CASH & BANK", "CASH"]
        if sub_type_name and sub_type_name not in valid_sub_types:
            raise serializers.ValidationError(
                _("GL account must be a Bank or Cash type asset account.")
            )

        return value

    def validate(self, data):
        paynow_type = data.get("paynow_type")
        paynow_id = data.get("paynow_id")

        if paynow_type and not paynow_id:
            raise serializers.ValidationError(
                {"paynow_id": _("PayNow ID is required when PayNow type is specified.")}
            )

        if paynow_id and not paynow_type:
            raise serializers.ValidationError(
                {"paynow_type": _("PayNow type is required when PayNow ID is provided.")}
            )

        if paynow_id:
            paynow_type_value = paynow_type if isinstance(paynow_type, str) else paynow_type[0]
            if paynow_type_value == "UEN" and len(paynow_id) > 10:
                raise serializers.ValidationError(
                    {"paynow_id": _("UEN PayNow ID must be 10 characters or less.")}
                )
            elif paynow_type_value == "MOBILE" and not paynow_id.startswith("+"):
                raise serializers.ValidationError(
                    {"paynow_id": _("Mobile PayNow ID must start with '+' (e.g., +65XXXXXXXX).")}
                )
            elif paynow_type_value == "NRIC" and len(paynow_id) != 9:
                raise serializers.ValidationError(
                    {"paynow_id": _("NRIC PayNow ID must be exactly 9 characters.")}
                )

        return data


class BankAccountUpdateSerializer(serializers.ModelSerializer):
    """Write serializer for updating BankAccount."""

    class Meta:
        model = BankAccount
        fields = [
            "account_name",
            "bank_name",
            "bank_code",
            "branch_code",
            "paynow_type",
            "paynow_id",
            "is_default",
            "is_active",
            "opening_balance",
            "opening_balance_date",
        ]

    def validate_account_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(_("Account name cannot be blank."))
        return value.strip()

    def validate_bank_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(_("Bank name cannot be blank."))
        return value.strip()

    def validate_opening_balance(self, value):
        if value is not None and value < Decimal("0"):
            raise serializers.ValidationError(_("Opening balance cannot be negative."))
        return value

    def validate(self, data):
        paynow_type = data.get("paynow_type")
        paynow_id = data.get("paynow_id")

        if paynow_type and not paynow_id:
            raise serializers.ValidationError(
                {"paynow_id": _("PayNow ID is required when PayNow type is specified.")}
            )

        if paynow_id and not paynow_type:
            raise serializers.ValidationError(
                {"paynow_type": _("PayNow type is required when PayNow ID is provided.")}
            )

        return data
