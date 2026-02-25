"""
Tax Code service for LedgerSG GST module.

Manages GST tax codes including:
- Listing tax codes (seeded + custom)
- Creating custom tax codes
- Validating tax codes for invoices
- Getting current GST rate
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID
from datetime import date

from apps.core.models import TaxCode
from common.exceptions import ValidationError, DuplicateResource, ResourceNotFound


# IRAS-defined tax codes (seeded)
IRAS_TAX_CODES = {
    "SR": {
        "name": "Standard-Rated",
        "rate": Decimal("0.09"),  # 9% GST
        "is_gst_charged": True,
        "description": "Standard-rated supplies (9% GST)",
        "box_mapping": "box1",  # F5 Box 1
    },
    "ZR": {
        "name": "Zero-Rated",
        "rate": Decimal("0.00"),  # 0% GST
        "is_gst_charged": True,
        "description": "Zero-rated supplies (exports, international services)",
        "box_mapping": "box2",  # F5 Box 2
    },
    "ES": {
        "name": "Exempt",
        "rate": None,  # No GST
        "is_gst_charged": False,
        "description": "Exempt supplies (financial services, residential rent)",
        "box_mapping": "box3",  # F5 Box 3
    },
    "OS": {
        "name": "Out-of-Scope",
        "rate": None,  # No GST
        "is_gst_charged": False,
        "description": "Out-of-scope supplies (asset sales, private transactions)",
        "box_mapping": None,  # Not reported
    },
    "IM": {
        "name": "Import",
        "rate": Decimal("0.09"),  # 9% GST
        "is_gst_charged": True,
        "description": "Imported goods",
        "box_mapping": "box9",  # F5 Box 9
    },
    "ME": {
        "name": "Metered",
        "rate": Decimal("0.09"),  # 9% GST
        "is_gst_charged": True,
        "description": "Metered services (utilities with special rules)",
        "box_mapping": "box1",  # F5 Box 1
    },
    "TX-E33": {
        "name": "Purchase with GST",
        "rate": Decimal("0.09"),
        "is_gst_charged": True,
        "description": "Purchase with GST incurred",
        "box_mapping": "box6",  # F5 Box 6
    },
    "BL": {
        "name": "BCRS Deposit",
        "rate": Decimal("0.00"),
        "is_gst_charged": False,
        "description": "Beverage container deposit (GST exempt)",
        "box_mapping": None,
        "is_bcrs_exempt": True,
    },
}


class TaxCodeService:
    """Service class for tax code operations."""
    
    @staticmethod
    def list_tax_codes(
        org_id: UUID,
        is_active: Optional[bool] = None,
        is_gst_charged: Optional[bool] = None,
        include_system: bool = True
    ) -> List[TaxCode]:
        """
        List tax codes for an organisation.
        
        Args:
            org_id: Organisation ID
            is_active: Filter by active status
            is_gst_charged: Filter by GST-charged flag
            include_system: Include system tax codes
            
        Returns:
            List of TaxCode instances
        """
        queryset = TaxCode.objects.filter(org_id=org_id)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        
        if is_gst_charged is not None:
            queryset = queryset.filter(is_gst_charged=is_gst_charged)
        
        if not include_system:
            queryset = queryset.filter(is_system=False)
        
        return list(queryset.order_by("code"))
    
    @staticmethod
    def get_tax_code(org_id: UUID, tax_code_id: UUID) -> TaxCode:
        """
        Get tax code by ID.
        
        Args:
            org_id: Organisation ID
            tax_code_id: Tax code ID
            
        Returns:
            TaxCode instance
            
        Raises:
            ResourceNotFound: If tax code doesn't exist
        """
        try:
            return TaxCode.objects.get(id=tax_code_id, org_id=org_id)
        except TaxCode.DoesNotExist:
            raise ResourceNotFound(f"Tax code {tax_code_id} not found")
    
    @staticmethod
    def get_tax_code_by_code(org_id: UUID, code: str) -> Optional[TaxCode]:
        """
        Get tax code by code.
        
        Args:
            org_id: Organisation ID
            code: Tax code (e.g., 'SR', 'ZR')
            
        Returns:
            TaxCode instance or None
        """
        try:
            return TaxCode.objects.get(org_id=org_id, code=code.upper())
        except TaxCode.DoesNotExist:
            return None
    
    @staticmethod
    def create_tax_code(
        org_id: UUID,
        code: str,
        name: str,
        rate: Optional[Decimal],
        is_gst_charged: bool,
        description: str = "",
        box_mapping: Optional[str] = None,
        **kwargs
    ) -> TaxCode:
        """
        Create a custom tax code.
        
        Note: Cannot create codes that match IRAS system codes.
        
        Args:
            org_id: Organisation ID
            code: Tax code (2-10 chars, uppercase)
            name: Display name
            rate: GST rate (e.g., 0.09 for 9%) or None
            is_gst_charged: Whether GST is charged
            description: Description
            box_mapping: F5 box mapping
            **kwargs: Additional fields
            
        Returns:
            Created TaxCode instance
            
        Raises:
            ValidationError: If code is reserved or invalid
            DuplicateResource: If code already exists
        """
        code = code.upper().strip()
        
        # Validate code format
        if not code:
            raise ValidationError("Tax code is required.")
        
        if len(code) < 2 or len(code) > 10:
            raise ValidationError("Tax code must be between 2 and 10 characters.")
        
        # Check if code is reserved (IRAS system codes)
        if code in IRAS_TAX_CODES:
            raise ValidationError(
                f"Tax code '{code}' is reserved for IRAS-defined codes. "
                "Use a different code for custom tax codes."
            )
        
        # Check uniqueness
        if TaxCode.objects.filter(org_id=org_id, code=code).exists():
            raise DuplicateResource(f"Tax code '{code}' already exists.")
        
        # Validate rate
        if rate is not None and (rate < 0 or rate > 1):
            raise ValidationError("GST rate must be between 0 and 1 (e.g., 0.09 for 9%).")
        
        # Validate box_mapping
        valid_boxes = ["box1", "box2", "box3", "box6", "box9", "box11", None]
        if box_mapping and box_mapping not in valid_boxes:
            raise ValidationError(f"Invalid box mapping. Valid: {valid_boxes}")
        
        # Create tax code
        tax_code = TaxCode.objects.create(
            org_id=org_id,
            code=code,
            name=name.strip(),
            rate=rate,
            is_gst_charged=is_gst_charged,
            description=description.strip(),
            box_mapping=box_mapping,
            is_system=False,  # Custom codes are never system
            is_active=True,
            effective_from=date.today(),
            **kwargs
        )
        
        return tax_code
    
    @staticmethod
    def update_tax_code(
        org_id: UUID,
        tax_code_id: UUID,
        **updates
    ) -> TaxCode:
        """
        Update tax code.
        
        System tax codes can only have description updated.
        Custom tax codes can be fully modified.
        
        Args:
            org_id: Organisation ID
            tax_code_id: Tax code ID
            **updates: Fields to update
            
        Returns:
            Updated TaxCode instance
        """
        tax_code = TaxCodeService.get_tax_code(org_id, tax_code_id)
        
        # System codes have limited update capability
        if tax_code.is_system:
            allowed_fields = {"description", "is_active"}
            for key in list(updates.keys()):
                if key not in allowed_fields:
                    raise ValidationError(
                        f"Cannot modify '{key}' on system tax codes. "
                        f"Only description and active status can be changed."
                    )
        
        # Validate rate if provided
        if "rate" in updates and updates["rate"] is not None:
            rate = updates["rate"]
            if rate < 0 or rate > 1:
                raise ValidationError("GST rate must be between 0 and 1.")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(tax_code, key):
                setattr(tax_code, key, value)
        
        tax_code.save()
        return tax_code
    
    @staticmethod
    def deactivate_tax_code(org_id: UUID, tax_code_id: UUID) -> TaxCode:
        """
        Deactivate a custom tax code.
        
        System tax codes cannot be deactivated.
        
        Args:
            org_id: Organisation ID
            tax_code_id: Tax code ID
            
        Returns:
            Deactivated TaxCode instance
        """
        tax_code = TaxCodeService.get_tax_code(org_id, tax_code_id)
        
        if tax_code.is_system:
            raise ValidationError("System tax codes cannot be deactivated.")
        
        tax_code.is_active = False
        tax_code.save()
        
        return tax_code
    
    @staticmethod
    def validate_tax_code_for_invoice(
        org_id: UUID,
        tax_code_id: UUID,
        amount: Decimal,
        is_bcrs_deposit: bool = False
    ) -> Dict[str, Any]:
        """
        Validate tax code for an invoice line.
        
        Args:
            org_id: Organisation ID
            tax_code_id: Tax code ID
            amount: Line amount
            is_bcrs_deposit: Whether this is a BCRS deposit
            
        Returns:
            Validation result with calculated GST
        """
        tax_code = TaxCodeService.get_tax_code(org_id, tax_code_id)
        
        if not tax_code.is_active:
            raise ValidationError(f"Tax code '{tax_code.code}' is not active.")
        
        # BCRS deposits are always GST exempt
        if is_bcrs_deposit or getattr(tax_code, 'is_bcrs_exempt', False):
            return {
                "valid": True,
                "tax_code": tax_code.code,
                "rate": Decimal("0.00"),
                "gst_amount": Decimal("0.00"),
                "total_amount": amount,
                "is_bcrs_exempt": True,
            }
        
        # Calculate GST
        if tax_code.rate is not None and tax_code.is_gst_charged:
            gst_amount = (amount * tax_code.rate).quantize(Decimal("0.01"))
            total_amount = amount + gst_amount
        else:
            gst_amount = Decimal("0.00")
            total_amount = amount
        
        return {
            "valid": True,
            "tax_code": tax_code.code,
            "rate": tax_code.rate,
            "gst_amount": gst_amount,
            "total_amount": total_amount,
            "is_bcrs_exempt": False,
            "box_mapping": tax_code.box_mapping,
        }
    
    @staticmethod
    def get_current_gst_rate(org_id: UUID, as_of_date: Optional[date] = None) -> Decimal:
        """
        Get current GST rate.
        
        Returns the standard-rated GST rate (SR code).
        
        Args:
            org_id: Organisation ID
            as_of_date: Date to check rate for (default: today)
            
        Returns:
            GST rate as Decimal (e.g., 0.09)
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        # Get standard-rated tax code
        sr_code = TaxCodeService.get_tax_code_by_code(org_id, "SR")
        if sr_code and sr_code.rate is not None:
            return sr_code.rate
        
        # Default to current Singapore rate
        return Decimal("0.09")
    
    @staticmethod
    def seed_default_tax_codes(org_id: UUID) -> List[TaxCode]:
        """
        Seed default IRAS tax codes for a new organisation.
        
        This is called during organisation creation.
        
        Args:
            org_id: Organisation ID
            
        Returns:
            List of created TaxCode instances
        """
        created = []
        
        for code, config in IRAS_TAX_CODES.items():
            # Check if already exists
            if TaxCode.objects.filter(org_id=org_id, code=code).exists():
                continue
            
            tax_code = TaxCode.objects.create(
                org_id=org_id,
                code=code,
                name=config["name"],
                rate=config["rate"],
                is_gst_charged=config["is_gst_charged"],
                description=config["description"],
                box_mapping=config.get("box_mapping"),
                is_system=True,
                is_active=True,
                effective_from=date(2024, 1, 1),  # 9% effective from 2024
            )
            created.append(tax_code)
        
        return created
    
    @staticmethod
    def get_iras_tax_codes_info() -> Dict[str, Any]:
        """
        Get information about IRAS-defined tax codes.
        
        Returns:
            Dictionary of tax code information
        """
        return {
            code: {
                "name": config["name"],
                "rate": str(config["rate"]) if config["rate"] else None,
                "is_gst_charged": config["is_gst_charged"],
                "description": config["description"],
                "box_mapping": config.get("box_mapping"),
            }
            for code, config in IRAS_TAX_CODES.items()
        }
