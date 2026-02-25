"""
GST Return service for LedgerSG.

Handles GST return periods and F5 form generation.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID
from datetime import date, timedelta
from calendar import monthrange

from django.db import connection, transaction

from apps.core.models import GSTReturn, FiscalPeriod
from apps.gst.services.calculation_service import GSTCalculationService
from common.exceptions import ValidationError, DuplicateResource, ResourceNotFound


class GSTReturnService:
    """Service class for GST return operations."""
    
    @staticmethod
    def list_returns(
        org_id: UUID,
        status: Optional[str] = None,
        year: Optional[int] = None
    ) -> List[GSTReturn]:
        """
        List GST returns for an organisation.
        
        Args:
            org_id: Organisation ID
            status: Filter by status
            year: Filter by calendar year
            
        Returns:
            List of GSTReturn instances
        """
        queryset = GSTReturn.objects.filter(org_id=org_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if year:
            queryset = queryset.filter(period_start__year=year)
        
        return list(queryset.order_by("-period_start"))
    
    @staticmethod
    def get_return(org_id: UUID, return_id: UUID) -> GSTReturn:
        """
        Get GST return by ID.
        
        Args:
            org_id: Organisation ID
            return_id: GST return ID
            
        Returns:
            GSTReturn instance
        """
        try:
            return GSTReturn.objects.get(id=return_id, org_id=org_id)
        except GSTReturn.DoesNotExist:
            raise ResourceNotFound(f"GST return {return_id} not found")
    
    @staticmethod
    def create_return_periods(
        org_id: UUID,
        filing_frequency: str,
        start_date: date,
        periods: int = 12
    ) -> List[GSTReturn]:
        """
        Create GST return periods for an organisation.
        
        Args:
            org_id: Organisation ID
            filing_frequency: 'MONTHLY' or 'QUARTERLY'
            start_date: First period start date
            periods: Number of periods to create
            
        Returns:
            List of created GSTReturn instances
        """
        if filing_frequency not in ["MONTHLY", "QUARTERLY"]:
            raise ValidationError("Filing frequency must be MONTHLY or QUARTERLY")
        
        created = []
        current_date = start_date
        
        for _ in range(periods):
            if filing_frequency == "MONTHLY":
                # Monthly period
                period_start = current_date.replace(day=1)
                last_day = monthrange(current_date.year, current_date.month)[1]
                period_end = current_date.replace(day=last_day)
                label = period_start.strftime("%b %Y")
                
                # Due date is last day of following month
                if current_date.month == 12:
                    due_date = date(current_date.year + 1, 1, 31)
                else:
                    due_date = date(current_date.year, current_date.month + 1, 1)
                    last_day_next = monthrange(due_date.year, due_date.month)[1]
                    due_date = due_date.replace(day=last_day_next)
                
                # Move to next month
                if current_date.month == 12:
                    current_date = date(current_date.year + 1, 1, 1)
                else:
                    current_date = date(current_date.year, current_date.month + 1, 1)
                
            else:  # QUARTERLY
                # Quarterly period
                quarter = (current_date.month - 1) // 3
                quarter_start_month = quarter * 3 + 1
                period_start = date(current_date.year, quarter_start_month, 1)
                
                quarter_end_month = quarter_start_month + 2
                last_day = monthrange(current_date.year, quarter_end_month)[1]
                period_end = date(current_date.year, quarter_end_month, last_day)
                
                label = f"Q{quarter + 1} {current_date.year}"
                
                # Due date is last day of month following quarter end
                if quarter_end_month == 12:
                    due_date = date(current_date.year + 1, 1, 31)
                else:
                    due_month = quarter_end_month + 1
                    last_day_due = monthrange(current_date.year, due_month)[1]
                    due_date = date(current_date.year, due_month, last_day_due)
                
                # Move to next quarter
                if quarter == 3:
                    current_date = date(current_date.year + 1, 1, 1)
                else:
                    current_date = date(current_date.year, (quarter + 1) * 3 + 1, 1)
            
            # Check if period already exists
            if GSTReturn.objects.filter(
                org_id=org_id,
                period_start=period_start,
                period_end=period_end
            ).exists():
                continue
            
            gst_return = GSTReturn.objects.create(
                org_id=org_id,
                period_start=period_start,
                period_end=period_end,
                due_date=due_date,
                filing_frequency=filing_frequency,
                label=label,
                status="DRAFT",
            )
            created.append(gst_return)
        
        return created
    
    @staticmethod
    def generate_f5(
        org_id: UUID,
        return_id: UUID,
        force_recalculate: bool = False
    ) -> GSTReturn:
        """
        Generate/update F5 form for a GST return period.
        
        Args:
            org_id: Organisation ID
            return_id: GST return ID
            force_recalculate: Force recalculation even if already calculated
            
        Returns:
            Updated GSTReturn instance
        """
        gst_return = GSTReturnService.get_return(org_id, return_id)
        
        # Only recalculate if in DRAFT status or forced
        if gst_return.status != "DRAFT" and not force_recalculate:
            raise ValidationError(
                f"Cannot recalculate F5 for status '{gst_return.status}'. "
                "Use force_recalculate=true to override."
            )
        
        # Get box amounts
        boxes = GSTCalculationService.get_f5_box_amounts(
            org_id=org_id,
            period_start=gst_return.period_start.isoformat(),
            period_end=gst_return.period_end.isoformat()
        )
        
        # Update GST return
        gst_return.box1_std_rated_supplies = Decimal(boxes["box1"])
        gst_return.box2_zero_rated_supplies = Decimal(boxes["box2"])
        gst_return.box3_exempt_supplies = Decimal(boxes["box3"])
        gst_return.box4_total_supplies = Decimal(boxes["box4"])
        gst_return.box5_output_tax = Decimal(boxes["box5"])
        gst_return.box6_taxable_purchases = Decimal(boxes["box6"])
        gst_return.box7_input_tax = Decimal(boxes["box7"])
        gst_return.box8_net_gst = Decimal(boxes["box8"])
        gst_return.box13_revenue = Decimal(boxes["box13"])
        gst_return.box14_exempt_supplies = Decimal(boxes["box14"])
        
        gst_return.save()
        
        return gst_return
    
    @staticmethod
    def file_return(
        org_id: UUID,
        return_id: UUID,
        filed_by_id: UUID,
        filing_reference: Optional[str] = None,
        boxes: Optional[Dict[str, Decimal]] = None
    ) -> GSTReturn:
        """
        File a GST return.
        
        Args:
            org_id: Organisation ID
            return_id: GST return ID
            filed_by_id: User ID who filed
            filing_reference: IRAS filing reference number
            boxes: Optional override box amounts
            
        Returns:
            Filed GSTReturn instance
        """
        with transaction.atomic():
            gst_return = GSTReturnService.get_return(org_id, return_id)
            
            if gst_return.status not in ["DRAFT", "AMENDING"]:
                raise ValidationError(
                    f"Cannot file return with status '{gst_return.status}'"
                )
            
            # Apply box overrides if provided
            if boxes:
                for box_name, value in boxes.items():
                    if hasattr(gst_return, box_name):
                        setattr(gst_return, box_name, value)
            
            # Recalculate net GST
            gst_return.box8_net_gst = (
                gst_return.box5_output_tax - gst_return.box7_input_tax
            )
            
            # Update status
            gst_return.status = "FILED"
            gst_return.filed_at = timezone.now()
            gst_return.filed_by_id = filed_by_id
            gst_return.filing_reference = filing_reference
            
            gst_return.save()
            
            return gst_return
    
    @staticmethod
    def amend_return(
        org_id: UUID,
        return_id: UUID,
        reason: str
    ) -> GSTReturn:
        """
        Mark a return for amendment.
        
        Args:
            org_id: Organisation ID
            return_id: GST return ID
            reason: Amendment reason
            
        Returns:
            GSTReturn instance marked for amendment
        """
        gst_return = GSTReturnService.get_return(org_id, return_id)
        
        if gst_return.status != "FILED":
            raise ValidationError("Only filed returns can be amended")
        
        gst_return.status = "AMENDING"
        gst_return.amendment_reason = reason
        gst_return.save()
        
        return gst_return
    
    @staticmethod
    def pay_return(
        org_id: UUID,
        return_id: UUID,
        payment_date: date,
        payment_amount: Decimal,
        payment_reference: str
    ) -> GSTReturn:
        """
        Record payment for a GST return.
        
        Args:
            org_id: Organisation ID
            return_id: GST return ID
            payment_date: Date of payment
            payment_amount: Amount paid
            payment_reference: Payment reference number
            
        Returns:
            Updated GSTReturn instance
        """
        gst_return = GSTReturnService.get_return(org_id, return_id)
        
        if gst_return.status != "FILED":
            raise ValidationError("Only filed returns can be paid")
        
        gst_return.paid_at = payment_date
        gst_return.payment_amount = payment_amount
        gst_return.payment_reference = payment_reference
        
        # Check if fully paid
        if abs(payment_amount - gst_return.box8_net_gst) < Decimal("0.01"):
            gst_return.status = "PAID"
        
        gst_return.save()
        
        return gst_return
    
    @staticmethod
    def get_f5_json(org_id: UUID, return_id: UUID) -> Dict[str, Any]:
        """
        Get F5 form data as JSON for API response.
        
        Args:
            org_id: Organisation ID
            return_id: GST return ID
            
        Returns:
            F5 form data dictionary
        """
        gst_return = GSTReturnService.get_return(org_id, return_id)
        
        return {
            "id": str(gst_return.id),
            "label": gst_return.label,
            "period_start": gst_return.period_start.isoformat(),
            "period_end": gst_return.period_end.isoformat(),
            "due_date": gst_return.due_date.isoformat(),
            "status": gst_return.status,
            "filing_frequency": gst_return.filing_frequency,
            "boxes": {
                "box1_standard_rated_supplies": str(gst_return.box1_std_rated_supplies),
                "box2_zero_rated_supplies": str(gst_return.box2_zero_rated_supplies),
                "box3_exempt_supplies": str(gst_return.box3_exempt_supplies),
                "box4_total_supplies": str(gst_return.box4_total_supplies),
                "box5_output_tax": str(gst_return.box5_output_tax),
                "box6_taxable_purchases": str(gst_return.box6_taxable_purchases),
                "box7_input_tax": str(gst_return.box7_input_tax),
                "box8_net_gst": str(gst_return.box8_net_gst),
                "box9_goods_imported": str(gst_return.box9_goods_imported or 0),
                "box10_gst_imports_mg_igds": str(gst_return.box10_gst_imports_mg_igds or 0),
                "box11_service_imports": str(gst_return.box11_service_imports or 0),
                "box12_output_tax_reverse_charge": str(gst_return.box12_output_tax_reverse_charge or 0),
                "box13_revenue": str(gst_return.box13_revenue),
                "box14_exempt_supplies": str(gst_return.box14_exempt_supplies),
                "box15_imports_exports_indicator": gst_return.box15_indicator or "N",
            },
            "filing": {
                "filed_at": gst_return.filed_at.isoformat() if gst_return.filed_at else None,
                "filed_by": str(gst_return.filed_by_id) if gst_return.filed_by_id else None,
                "filing_reference": gst_return.filing_reference,
            },
            "payment": {
                "paid_at": gst_return.paid_at.isoformat() if gst_return.paid_at else None,
                "payment_amount": str(gst_return.payment_amount) if gst_return.payment_amount else None,
                "payment_reference": gst_return.payment_reference,
            },
        }
    
    @staticmethod
    def get_upcoming_deadlines(
        org_id: UUID,
        days: int = 30
    ) -> List[GSTReturn]:
        """
        Get upcoming GST filing deadlines.
        
        Args:
            org_id: Organisation ID
            days: Number of days to look ahead
            
        Returns:
            List of GSTReturn instances with upcoming deadlines
        """
        today = date.today()
        deadline = today + timedelta(days=days)
        
        return list(GSTReturn.objects.filter(
            org_id=org_id,
            status="DRAFT",
            due_date__lte=deadline,
            due_date__gte=today
        ).order_by("due_date"))


# Import at end to avoid circular imports
from django.utils import timezone
