"""
BankTransaction model for LedgerSG.

Maps to banking.bank_transaction table.
Imported bank feed transactions for reconciliation matching.
"""

from django.db import models
from common.models import TenantModel


class BankTransaction(TenantModel):
    """Imported bank feed transaction for reconciliation."""

    IMPORT_SOURCES = [
        ("CSV", "CSV Import"),
        ("OFX", "OFX/QFX"),
        ("MT940", "MT940/SWIFT"),
        ("API", "Bank API"),
    ]

    bank_account = models.ForeignKey(
        "BankAccount",
        on_delete=models.CASCADE,
        db_column="bank_account_id",
        related_name="transactions",
    )

    transaction_date = models.DateField(db_column="transaction_date")
    value_date = models.DateField(null=True, blank=True, db_column="value_date")
    description = models.TextField(db_column="description")
    reference = models.CharField(max_length=100, blank=True, db_column="reference")

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        db_column="amount",
        help_text="Positive = credit (money in), Negative = debit (money out)",
    )
    running_balance = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        db_column="running_balance",
    )

    is_reconciled = models.BooleanField(default=False, db_column="is_reconciled")
    reconciled_at = models.DateTimeField(null=True, blank=True, db_column="reconciled_at")

    matched_payment = models.ForeignKey(
        "Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="matched_payment_id",
        related_name="matched_transactions",
    )
    matched_journal = models.ForeignKey(
        "JournalEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="matched_journal_id",
        related_name="matched_transactions",
    )

    import_batch_id = models.UUIDField(null=True, blank=True, db_column="import_batch_id")
    import_source = models.CharField(
        max_length=50,
        blank=True,
        db_column="import_source",
        choices=IMPORT_SOURCES,
    )
    external_id = models.CharField(
        max_length=100,
        blank=True,
        db_column="external_id",
        help_text="Bank's transaction reference for deduplication",
    )

    class Meta:
        managed = False
        db_table = 'banking"."bank_transaction'
        ordering = ["-transaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["bank_account", "transaction_date"]),
        ]

    def __str__(self):
        sign = "+" if self.amount >= 0 else ""
        return f"{self.transaction_date} | {sign}{self.amount} | {self.description[:50]}"
