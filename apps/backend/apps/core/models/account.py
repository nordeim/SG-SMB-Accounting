"""
Account model for LedgerSG Chart of Accounts.

Maps to coa.account table.
"""

from django.db import models
from common.models import TenantModel


class Account(TenantModel):
    """Chart of Accounts model."""
    
    code = models.CharField(max_length=20, db_column="code")
    name = models.CharField(max_length=255, db_column="name")
    account_type = models.CharField(max_length=50, db_column="account_type")
    parent = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL,
        db_column="parent_id"
    )
    is_system = models.BooleanField(default=False, db_column="is_system")
    is_active = models.BooleanField(default=True, db_column="is_active")
    
    class Meta:
        managed = False
        db_table = 'coa"."account'
        unique_together = [["org", "code"]]
