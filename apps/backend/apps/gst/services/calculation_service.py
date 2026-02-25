"""
GST Calculation service for LedgerSG.

Handles all GST calculations including:
- Line-level GST calculation
- BCRS deposit exemption
- Document totals
- Rounding per IRAS standards
"""

from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from common.decimal_utils import money


class GSTCalculationService:
    """Service class for GST calculations."""
    
    # Singapore GST rate
    DEFAULT_GST_RATE = Decimal("0.09")  # 9%
    
    @staticmethod
    def calculate_line_gst(
        amount: Decimal,
        rate: Decimal,
        is_bcrs_deposit: bool = False,
        rounding: int = 2
    ) -> Dict[str, Decimal]:
        """
        Calculate GST for a single line item.
        
        Singapore IRAS rules:
        - GST is calculated per line and rounded to 2 decimal places
        - BCRS (beverage container) deposits are GST exempt
        
        Args:
            amount: Line amount (excluding GST)
            rate: GST rate (e.g., 0.09 for 9%)
            is_bcrs_deposit: Whether this is a BCRS deposit
            rounding: Decimal places for rounding (default: 2)
            
        Returns:
            Dictionary with gst_amount, total_amount, net_amount
        """
        amount = money(amount)
        
        # BCRS deposits are GST exempt
        if is_bcrs_deposit:
            return {
                "net_amount": amount,
                "gst_amount": Decimal("0.00"),
                "total_amount": amount,
                "is_bcrs_exempt": True,
            }
        
        # Calculate GST
        if rate and rate > 0:
            gst_amount = (amount * rate).quantize(
                Decimal(f"0.{('0' * rounding)}1"),
                rounding=ROUND_HALF_UP
            )
        else:
            gst_amount = Decimal("0.00")
        
        total_amount = amount + gst_amount
        
        return {
            "net_amount": amount,
            "gst_amount": gst_amount,
            "total_amount": total_amount,
            "is_bcrs_exempt": False,
        }
    
    @staticmethod
    def calculate_document_gst(
        lines: List[Dict[str, Any]],
        default_rate: Decimal = DEFAULT_GST_RATE
    ) -> Dict[str, Any]:
        """
        Calculate GST for a document with multiple lines.
        
        Args:
            lines: List of line dictionaries with:
                - amount: Line amount
                - rate: GST rate (optional, uses default)
                - is_bcrs_deposit: Whether BCRS exempt
            default_rate: Default GST rate if not specified per line
            
        Returns:
            Document totals with breakdown
        """
        total_net = Decimal("0.00")
        total_gst = Decimal("0.00")
        total_amount = Decimal("0.00")
        bcrs_total = Decimal("0.00")
        
        line_results = []
        
        for line in lines:
            amount = money(line.get("amount", 0))
            rate = Decimal(str(line.get("rate", default_rate)))
            is_bcrs = line.get("is_bcrs_deposit", False)
            
            result = GSTCalculationService.calculate_line_gst(
                amount=amount,
                rate=rate,
                is_bcrs_deposit=is_bcrs
            )
            
            line_results.append({
                "line_id": line.get("id"),
                "net_amount": str(result["net_amount"]),
                "gst_amount": str(result["gst_amount"]),
                "total_amount": str(result["total_amount"]),
                "is_bcrs_exempt": result["is_bcrs_exempt"],
            })
            
            total_net += result["net_amount"]
            total_gst += result["gst_amount"]
            total_amount += result["total_amount"]
            
            if result["is_bcrs_exempt"]:
                bcrs_total += result["net_amount"]
        
        return {
            "lines": line_results,
            "summary": {
                "total_net": str(total_net.quantize(Decimal("0.01"))),
                "total_gst": str(total_gst.quantize(Decimal("0.01"))),
                "total_amount": str(total_amount.quantize(Decimal("0.01"))),
                "bcrs_exempt_total": str(bcrs_total.quantize(Decimal("0.01"))),
                "taxable_amount": str((total_net - bcrs_total).quantize(Decimal("0.01"))),
            }
        }
    
    @staticmethod
    def calculate_tax_inclusive_gst(
        total_amount: Decimal,
        rate: Decimal = DEFAULT_GST_RATE
    ) -> Dict[str, Decimal]:
        """
        Calculate GST from a tax-inclusive amount.
        
        Used when total includes GST and we need to back-calculate.
        
        Formula: GST = Total - (Total / (1 + rate))
        
        Args:
            total_amount: Total amount including GST
            rate: GST rate
            
        Returns:
            Dictionary with net_amount, gst_amount, total_amount
        """
        total_amount = money(total_amount)
        
        if rate <= 0:
            return {
                "net_amount": total_amount,
                "gst_amount": Decimal("0.00"),
                "total_amount": total_amount,
            }
        
        # Calculate net amount
        net_amount = (total_amount / (1 + rate)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        
        gst_amount = total_amount - net_amount
        
        return {
            "net_amount": net_amount,
            "gst_amount": gst_amount.quantize(Decimal("0.01")),
            "total_amount": total_amount,
        }
    
    @staticmethod
    def validate_gst_precision(
        calculated_gst: Decimal,
        expected_gst: Decimal,
        tolerance: Decimal = Decimal("0.01")
    ) -> bool:
        """
        Validate GST calculation matches expected within tolerance.
        
        IRAS allows 1 cent rounding difference.
        
        Args:
            calculated_gst: Our calculated GST
            expected_gst: Expected GST amount
            tolerance: Allowed difference (default: 0.01)
            
        Returns:
            True if within tolerance
        """
        diff = abs(calculated_gst - expected_gst)
        return diff <= tolerance
    
    @staticmethod
    def get_f5_box_amounts(
        org_id: UUID,
        period_start: str,
        period_end: str
    ) -> Dict[str, Any]:
        """
        Calculate F5 form box amounts for a period.
        
        This queries the database for aggregated amounts by tax code.
        
        Args:
            org_id: Organisation ID
            period_start: Period start date (YYYY-MM-DD)
            period_end: Period end date (YYYY-MM-DD)
            
        Returns:
            F5 box amounts dictionary
        """
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    tc.code as tax_code,
                    tc.box_mapping,
                    SUM(il.amount) as total_amount,
                    SUM(il.gst_amount) as total_gst,
                    COUNT(*) as line_count
                FROM invoicing.invoice_line il
                JOIN invoicing.invoice i ON i.id = il.invoice_id
                JOIN gst.tax_code tc ON tc.id = il.tax_code_id
                WHERE i.org_id = %s
                    AND i.document_date BETWEEN %s AND %s
                    AND i.status IN ('APPROVED', 'SENT', 'PAID_PARTIAL', 'PAID')
                    AND NOT il.is_voided
                GROUP BY tc.code, tc.box_mapping
                """,
                [str(org_id), period_start, period_end]
            )
            
            results = cursor.fetchall()
        
        # Initialize all boxes
        boxes = {
            # Output tax boxes
            "box1": Decimal("0.00"),  # Standard-rated supplies
            "box2": Decimal("0.00"),  # Zero-rated supplies
            "box3": Decimal("0.00"),  # Exempt supplies
            "box4": Decimal("0.00"),  # Total supplies (1+2+3)
            "box5": Decimal("0.00"),  # Output tax due
            
            # Input tax boxes
            "box6": Decimal("0.00"),  # Taxable purchases
            "box7": Decimal("0.00"),  # Input tax claims
            "box8": Decimal("0.00"),  # Net GST (5-7)
            
            # Additional boxes
            "box9": Decimal("0.00"),  # Goods imported
            "box10": Decimal("0.00"),  # GST on imports under MG/IGDS
            "box11": Decimal("0.00"),  # Service imports (reverse charge)
            "box12": Decimal("0.00"),  # Output tax on reverse charge
            "box13": Decimal("0.00"),  # Revenue
            "box14": Decimal("0.00"),  # Exempt supplies (repeat)
        }
        
        # Aggregate by box mapping
        for row in results:
            tax_code, box_mapping, amount, gst_amount, count = row
            amount = Decimal(str(amount or 0))
            gst_amount = Decimal(str(gst_amount or 0))
            
            if box_mapping and box_mapping in boxes:
                if tax_code in ["SR", "ME"]:
                    # Standard-rated: add to Box 1 and Box 5
                    boxes["box1"] += amount
                    boxes["box5"] += gst_amount
                    boxes["box13"] += amount
                elif tax_code == "ZR":
                    # Zero-rated: Box 2
                    boxes["box2"] += amount
                    boxes["box13"] += amount
                elif tax_code == "ES":
                    # Exempt: Box 3 and 14
                    boxes["box3"] += amount
                    boxes["box14"] += amount
                    boxes["box13"] += amount
                elif tax_code == "IM":
                    # Import: Box 9
                    boxes["box9"] += amount
                elif tax_code == "TX-E33":
                    # Purchase with GST: Box 6 and 7
                    boxes["box6"] += amount
                    boxes["box7"] += gst_amount
        
        # Calculate derived boxes
        boxes["box4"] = boxes["box1"] + boxes["box2"] + boxes["box3"]
        boxes["box8"] = boxes["box5"] - boxes["box7"]
        
        # Format for output
        return {
            box: str(value.quantize(Decimal("0.01")))
            for box, value in boxes.items()
        }


def calculate_gst_summary(
    net_amount: Decimal,
    gst_rate: Decimal = GSTCalculationService.DEFAULT_GST_RATE,
    is_bcrs_deposit: bool = False
) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Convenience function for GST calculation.
    
    Args:
        net_amount: Amount before GST
        gst_rate: GST rate (default 9%)
        is_bcrs_deposit: Whether BCRS exempt
        
    Returns:
        Tuple of (net_amount, gst_amount, total_amount)
    """
    result = GSTCalculationService.calculate_line_gst(
        amount=net_amount,
        rate=gst_rate,
        is_bcrs_deposit=is_bcrs_deposit
    )
    
    return (
        result["net_amount"],
        result["gst_amount"],
        result["total_amount"]
    )
