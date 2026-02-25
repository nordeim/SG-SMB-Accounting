"""
Role model for LedgerSG.

Defines permission roles within an organisation.
Maps to core.role table.
"""

from django.db import models

from common.models import BaseModel, TenantModel


class Role(BaseModel, TenantModel):
    """
    Role model for RBAC (Role-Based Access Control).
    
    Maps to core.role table.
    Each role has granular permission flags.
    """
    
    # Role name
    name = models.CharField(
        max_length=100,
        db_column="name",
    )
    description = models.TextField(
        blank=True,
        db_column="description",
    )
    
    # Permission flags
    can_manage_org = models.BooleanField(
        default=False,
        db_column="can_manage_org",
        help_text="Can modify organisation settings",
    )
    can_manage_users = models.BooleanField(
        default=False,
        db_column="can_manage_users",
        help_text="Can invite and manage users",
    )
    can_manage_coa = models.BooleanField(
        default=False,
        db_column="can_manage_coa",
        help_text="Can modify Chart of Accounts",
    )
    can_create_invoices = models.BooleanField(
        default=True,
        db_column="can_create_invoices",
        help_text="Can create and edit draft invoices",
    )
    can_approve_invoices = models.BooleanField(
        default=False,
        db_column="can_approve_invoices",
        help_text="Can approve invoices (creates journal entries)",
    )
    can_void_invoices = models.BooleanField(
        default=False,
        db_column="can_void_invoices",
        help_text="Can void approved invoices",
    )
    can_create_journals = models.BooleanField(
        default=False,
        db_column="can_create_journals",
        help_text="Can create manual journal entries",
    )
    can_manage_banking = models.BooleanField(
        default=False,
        db_column="can_manage_banking",
        help_text="Can manage bank accounts and reconciliation",
    )
    can_file_gst = models.BooleanField(
        default=False,
        db_column="can_file_gst",
        help_text="Can file GST returns",
    )
    can_view_reports = models.BooleanField(
        default=True,
        db_column="can_view_reports",
        help_text="Can view financial reports",
    )
    can_export_data = models.BooleanField(
        default=False,
        db_column="can_export_data",
        help_text="Can export data (CSV, Excel, PDF)",
    )
    
    # System roles cannot be deleted or modified
    is_system = models.BooleanField(
        default=False,
        db_column="is_system",
    )
    
    # Soft delete
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column="deleted_at",
    )
    
    class Meta:
        managed = False
        db_table = 'core"."role'
        verbose_name = "role"
        verbose_name_plural = "roles"
        unique_together = [["org", "name"]]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.org.name})"
    
    @classmethod
    def get_system_roles(cls):
        """Return system role definitions."""
        return {
            "OWNER": {
                "name": "Owner",
                "description": "Full access to the organisation",
                "permissions": {
                    "can_manage_org": True,
                    "can_manage_users": True,
                    "can_manage_coa": True,
                    "can_create_invoices": True,
                    "can_approve_invoices": True,
                    "can_void_invoices": True,
                    "can_create_journals": True,
                    "can_manage_banking": True,
                    "can_file_gst": True,
                    "can_view_reports": True,
                    "can_export_data": True,
                },
            },
            "ADMIN": {
                "name": "Admin",
                "description": "Administrative access",
                "permissions": {
                    "can_manage_org": True,
                    "can_manage_users": True,
                    "can_manage_coa": True,
                    "can_create_invoices": True,
                    "can_approve_invoices": True,
                    "can_void_invoices": True,
                    "can_create_journals": True,
                    "can_manage_banking": True,
                    "can_file_gst": True,
                    "can_view_reports": True,
                    "can_export_data": True,
                },
            },
            "ACCOUNTANT": {
                "name": "Accountant",
                "description": "Can manage books and file GST",
                "permissions": {
                    "can_manage_org": False,
                    "can_manage_users": False,
                    "can_manage_coa": True,
                    "can_create_invoices": True,
                    "can_approve_invoices": True,
                    "can_void_invoices": True,
                    "can_create_journals": True,
                    "can_manage_banking": True,
                    "can_file_gst": True,
                    "can_view_reports": True,
                    "can_export_data": True,
                },
            },
            "VIEWER": {
                "name": "Viewer",
                "description": "Read-only access",
                "permissions": {
                    "can_manage_org": False,
                    "can_manage_users": False,
                    "can_manage_coa": False,
                    "can_create_invoices": False,
                    "can_approve_invoices": False,
                    "can_void_invoices": False,
                    "can_create_journals": False,
                    "can_manage_banking": False,
                    "can_file_gst": False,
                    "can_view_reports": True,
                    "can_export_data": False,
                },
            },
        }
