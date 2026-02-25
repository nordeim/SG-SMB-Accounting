"""
Custom user model for LedgerSG.

Extends AbstractBaseUser to use email as the username.
Maps to core.app_user table.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from common.models import BaseModel


class AppUserManager(models.Manager):
    """Custom manager for AppUser."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superadmin", True)
        return self.create_user(email, password, **extra_fields)


class AppUser(AbstractBaseUser, BaseModel):
    """
    Custom user model with email as username.
    
    Maps to core.app_user table.
    """
    
    email = models.EmailField(
        unique=True,
        db_column="email",
        verbose_name="email address",
    )
    full_name = models.CharField(
        max_length=255,
        db_column="full_name",
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        db_column="phone",
    )
    
    # Status flags
    is_active = models.BooleanField(
        default=True,
        db_column="is_active",
    )
    is_superadmin = models.BooleanField(
        default=False,
        db_column="is_superadmin",
    )
    
    # Timestamps (override BaseModel to match schema)
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        db_column="last_login",
    )
    
    objects = AppUserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]
    
    class Meta:
        managed = False
        db_table = 'core"."app_user'
        verbose_name = "user"
        verbose_name_plural = "users"
    
    def __str__(self) -> str:
        return self.email
    
    @property
    def is_staff(self) -> bool:
        """Required for Django admin access."""
        return self.is_superadmin
    
    @property
    def is_superuser(self) -> bool:
        """Required for Django permissions."""
        return self.is_superadmin
    
    def get_organisations(self):
        """Get all organisations the user belongs to."""
        from .user_organisation import UserOrganisation
        return Organisation.objects.filter(
            userorganisation__user=self,
            userorganisation__accepted_at__isnull=False,
        )


# Import here to avoid circular dependency
from .organisation import Organisation
