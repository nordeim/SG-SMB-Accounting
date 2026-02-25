"""
Abstract base models for LedgerSG.

All models inherit from these base classes to ensure consistency
in primary keys, timestamps, and multi-tenancy.
"""

import uuid
from datetime import datetime

from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamps.
    
    All models in the system inherit from this class.
    Uses unmanaged models since schema is DDL-managed.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="id",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column="created_at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column="updated_at",
    )
    
    class Meta:
        abstract = True
        managed = False  # Schema is DDL-managed
        
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"


class TenantModel(BaseModel):
    """
    Abstract model for all multi-tenant tables.
    
    Adds org_id foreign key to core.organisation.
    All tenant-scoped models inherit from this class.
    
    The org_id is set automatically from the request context via middleware.
    All queries are further filtered by PostgreSQL RLS policies.
    """
    
    org = models.ForeignKey(
        "core.Organisation",
        on_delete=models.CASCADE,
        db_column="org_id",
        editable=False,
        related_name="%(class)s_set",
    )
    
    class Meta:
        abstract = True
        managed = False
        
    def save(self, **kwargs):
        """
        Override save to automatically set org_id from context if not set.
        """
        if not self.org_id:
            from common.middleware.tenant_context import get_current_org_id
            org_id = get_current_org_id()
            if org_id:
                self.org_id = org_id
        super().save(**kwargs)


class ImmutableModel(BaseModel):
    """
    Abstract model for immutable records.
    
    Overrides save() to block updates after initial creation.
    Used for journal entries and audit logs.
    """
    
    class Meta:
        abstract = True
        managed = False
        
    def save(self, force_insert=False, force_update=False, **kwargs):
        """
        Prevent updates to immutable records.
        """
        if self.pk and not force_insert:
            raise ImmutabilityError(
                f"{self.__class__.__name__} is immutable and cannot be updated."
            )
        super().save(force_insert=True, **kwargs)


class ImmutabilityError(Exception):
    """Raised when attempting to modify an immutable record."""
    pass


class SequenceModel(BaseModel):
    """
    Abstract model for tables with auto-numbering sequences.
    
    Provides a hook for sequence generation before save.
    """
    
    sequence_number = models.CharField(
        max_length=50,
        db_column="sequence_number",
        editable=False,
        blank=True,
    )
    
    class Meta:
        abstract = True
        managed = False
        
    def generate_sequence(self) -> str:
        """
        Generate the sequence number for this record.
        
        Subclasses should override this method.
        """
        raise NotImplementedError("Subclasses must implement generate_sequence()")
        
    def save(self, **kwargs):
        """
        Generate sequence number before saving if not set.
        """
        if not self.sequence_number:
            self.sequence_number = self.generate_sequence()
        super().save(**kwargs)
