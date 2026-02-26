"""
Organisation service for LedgerSG.

Handles organisation lifecycle management including:
- Organisation creation with CoA seeding
- Organisation updates
- GST registration toggle
- Fiscal year management
"""

import uuid
from typing import Optional
from datetime import date, timedelta

from django.db import connection, transaction

from apps.core.models import (
    Organisation, 
    AppUser, 
    Role, 
    UserOrganisation,
    FiscalYear,
    FiscalPeriod,
)
from common.exceptions import ValidationError, DuplicateResource


def create_organisation(
    user: AppUser,
    name: str,
    legal_name: str = "",
    uen: str = "",
    entity_type: str = "",
    gst_registered: bool = False,
    gst_reg_number: str = "",
    gst_reg_date: Optional[date] = None,
    fy_start_month: int = 1,
    base_currency: str = "SGD",
    **kwargs
) -> Organisation:
    """
    Create a new organisation with full setup.
    
    This function:
    1. Creates the organisation
    2. Seeds the Chart of Accounts via PostgreSQL function
    3. Creates document sequences
    4. Creates the first fiscal year with periods
    5. Assigns the user as Owner
    
    Args:
        user: The user creating the organisation (becomes Owner)
        name: Organisation name
        legal_name: Legal name (optional)
        uen: UEN (optional)
        entity_type: Entity type (optional)
        gst_registered: Whether GST registered
        gst_reg_number: GST registration number
        gst_reg_date: GST registration date
        fy_start_month: Fiscal year start month (1-12)
        base_currency: Base currency code
        **kwargs: Additional organisation fields
        
    Returns:
        Created Organisation instance
    """
    # Set default entity_type if empty
    if not entity_type:
        entity_type = "PRIVATE_LIMITED"
    
    with transaction.atomic():
        # Create organisation
        org = Organisation.objects.create(
            name=name,
            legal_name=legal_name or name,
            uen=uen,
            entity_type=entity_type,
            gst_registered=gst_registered,
            gst_reg_number=gst_reg_number,
            gst_reg_date=gst_reg_date,
            fy_start_month=fy_start_month,
            base_currency=base_currency,
            **kwargs
        )
        
        # Seed Chart of Accounts via PostgreSQL function (includes document sequences)
        _seed_chart_of_accounts(org.id, gst_registered)
        
        # Create first fiscal year
        _create_first_fiscal_year(org, fy_start_month)
        
        # Assign user as Owner
        _assign_owner_role(org, user)
        
    return org


def _seed_chart_of_accounts(org_id: uuid.UUID, gst_registered: bool) -> None:
    """
    Seed default Chart of Accounts via PostgreSQL function.
    
    Args:
        org_id: Organisation ID
        gst_registered: Whether GST is registered
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT core.seed_default_chart_of_accounts(%s, %s)",
            [str(org_id), gst_registered]
        )


def _create_document_sequences(org_id: uuid.UUID) -> None:
    """
    Create document sequences for the organisation.
    
    Args:
        org_id: Organisation ID
    """
    sequences = [
        ("INVOICE", "INV", 1),
        ("CREDIT_NOTE", "CN", 1),
        ("DEBIT_NOTE", "DN", 1),
        ("PURCHASE_ORDER", "PO", 1),
        ("QUOTE", "QUO", 1),
        ("JOURNAL_ENTRY", "JE", 1),
    ]
    
    with connection.cursor() as cursor:
        for doc_type, prefix, start_num in sequences:
            cursor.execute(
                """
                INSERT INTO core.document_sequence (
                    id, org_id, document_type, prefix, next_number, 
                    padding, fiscal_year_reset, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), %s, %s, %s, %s, 5, false, NOW(), NOW()
                )
                """,
                [str(org_id), doc_type, prefix, start_num]
            )


def _create_first_fiscal_year(org: Organisation, start_month: int) -> None:
    """
    Create the first fiscal year with periods.
    
    Args:
        org: Organisation instance
        start_month: Fiscal year start month (1-12)
    """
    current_year = date.today().year
    
    # Calculate fiscal year dates
    if start_month == 1:
        # Calendar year
        start_date = date(current_year, 1, 1)
        end_date = date(current_year, 12, 31)
        label = f"FY{current_year}"
    else:
        # Non-calendar year (e.g., Apr-Mar)
        start_date = date(current_year, start_month, 1)
        end_date = date(current_year + 1, start_month, 1) - timedelta(days=1)
        label = f"FY{current_year}-{current_year + 1}"
    
    # Create fiscal year
    fiscal_year = FiscalYear.objects.create(
        org=org,
        label=label,
        start_date=start_date,
        end_date=end_date,
        is_closed=False,
    )
    
    # Create fiscal periods (months)
    _create_fiscal_periods(org, fiscal_year, start_date, end_date)


def _create_fiscal_periods(
    org: Organisation,
    fiscal_year: FiscalYear,
    start_date: date,
    end_date: date
) -> None:
    """
    Create fiscal periods (months) for a fiscal year.
    
    Args:
        org: Organisation instance
        fiscal_year: FiscalYear instance
        start_date: Year start date
        end_date: Year end date
    """
    from calendar import month_name
    
    current_date = start_date
    period_number = 1
    
    while current_date <= end_date:
        # Calculate period end (last day of month)
        if current_date.month == 12:
            period_end = date(current_date.year, 12, 31)
        else:
            period_end = date(current_date.year, current_date.month + 1, 1) - timedelta(days=1)
        
        # Ensure we don't exceed fiscal year end
        if period_end > end_date:
            period_end = end_date
        
        # Create period
        FiscalPeriod.objects.create(
            org=org,
            fiscal_year=fiscal_year,
            label=f"{month_name[current_date.month]} {current_date.year}",
            period_number=period_number,
            start_date=current_date,
            end_date=period_end,
            is_open=True,
        )
        
        # Move to next month
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)
        
        period_number += 1


def _assign_owner_role(org: Organisation, user: AppUser) -> None:
    """
    Assign the user as Owner of the organisation.
    
    Args:
        org: Organisation instance
        user: AppUser instance
    """
    # Create Owner role if it doesn't exist
    role, created = Role.objects.get_or_create(
        org=org,
        name="Owner",
        defaults={
            "description": "Full access to the organisation",
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
            "is_system": True,
        }
    )
    
    # Create user-organisation membership
    UserOrganisation.objects.create(
        user=user,
        org=org,
        role=role,
        is_default=True,
        accepted_at=timezone.now(),
    )


def update_organisation(org: Organisation, **kwargs) -> Organisation:
    """
    Update organisation settings.
    
    Args:
        org: Organisation instance
        **kwargs: Fields to update
        
    Returns:
        Updated Organisation instance
    """
    for key, value in kwargs.items():
        if hasattr(org, key):
            setattr(org, key, value)
    
    org.save()
    return org


def toggle_gst_registration(
    org: Organisation,
    registered: bool,
    reg_number: str = "",
    reg_date: Optional[date] = None
) -> Organisation:
    """
    Toggle GST registration status.
    
    Args:
        org: Organisation instance
        registered: New GST registration status
        reg_number: GST registration number (required if registered=True)
        reg_date: GST registration date (required if registered=True)
        
    Returns:
        Updated Organisation instance
        
    Raises:
        ValidationError: If required fields missing when registering
    """
    if registered:
        if not reg_number:
            raise ValidationError("GST registration number is required.")
        if not reg_date:
            raise ValidationError("GST registration date is required.")
        
        org.gst_registered = True
        org.gst_reg_number = reg_number
        org.gst_reg_date = reg_date
        
        # Seed GST accounts if newly registered
        if not org.gst_reg_number:
            _seed_chart_of_accounts(org.id, True)
    else:
        org.gst_registered = False
        org.gst_reg_number = ""
        org.gst_reg_date = None
    
    org.save()
    return org


# Need to import here to avoid circular dependency
from django.utils import timezone
