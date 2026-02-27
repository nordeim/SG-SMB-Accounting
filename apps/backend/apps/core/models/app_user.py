"""
Custom user model for LedgerSG.

Extends AbstractBaseUser to use email as the username.
Maps to core.app_user table.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

from common.models import BaseModel


class AppUserManager(BaseUserManager):
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
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
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
    password = models.CharField(
        max_length=128,
        db_column="password",
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
    is_staff = models.BooleanField(
        default=False,
        db_column="is_staff",
    )
    is_superuser = models.BooleanField(
        default=False,
        db_column="is_superuser",
    )
    
    # Timestamps (standard Django fields)
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        db_column="last_login",
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        db_column="date_joined",
    )
    password_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column="password_changed_at",
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
    
    def get_organisations(self):
        """Get all organisations the user belongs to."""
        from .user_organisation import UserOrganisation
        return Organisation.objects.filter(
            userorganisation__user=self,
            userorganisation__accepted_at__isnull=False,
        )


# Import here to avoid circular dependency
from .organisation import Organisation
