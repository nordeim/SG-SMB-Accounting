"""
Contact service for LedgerSG Invoicing module.

Manages customers and suppliers including:
- Contact CRUD
- UEN validation (Singapore)
- Peppol ID validation
- Customer/Supplier categorization
"""

from typing import Optional, List
from uuid import UUID
from datetime import date, timedelta

from apps.core.models import Contact
from common.exceptions import ValidationError, DuplicateResource, ResourceNotFound


class ContactService:
    """Service class for contact operations."""
    
    @staticmethod
    def list_contacts(
        org_id: UUID,
        is_customer: Optional[bool] = None,
        is_supplier: Optional[bool] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Contact]:
        """
        List contacts for an organisation.
        
        Args:
            org_id: Organisation ID
            is_customer: Filter by customer flag
            is_supplier: Filter by supplier flag
            is_active: Filter by active status
            search: Search in name, email, UEN
            
        Returns:
            List of Contact instances
        """
        queryset = Contact.objects.filter(org_id=org_id)
        
        if is_customer is not None:
            queryset = queryset.filter(is_customer=is_customer)
        
        if is_supplier is not None:
            queryset = queryset.filter(is_supplier=is_supplier)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(uen__icontains=search) |
                models.Q(company_name__icontains=search)
            )
        
        return list(queryset.order_by("name"))
    
    @staticmethod
    def get_contact(org_id: UUID, contact_id: UUID) -> Contact:
        """
        Get contact by ID.
        
        Args:
            org_id: Organisation ID
            contact_id: Contact ID
            
        Returns:
            Contact instance
        """
        try:
            return Contact.objects.get(id=contact_id, org_id=org_id)
        except Contact.DoesNotExist:
            raise ResourceNotFound(f"Contact {contact_id} not found")
    
    @staticmethod
    def create_contact(
        org_id: UUID,
        name: str,
        company_name: str = "",
        email: str = "",
        phone: str = "",
        address_line1: str = "",
        address_line2: str = "",
        city: str = "",
        postal_code: str = "",
        country: str = "SG",
        uen: str = "",
        peppol_id: str = "",
        is_customer: bool = True,
        is_supplier: bool = False,
        payment_terms_days: int = 30,
        **kwargs
    ) -> Contact:
        """
        Create a new contact.
        
        Args:
            org_id: Organisation ID
            name: Contact name (person or company)
            company_name: Company name
            email: Email address
            phone: Phone number
            address_line1: Street address line 1
            address_line2: Street address line 2
            city: City
            postal_code: Postal code
            country: Country code (default: SG)
            uen: Singapore UEN (optional)
            peppol_id: Peppol participant ID (optional)
            is_customer: Is a customer
            is_supplier: Is a supplier
            payment_terms_days: Payment terms in days
            **kwargs: Additional fields
            
        Returns:
            Created Contact instance
        """
        # Validate at least one of customer/supplier
        if not is_customer and not is_supplier:
            raise ValidationError("Contact must be a customer, supplier, or both.")
        
        # Validate UEN format if provided
        if uen:
            uen = uen.strip().upper()
            if not ContactService._validate_uen(uen):
                raise ValidationError(f"Invalid UEN format: {uen}")
            
            # Check uniqueness within org
            if Contact.objects.filter(org_id=org_id, uen=uen).exists():
                raise DuplicateResource(f"Contact with UEN '{uen}' already exists.")
        
        # Validate Peppol ID if provided
        if peppol_id:
            peppol_id = peppol_id.strip()
            if not ContactService._validate_peppol_id(peppol_id):
                raise ValidationError(f"Invalid Peppol ID format: {peppol_id}")
        
        # Create contact
        contact = Contact.objects.create(
            org_id=org_id,
            name=name.strip(),
            company_name=company_name.strip(),
            email=email.strip().lower(),
            phone=phone.strip(),
            address_line1=address_line1.strip(),
            address_line2=address_line2.strip(),
            city=city.strip(),
            postal_code=postal_code.strip(),
            country=country.upper(),
            uen=uen,
            peppol_id=peppol_id,
            is_customer=is_customer,
            is_supplier=is_supplier,
            payment_terms_days=payment_terms_days,
            is_active=True,
            **kwargs
        )
        
        return contact
    
    @staticmethod
    def update_contact(
        org_id: UUID,
        contact_id: UUID,
        **updates
    ) -> Contact:
        """
        Update contact fields.
        
        Args:
            org_id: Organisation ID
            contact_id: Contact ID
            **updates: Fields to update
            
        Returns:
            Updated Contact instance
        """
        contact = ContactService.get_contact(org_id, contact_id)
        
        # Validate UEN if changed
        if "uen" in updates:
            new_uen = updates["uen"].strip().upper()
            if new_uen != contact.uen:
                if new_uen and not ContactService._validate_uen(new_uen):
                    raise ValidationError(f"Invalid UEN format: {new_uen}")
                
                if Contact.objects.filter(org_id=org_id, uen=new_uen).exclude(id=contact_id).exists():
                    raise DuplicateResource(f"Contact with UEN '{new_uen}' already exists.")
                
                updates["uen"] = new_uen
        
        # Validate Peppol ID if changed
        if "peppol_id" in updates:
            new_peppol = updates["peppol_id"].strip()
            if new_peppol and not ContactService._validate_peppol_id(new_peppol):
                raise ValidationError(f"Invalid Peppol ID format: {new_peppol}")
            updates["peppol_id"] = new_peppol
        
        # Update fields
        for key, value in updates.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        
        contact.save()
        return contact
    
    @staticmethod
    def deactivate_contact(org_id: UUID, contact_id: UUID) -> Contact:
        """
        Deactivate a contact.
        
        Args:
            org_id: Organisation ID
            contact_id: Contact ID
            
        Returns:
            Deactivated Contact instance
        """
        contact = ContactService.get_contact(org_id, contact_id)
        
        # Check for open invoices
        open_invoices = InvoiceDocument.objects.filter(
            contact=contact,
            status__in=["DRAFT", "SENT", "APPROVED", "PAID_PARTIAL"]
        ).count()
        
        if open_invoices > 0:
            raise ValidationError(
                f"Cannot deactivate contact with {open_invoices} open invoices. "
                "Void or pay all invoices first."
            )
        
        contact.is_active = False
        contact.save()
        
        return contact
    
    @staticmethod
    def _validate_uen(uen: str) -> bool:
        """
        Validate Singapore UEN format.
        
        UEN formats:
        - Local companies: 9 digits (e.g., 123456789A)
        - Businesses: 8 digits + 1 letter (e.g., 12345678A)
        - Others: Various formats
        
        Args:
            uen: UEN to validate
            
        Returns:
            True if valid format
        """
        if not uen:
            return True  # Empty is valid (optional field)
        
        uen = uen.strip().upper()
        
        # Basic format checks
        if len(uen) < 8 or len(uen) > 10:
            return False
        
        # Common UEN patterns
        import re
        patterns = [
            r'^\d{9}[A-Z]$',  # Local companies
            r'^\d{8}[A-Z]$',  # Businesses
            r'^[TS]\d{2}[A-Z]{2}\d{4}[A-Z]$',  # Partnerships
            r'^\d{10}$',  # GST-registered businesses
        ]
        
        return any(re.match(pattern, uen) for pattern in patterns)
    
    @staticmethod
    def _validate_peppol_id(peppol_id: str) -> bool:
        """
        Validate Peppol participant ID format.
        
        Format: 0195:123456789A (scheme:identifier)
        
        Args:
            peppol_id: Peppol ID to validate
            
        Returns:
            True if valid format
        """
        if not peppol_id:
            return True  # Empty is valid
        
        peppol_id = peppol_id.strip()
        
        # Common Peppol schemes
        valid_schemes = ["0195", "0088", "0060", "9901"]
        
        if ":" in peppol_id:
            parts = peppol_id.split(":", 1)
            if len(parts) == 2:
                scheme, identifier = parts
                return scheme in valid_schemes and len(identifier) >= 3
        
        # Allow identifier only (assume 0195 for Singapore)
        return len(peppol_id) >= 8


# Import at end to avoid circular imports
from django.db import models
from apps.core.models import InvoiceDocument
