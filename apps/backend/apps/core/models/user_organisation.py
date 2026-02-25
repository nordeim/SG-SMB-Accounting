"""
UserOrganisation model for LedgerSG.

Many-to-many relationship between users and organisations.
Maps to core.user_organisation table.
"""

from django.db import models

from common.models import BaseModel


class UserOrganisation(BaseModel):
    """
    Many-to-many join between users and organisations with role assignment.
    
    Maps to core.user_organisation table.
    """
    
    user = models.ForeignKey(
        "AppUser",
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="organisation_memberships",
    )
    org = models.ForeignKey(
        "Organisation",
        on_delete=models.CASCADE,
        db_column="org_id",
        related_name="user_memberships",
    )
    role = models.ForeignKey(
        "Role",
        on_delete=models.PROTECT,
        db_column="role_id",
        related_name="user_assignments",
    )
    
    # Invitation tracking
    is_default = models.BooleanField(
        default=False,
        db_column="is_default",
        help_text="Default org for this user",
    )
    invited_at = models.DateTimeField(
        auto_now_add=True,
        db_column="invited_at",
    )
    invited_by = models.UUIDField(
        null=True,
        blank=True,
        db_column="invited_by",
    )
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column="accepted_at",
    )
    
    class Meta:
        managed = False
        db_table = 'core"."user_organisation'
        verbose_name = "user organisation"
        verbose_name_plural = "user organisations"
        unique_together = [["user", "org"]]
    
    def __str__(self) -> str:
        return f"{self.user.email} - {self.org.name}"
    
    @property
    def is_pending(self) -> bool:
        """Check if invitation is pending acceptance."""
        return self.accepted_at is None
    
    @property
    def is_active(self) -> bool:
        """Check if membership is active (accepted)."""
        return self.accepted_at is not None
    
    def accept(self):
        """Mark invitation as accepted."""
        from django.utils import timezone
        self.accepted_at = timezone.now()
        self.save()
