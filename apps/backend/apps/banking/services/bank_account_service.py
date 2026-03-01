"""
BankAccount Service for LedgerSG Banking Module.

Business logic for bank account CRUD operations.
SEC-001 Remediation: All operations validated and logged.
"""

from uuid import UUID
from typing import List, Optional, Dict, Any
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.core.models import BankAccount, Account, AuditEventLog
from common.exceptions import ValidationError, ResourceNotFound, DuplicateResource
from common.decimal_utils import money


class BankAccountService:
    """Service class for bank account operations."""

    @staticmethod
    @transaction.atomic()
    def create(
        org_id: UUID,
        data: dict,
        user_id: Optional[UUID] = None,
    ) -> BankAccount:
        """
        Create a new bank account with GL linkage.

        Args:
            org_id: Organisation UUID
            data: Validated serializer data
            user_id: Creating user ID (for audit)

        Returns:
            Created BankAccount instance

        Raises:
            ValidationError: If validation fails
            DuplicateResource: If account_number already exists
        """
        existing = BankAccount.objects.filter(
            org_id=org_id,
            account_number=data["account_number"],
        ).first()

        if existing:
            raise DuplicateResource(
                f"Bank account with number '{data['account_number']}' already exists."
            )

        gl_account_id = data.get("gl_account")
        if gl_account_id:
            try:
                gl_account = Account.objects.get(id=gl_account_id.id, org_id=org_id)
            except Account.DoesNotExist:
                raise ValidationError("GL account not found in this organisation.")
        else:
            gl_account = None

        if data.get("is_default"):
            BankAccount.objects.filter(org_id=org_id, is_default=True).update(is_default=False)

        bank_account = BankAccount.objects.create(
            org_id=org_id,
            account_name=data["account_name"],
            bank_name=data["bank_name"],
            account_number=data["account_number"],
            bank_code=data.get("bank_code", ""),
            branch_code=data.get("branch_code", ""),
            currency=data.get("currency", "SGD"),
            gl_account=gl_account,
            paynow_type=data.get("paynow_type") or None,
            paynow_id=data.get("paynow_id") or None,
            is_default=data.get("is_default", False),
            is_active=True,
            opening_balance=money(data.get("opening_balance", 0)),
            opening_balance_date=data.get("opening_balance_date"),
        )

        AuditEventLog.objects.create(
            org_id=org_id,
            user_id=user_id,
            action="CREATE",
            entity_schema="banking",
            entity_table="bank_account",
            entity_id=bank_account.id,
            new_data={
                "account_name": bank_account.account_name,
                "account_number": bank_account.account_number,
                "bank_name": bank_account.bank_name,
                "currency": bank_account.currency,
            },
        )

        return bank_account

    @staticmethod
    def list(
        org_id: UUID,
        is_active: Optional[bool] = None,
        currency: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[BankAccount]:
        """
        List bank accounts for an organisation.

        Args:
            org_id: Organisation UUID
            is_active: Filter by active status
            currency: Filter by currency
            search: Search in account_name, bank_name, account_number

        Returns:
            List of BankAccount instances
        """
        queryset = BankAccount.objects.filter(org_id=org_id)

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        if currency:
            queryset = queryset.filter(currency=currency.upper())

        if search:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(account_name__icontains=search)
                | Q(bank_name__icontains=search)
                | Q(account_number__icontains=search)
            )

        return list(queryset.order_by("-is_default", "account_name"))

    @staticmethod
    def get(org_id: UUID, account_id: UUID) -> BankAccount:
        """
        Get a single bank account.

        Args:
            org_id: Organisation UUID
            account_id: Bank Account UUID

        Returns:
            BankAccount instance

        Raises:
            ResourceNotFound: If not found
        """
        try:
            return BankAccount.objects.get(id=account_id, org_id=org_id)
        except BankAccount.DoesNotExist:
            raise ResourceNotFound(f"Bank account {account_id} not found")

    @staticmethod
    @transaction.atomic()
    def update(
        org_id: UUID,
        account_id: UUID,
        data: dict,
        user_id: Optional[UUID] = None,
    ) -> BankAccount:
        """
        Update a bank account.

        Args:
            org_id: Organisation UUID
            account_id: Bank Account UUID
            data: Validated serializer data
            user_id: Updating user ID

        Returns:
            Updated BankAccount instance

        Raises:
            ResourceNotFound: If not found
            ValidationError: If validation fails
        """
        bank_account = BankAccountService.get(org_id, account_id)

        old_data = {
            "account_name": bank_account.account_name,
            "bank_name": bank_account.bank_name,
            "is_default": bank_account.is_default,
            "is_active": bank_account.is_active,
        }

        if data.get("is_default") and not bank_account.is_default:
            BankAccount.objects.filter(org_id=org_id, is_default=True).update(is_default=False)

        allowed_fields = [
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

        for field in allowed_fields:
            if field in data:
                setattr(bank_account, field, data[field])

        bank_account.save()

        AuditEventLog.objects.create(
            org_id=org_id,
            user_id=user_id,
            action="UPDATE",
            entity_schema="banking",
            entity_table="bank_account",
            entity_id=bank_account.id,
            old_data=old_data,
            new_data={
                "account_name": bank_account.account_name,
                "bank_name": bank_account.bank_name,
                "is_default": bank_account.is_default,
                "is_active": bank_account.is_active,
            },
        )

        return bank_account

    @staticmethod
    @transaction.atomic()
    def deactivate(
        org_id: UUID,
        account_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> BankAccount:
        """
        Deactivate a bank account (soft delete).

        Args:
            org_id: Organisation UUID
            account_id: Bank Account UUID
            user_id: Deactivating user ID

        Returns:
            Deactivated BankAccount instance

        Raises:
            ResourceNotFound: If not found
            ValidationError: If account is the only active one
        """
        bank_account = BankAccountService.get(org_id, account_id)

        active_count = BankAccount.objects.filter(org_id=org_id, is_active=True).count()
        if active_count == 1 and bank_account.is_active:
            raise ValidationError(
                "Cannot deactivate the only active bank account. "
                "Please create another bank account first."
            )

        bank_account.is_active = False
        bank_account.is_default = False
        bank_account.save()

        AuditEventLog.objects.create(
            org_id=org_id,
            user_id=user_id,
            action="UPDATE",
            entity_schema="banking",
            entity_table="bank_account",
            entity_id=bank_account.id,
            old_data={"is_active": True, "is_default": bank_account.is_default},
            new_data={"is_active": False, "is_default": False},
        )

        return bank_account

    @staticmethod
    @transaction.atomic()
    def set_default(
        org_id: UUID,
        account_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> BankAccount:
        """
        Set a bank account as the default.

        Args:
            org_id: Organisation UUID
            account_id: Bank Account UUID
            user_id: User ID

        Returns:
            Updated BankAccount instance
        """
        bank_account = BankAccountService.get(org_id, account_id)

        if not bank_account.is_active:
            raise ValidationError("Cannot set inactive bank account as default.")

        BankAccount.objects.filter(org_id=org_id, is_default=True).update(is_default=False)

        bank_account.is_default = True
        bank_account.save()

        AuditEventLog.objects.create(
            org_id=org_id,
            user_id=user_id,
            action="UPDATE",
            entity_schema="banking",
            entity_table="bank_account",
            entity_id=bank_account.id,
            old_data={"is_default": False},
            new_data={"is_default": True},
        )

        return bank_account
