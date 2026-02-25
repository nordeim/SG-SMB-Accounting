"""
Contact model for LedgerSG.

Maps to invoicing.contact table.
"""

from django.db import models
from common.models import TenantModel


class Contact(TenantModel):
    """Contact model for customers and suppliers."""
    
    name = models.CharField(max_length=255, db_column="name")
    company_name = models.CharField(
        max_length=255, blank=True,
        db_column="company_name"
    )
    email = models.EmailField(blank=True, db_column="email")
    phone = models.CharField(max_length=50, blank=True, db_column="phone")
    is_customer = models.BooleanField(default=False, db_column="is_customer")
    is_supplier = models.BooleanField(default=False, db_column="is_supplier")
    payment_terms_days = models.IntegerField(
        default=30, db_column="payment_terms_days"
    )
    is_active = models.BooleanField(default=True, db_column="is_active")
    
    class Meta:
        managed = False
        db_table = 'invoicing"."contact'
