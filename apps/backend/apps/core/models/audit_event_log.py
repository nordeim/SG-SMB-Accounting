"""
AuditEventLog model for LedgerSG.

Maps to audit.event_log table.
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField


class AuditEventLog(models.Model):
    """Immutable audit trail for IRAS compliance."""

    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("APPROVE", "Approve"),
        ("VOID", "Void"),
        ("REVERSE", "Reverse"),
        ("FILE", "File"),
        ("SEND", "Send"),
        ("RECONCILE", "Reconcile"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("EXPORT", "Export"),
        ("IMPORT", "Import"),
        ("SETTINGS_CHANGE", "Settings Change"),
    ]

    id = models.BigAutoField(primary_key=True, db_column="id")
    org = models.ForeignKey("Organisation", on_delete=models.CASCADE, db_column="org_id")
    user = models.ForeignKey(
        "AppUser", null=True, blank=True, on_delete=models.SET_NULL, db_column="user_id"
    )
    session_id = models.CharField(max_length=64, blank=True, db_column="session_id")

    action = models.CharField(max_length=30, db_column="action", choices=ACTION_CHOICES)
    entity_schema = models.CharField(max_length=30, db_column="entity_schema")
    entity_table = models.CharField(max_length=50, db_column="entity_table")
    entity_id = models.UUIDField(db_column="entity_id")

    old_data = models.JSONField(null=True, db_column="old_data")
    new_data = models.JSONField(null=True, db_column="new_data")
    changed_fields = ArrayField(
        models.CharField(max_length=100), default=list, blank=True, db_column="changed_fields"
    )

    ip_address = models.GenericIPAddressField(null=True, db_column="ip_address")
    user_agent = models.TextField(blank=True, db_column="user_agent")
    request_path = models.CharField(max_length=500, blank=True, db_column="request_path")

    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at")

    class Meta:
        managed = False
        db_table = 'audit"."event_log'
