"""
Bank Transaction / Reconciliation Service for LedgerSG Banking Module.

Business logic for bank statement imports and reconciliation.
SEC-001 Remediation: All operations validated and logged.
"""

from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date, datetime
from django.db import transaction
from django.utils import timezone
import csv
import io

from apps.core.models import (
    BankTransaction,
    BankAccount,
    Payment,
    AuditEventLog,
)
from common.exceptions import ValidationError, ResourceNotFound, DuplicateResource
from common.decimal_utils import money


class ReconciliationService:
    """Service class for bank transaction and reconciliation operations."""

    @staticmethod
    def list_transactions(
        org_id: UUID,
        bank_account_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        is_reconciled: Optional[bool] = None,
        unreconciled_only: bool = False,
    ) -> List[BankTransaction]:
        """
        List bank transactions with optional filters.

        Args:
            org_id: Organisation UUID
            bank_account_id: Filter by bank account
            date_from: Filter from date
            date_to: Filter to date
            is_reconciled: Filter by reconciliation status
            unreconciled_only: Show only unreconciled transactions

        Returns:
            List of BankTransaction instances
        """
        queryset = BankTransaction.objects.filter(org_id=org_id)

        if bank_account_id:
            queryset = queryset.filter(bank_account_id=bank_account_id)

        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)

        if is_reconciled is not None:
            queryset = queryset.filter(is_reconciled=is_reconciled)

        if unreconciled_only:
            queryset = queryset.filter(is_reconciled=False)

        return list(queryset.order_by("-transaction_date", "-created_at"))

    @staticmethod
    def get_transaction(org_id: UUID, transaction_id: UUID) -> BankTransaction:
        """
        Get a single bank transaction.

        Args:
            org_id: Organisation UUID
            transaction_id: BankTransaction UUID

        Returns:
            BankTransaction instance

        Raises:
            ResourceNotFound: If not found
        """
        try:
            return BankTransaction.objects.get(id=transaction_id, org_id=org_id)
        except BankTransaction.DoesNotExist:
            raise ResourceNotFound(f"Bank transaction {transaction_id} not found")

    @staticmethod
    @transaction.atomic()
    def import_csv(
        org_id: UUID,
        bank_account_id: UUID,
        csv_file,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Import bank transactions from a CSV file.

        Expected CSV columns:
        - transaction_date (YYYY-MM-DD)
        - amount (decimal, positive for credit, negative for debit)
        - description
        - reference (optional)
        - value_date (optional)
        - running_balance (optional)

        Args:
            org_id: Organisation UUID
            bank_account_id: Bank Account UUID
            csv_file: CSV file object
            user_id: Importing user ID

        Returns:
            Dict with import results: {'imported': int, 'skipped': int, 'errors': list}
        """
        bank_account = BankAccount.objects.get(id=bank_account_id, org_id=org_id)
        if not bank_account.is_active:
            raise ValidationError("Bank account is not active.")

        batch_id = uuid4()
        imported = 0
        skipped = 0
        errors = []

        try:
            decoded_file = csv_file.read().decode("utf-8")
        except UnicodeDecodeError:
            try:
                decoded_file = csv_file.read().decode("latin-1")
            except Exception as e:
                raise ValidationError(f"Could not decode file: {e}")

        reader = csv.DictReader(io.StringIO(decoded_file))

        for row_num, row in enumerate(reader, start=2):
            try:
                transaction_date = row.get("transaction_date") or row.get("date")
                if not transaction_date:
                    errors.append(f"Row {row_num}: Missing transaction_date")
                    skipped += 1
                    continue

                amount_str = row.get("amount") or row.get("txn_amount")
                if not amount_str:
                    errors.append(f"Row {row_num}: Missing amount")
                    skipped += 1
                    continue

                description = row.get("description") or row.get("narration") or ""
                if not description:
                    errors.append(f"Row {row_num}: Missing description")
                    skipped += 1
                    continue

                try:
                    from datetime import datetime as dt

                    transaction_date_parsed = dt.strptime(
                        transaction_date.strip(), "%Y-%m-%d"
                    ).date()
                except ValueError:
                    try:
                        transaction_date_parsed = dt.strptime(
                            transaction_date.strip(), "%d/%m/%Y"
                        ).date()
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid date format '{transaction_date}'")
                        skipped += 1
                        continue

                try:
                    amount = money(amount_str.replace(",", "").strip())
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid amount '{amount_str}'")
                    skipped += 1
                    continue

                reference = row.get("reference", "").strip()
                external_id = (
                    row.get("external_id") or row.get("txn_id") or row.get("reference_number") or ""
                )

                existing = BankTransaction.objects.filter(
                    bank_account=bank_account,
                    transaction_date=transaction_date_parsed,
                    amount=amount,
                    description=description[:500],
                ).first()

                if existing:
                    skipped += 1
                    continue

                value_date = None
                value_date_str = row.get("value_date")
                if value_date_str:
                    try:
                        value_date = dt.strptime(value_date_str.strip(), "%Y-%m-%d").date()
                    except ValueError:
                        pass

                running_balance = None
                running_balance_str = row.get("running_balance") or row.get("balance")
                if running_balance_str:
                    try:
                        running_balance = money(running_balance_str.replace(",", "").strip())
                    except ValueError:
                        pass

                BankTransaction.objects.create(
                    org_id=org_id,
                    bank_account=bank_account,
                    transaction_date=transaction_date_parsed,
                    value_date=value_date,
                    description=description[:500],
                    reference=reference[:100],
                    amount=amount,
                    running_balance=running_balance,
                    is_reconciled=False,
                    import_batch_id=batch_id,
                    import_source="CSV",
                    external_id=external_id[:100],
                )
                imported += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                skipped += 1

        AuditEventLog.objects.create(
            org_id=org_id,
            user_id=user_id,
            action="IMPORT",
            entity_schema="banking",
            entity_table="bank_transaction",
            entity_id=batch_id,
            new_data={
                "bank_account_id": str(bank_account_id),
                "imported": imported,
                "skipped": skipped,
                "import_source": "CSV",
            },
        )

        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors[:20],
            "batch_id": str(batch_id),
        }

    @staticmethod
    @transaction.atomic()
    def reconcile(
        org_id: UUID,
        transaction_id: UUID,
        payment_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> BankTransaction:
        """
        Reconcile a bank transaction to a payment.

        Args:
            org_id: Organisation UUID
            transaction_id: BankTransaction UUID
            payment_id: Payment UUID
            user_id: Reconciling user ID

        Returns:
            Updated BankTransaction instance

        Raises:
            ValidationError: If validation fails
        """
        transaction_obj = ReconciliationService.get_transaction(org_id, transaction_id)

        if transaction_obj.is_reconciled:
            raise ValidationError("Transaction is already reconciled.")

        try:
            payment = Payment.objects.get(id=payment_id, org_id=org_id)
        except Payment.DoesNotExist:
            raise ResourceNotFound(f"Payment {payment_id} not found")

        if payment.is_voided:
            raise ValidationError("Cannot reconcile to a voided payment.")

        if payment.bank_account_id != transaction_obj.bank_account_id:
            raise ValidationError("Payment bank account does not match transaction bank account.")

        tolerance = Decimal("1.00")
        if abs(transaction_obj.amount - payment.amount) > tolerance:
            raise ValidationError(
                f"Amount mismatch: Transaction ({transaction_obj.amount}) vs "
                f"Payment ({payment.amount}). Difference exceeds tolerance ({tolerance})."
            )

        transaction_obj.is_reconciled = True
        transaction_obj.reconciled_at = timezone.now()
        transaction_obj.matched_payment = payment
        transaction_obj.save()

        payment.is_reconciled = True
        payment.save()

        AuditEventLog.objects.create(
            org_id=org_id,
            user_id=user_id,
            action="RECONCILE",
            entity_schema="banking",
            entity_table="bank_transaction",
            entity_id=transaction_obj.id,
            old_data={"is_reconciled": False},
            new_data={
                "is_reconciled": True,
                "payment_id": str(payment_id),
                "payment_number": payment.payment_number,
            },
        )

        return transaction_obj

    @staticmethod
    @transaction.atomic()
    def unreconcile(
        org_id: UUID,
        transaction_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> BankTransaction:
        """
        Remove reconciliation from a bank transaction.

        Args:
            org_id: Organisation UUID
            transaction_id: BankTransaction UUID
            user_id: User ID

        Returns:
            Updated BankTransaction instance
        """
        transaction_obj = ReconciliationService.get_transaction(org_id, transaction_id)

        if not transaction_obj.is_reconciled:
            raise ValidationError("Transaction is not reconciled.")

        old_payment_id = transaction_obj.matched_payment_id

        transaction_obj.is_reconciled = False
        transaction_obj.reconciled_at = None
        transaction_obj.matched_payment = None
        transaction_obj.save()

        if old_payment_id:
            Payment.objects.filter(id=old_payment_id).update(is_reconciled=False)

        AuditEventLog.objects.create(
            org_id=org_id,
            user_id=user_id,
            action="DELETE",
            entity_schema="banking",
            entity_table="bank_transaction",
            entity_id=transaction_obj.id,
            old_data={"is_reconciled": True, "payment_id": str(old_payment_id)},
            new_data={"is_reconciled": False},
        )

        return transaction_obj

    @staticmethod
    def suggest_matches(
        org_id: UUID,
        transaction_id: UUID,
        tolerance: Decimal = Decimal("1.00"),
    ) -> List[Dict[str, Any]]:
        """
        Suggest payment matches for a bank transaction.

        Args:
            org_id: Organisation UUID
            transaction_id: BankTransaction UUID
            tolerance: Amount tolerance for matching

        Returns:
            List of suggested payment matches with scores
        """
        transaction_obj = ReconciliationService.get_transaction(org_id, transaction_id)

        if transaction_obj.is_reconciled:
            return []

        candidates = Payment.objects.filter(
            org_id=org_id,
            bank_account_id=transaction_obj.bank_account_id,
            is_voided=False,
            is_reconciled=False,
        )

        suggestions = []
        for payment in candidates:
            amount_diff = abs(transaction_obj.amount - payment.amount)

            if amount_diff <= tolerance:
                suggestions.append(
                    {
                        "payment_id": str(payment.id),
                        "payment_number": payment.payment_number,
                        "payment_date": payment.payment_date.isoformat(),
                        "amount": str(payment.amount),
                        "contact": payment.contact.name if payment.contact else None,
                        "amount_difference": str(amount_diff),
                        "score": 100 - int(amount_diff * 10),
                    }
                )

        suggestions.sort(key=lambda x: x["score"], reverse=True)

        return suggestions[:10]
