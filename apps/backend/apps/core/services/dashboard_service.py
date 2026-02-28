"""
Dashboard Service for LedgerSG.

Aggregates dashboard metrics from multiple sources for real-time
financial overview and IRAS compliance monitoring.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Any
from django.db import connection
from django.db.models import Sum, Q, Count

from apps.core.models import (
    Organisation,
    Account,
    FiscalYear,
    FiscalPeriod,
    InvoiceDocument,
)


class DashboardService:
    """
    Service for aggregating dashboard metrics.
    
    Combines data from:
    - Accounts (cash, receivables, payables)
    - GST (output tax, input tax, threshold monitoring)
    - Invoices (pending, overdue, peppol status)
    - Fiscal periods (current period, filing deadlines)
    """
    
    # GST threshold limit for Singapore (S$1,000,000)
    GST_THRESHOLD_LIMIT = Decimal("1000000.00")
    
    @classmethod
    def get_dashboard_data(cls, org_id: str) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for an organisation.
        
        Args:
            org_id: Organisation UUID
            
        Returns:
            Dictionary containing all dashboard metrics
            
        Raises:
            Organisation.DoesNotExist: If organisation not found
        """
        org = Organisation.objects.get(id=org_id)
        
        # Aggregate all metrics
        data = {
            # Financial metrics
            **cls._get_gst_metrics(org),
            **cls._get_cash_metrics(org),
            **cls._get_receivables_metrics(org),
            **cls._get_revenue_metrics(org),
            
            # GST threshold monitoring
            **cls._get_gst_threshold_metrics(org),
            
            # Compliance
            'compliance_alerts': cls._get_compliance_alerts(org),
            
            # Invoice statistics
            **cls._get_invoice_metrics(org),
            
            # Period info
            'current_gst_period': cls._get_current_gst_period(org),
            
            # Metadata
            'last_updated': cls._get_iso_timestamp(),
        }
        
        return data
    
    @classmethod
    def _get_gst_metrics(cls, org: Organisation) -> Dict[str, str]:
        """Calculate GST payable (Output - Input)."""
        # For MVP: Calculate from invoices if GST accounts not available
        # In production, this should aggregate from journal entries
        
        # Get GST from SENT invoices (output tax collected)
        output_tax = InvoiceDocument.objects.filter(
            org=org,
            document_type='SALES_INVOICE',
            status__in=['SENT', 'PARTIALLY_PAID', 'PAID', 'OVERDUE'],
        ).aggregate(
            total=Sum('gst_total')
        )['total'] or Decimal('0.00')
        
        # Get GST from purchase invoices (input tax paid)
        input_tax = InvoiceDocument.objects.filter(
            org=org,
            document_type='PURCHASE_INVOICE',
            status__in=['SENT', 'PARTIALLY_PAID', 'PAID', 'OVERDUE'],
        ).aggregate(
            total=Sum('gst_total')
        )['total'] or Decimal('0.00')
        
        # GST Payable = Output - Input
        gst_payable = output_tax - input_tax
        
        return {
            'gst_payable': str(gst_payable),  # 4dp internal
            'gst_payable_display': cls._format_currency(gst_payable),  # 2dp display
        }
    
    @classmethod
    def _get_cash_metrics(cls, org: Organisation) -> Dict[str, str]:
        """Get cash on hand - calculated from paid invoices minus payables."""
        # For MVP: Calculate from invoices as proxy
        # In production, this should come from bank account balances
        
        cash_received = InvoiceDocument.objects.filter(
            org=org,
            document_type='SALES_INVOICE',
            status='PAID',
        ).aggregate(
            total=Sum('total_incl')
        )['total'] or Decimal('0.00')
        
        cash_paid = InvoiceDocument.objects.filter(
            org=org,
            document_type='PURCHASE_INVOICE',
            status='PAID',
        ).aggregate(
            total=Sum('total_incl')
        )['total'] or Decimal('0.00')
        
        cash = cash_received - cash_paid
        
        return {
            'cash_on_hand': cls._format_currency(cash),
        }
    
    @classmethod
    def _get_receivables_metrics(cls, org: Organisation) -> Dict[str, str]:
        """Calculate outstanding receivables from unpaid invoices."""
        # Sum of SENT/PARTIAL/OVERDUE invoices (not fully paid, not voided)
        receivables = InvoiceDocument.objects.filter(
            org=org,
            document_type='SALES_INVOICE',
            status__in=['SENT', 'PARTIALLY_PAID', 'OVERDUE'],
        ).aggregate(
            total=Sum('total_incl')
        )['total'] or Decimal('0.00')
        
        # Calculate payables similarly (purchase invoices)
        payables = InvoiceDocument.objects.filter(
            org=org,
            document_type='PURCHASE_INVOICE',
            status__in=['SENT', 'PARTIALLY_PAID', 'OVERDUE'],
        ).aggregate(
            total=Sum('total_incl')
        )['total'] or Decimal('0.00')
        
        return {
            'outstanding_receivables': cls._format_currency(receivables),
            'outstanding_payables': cls._format_currency(payables),
        }
    
    @classmethod
    def _get_revenue_metrics(cls, org: Organisation) -> Dict[str, str]:
        """Calculate MTD and YTD revenue from paid invoices."""
        today = date.today()
        
        # MTD: Current month paid invoices
        mtd_start = date(today.year, today.month, 1)
        mtd_revenue = InvoiceDocument.objects.filter(
            org=org,
            document_type='SALES_INVOICE',
            status='PAID',
            issue_date__gte=mtd_start,
        ).aggregate(
            total=Sum('total_excl')  # Exclude GST for revenue
        )['total'] or Decimal('0.00')
        
        # YTD: Current year paid invoices
        ytd_start = date(today.year, 1, 1)
        ytd_revenue = InvoiceDocument.objects.filter(
            org=org,
            document_type='SALES_INVOICE',
            status='PAID',
            issue_date__gte=ytd_start,
        ).aggregate(
            total=Sum('total_excl')
        )['total'] or Decimal('0.00')
        
        return {
            'revenue_mtd': cls._format_currency(mtd_revenue),
            'revenue_ytd': cls._format_currency(ytd_revenue),
        }
    
    @classmethod
    def _get_gst_threshold_metrics(cls, org: Organisation) -> Dict[str, Any]:
        """
        Calculate GST registration threshold monitoring.
        
        Singapore requires GST registration if taxable turnover
        exceeds S$1 million in the past 12 months.
        """
        # Calculate rolling 12-month revenue from paid invoices
        twelve_months_ago = date.today() - timedelta(days=365)
        
        annual_revenue = InvoiceDocument.objects.filter(
            org=org,
            document_type='SALES_INVOICE',
            status='PAID',
            issue_date__gte=twelve_months_ago,
        ).aggregate(
            total=Sum('total_excl')  # Taxable turnover excludes GST
        )['total'] or Decimal('0.00')
        
        # Calculate utilization percentage
        utilization = min(
            int((annual_revenue / cls.GST_THRESHOLD_LIMIT) * 100),
            100
        )
        
        # Determine status
        if utilization >= 100:
            status = 'EXCEEDED'
        elif utilization >= 90:
            status = 'CRITICAL'
        elif utilization >= 75:
            status = 'WARNING'
        else:
            status = 'SAFE'
        
        return {
            'gst_threshold_status': status,
            'gst_threshold_utilization': utilization,
            'gst_threshold_amount': cls._format_currency(annual_revenue),
            'gst_threshold_limit': cls._format_currency(cls.GST_THRESHOLD_LIMIT),
        }
    
    @classmethod
    def _get_compliance_alerts(cls, org: Organisation) -> List[Dict[str, Any]]:
        """Generate compliance alerts based on organisation state."""
        alerts = []
        today = date.today()
        
        # Check GST filing deadline
        current_period = cls._get_current_gst_period(org)
        if current_period['days_remaining'] <= 7:
            alerts.append({
                'id': f"gst-filing-{today.isoformat()}",
                'severity': 'HIGH',
                'title': 'GST F5 Filing Due Soon',
                'message': f"Your GST F5 return is due in {current_period['days_remaining']} days",
                'action_required': 'File GST F5 return',
                'deadline': current_period['filing_due_date'],
                'dismissed': False,
            })
        elif current_period['days_remaining'] <= 30:
            alerts.append({
                'id': f"gst-filing-{today.isoformat()}",
                'severity': 'MEDIUM',
                'title': 'GST F5 Filing Approaching',
                'message': f"Your GST F5 return is due in {current_period['days_remaining']} days",
                'action_required': 'Prepare GST F5 return',
                'deadline': current_period['filing_due_date'],
                'dismissed': False,
            })
        
        # Check overdue invoices
        overdue_count = InvoiceDocument.objects.filter(
            org=org,
            document_type='SALES_INVOICE',
            status='OVERDUE',
        ).count()
        
        if overdue_count > 0:
            alerts.append({
                'id': f"overdue-invoices-{today.isoformat()}",
                'severity': 'HIGH' if overdue_count >= 5 else 'MEDIUM',
                'title': f'{overdue_count} Invoice{"s" if overdue_count > 1 else ""} Overdue',
                'message': f'You have {overdue_count} invoice{"s" if overdue_count > 1 else ""} that {"are" if overdue_count > 1 else "is"} past their due date',
                'action_required': 'Follow up on overdue invoices',
                'dismissed': False,
            })
        
        # Check GST threshold
        threshold_metrics = cls._get_gst_threshold_metrics(org)
        if threshold_metrics['gst_threshold_status'] == 'CRITICAL':
            alerts.append({
                'id': f"gst-threshold-{today.isoformat()}",
                'severity': 'CRITICAL',
                'title': 'GST Registration Threshold Approaching',
                'message': f"Your taxable turnover is at {threshold_metrics['gst_threshold_utilization']}% of the GST registration threshold",
                'action_required': 'Monitor and prepare for GST registration',
                'dismissed': False,
            })
        elif threshold_metrics['gst_threshold_status'] == 'WARNING':
            alerts.append({
                'id': f"gst-threshold-{today.isoformat()}",
                'severity': 'MEDIUM',
                'title': 'GST Registration Threshold Monitor',
                'message': f"Your taxable turnover is at {threshold_metrics['gst_threshold_utilization']}% of the GST registration threshold",
                'action_required': 'Review turnover projections',
                'dismissed': False,
            })
        
        return alerts
    
    @classmethod
    def _get_invoice_metrics(cls, org: Organisation) -> Dict[str, int]:
        """Get invoice statistics."""
        today = date.today()
        
        # Pending: SENT invoices not yet due (excluding OVERDUE)
        pending_count = InvoiceDocument.objects.filter(
            org=org,
            document_type='SALES_INVOICE',
            status='SENT',
            due_date__gte=today,
        ).count()
        
        # Overdue: Status is OVERDUE or SENT with past due date
        overdue_count = InvoiceDocument.objects.filter(
            org=org,
            document_type='SALES_INVOICE',
            status='OVERDUE',
        ).count()
        
        # Peppol pending: SENT invoices with Peppol not acknowledged
        peppol_pending = InvoiceDocument.objects.filter(
            org=org,
            document_type='SALES_INVOICE',
            invoicenow_status='PENDING',
        ).count()
        
        return {
            'invoices_pending': pending_count,
            'invoices_overdue': overdue_count,
            'invoices_peppol_pending': peppol_pending,
        }
    
    @classmethod
    def _get_current_gst_period(cls, org: Organisation) -> Dict[str, Any]:
        """Get current GST period information."""
        today = date.today()
        
        # Try to find current fiscal period
        try:
            current_period = FiscalPeriod.objects.filter(
                org=org,
                start_date__lte=today,
                end_date__gte=today,
                is_open=True,
            ).first()
            
            if current_period:
                # Filing due date is typically 1 month after period end
                filing_due = current_period.end_date + timedelta(days=30)
                days_remaining = (filing_due - today).days
                
                return {
                    'start_date': current_period.start_date.isoformat(),
                    'end_date': current_period.end_date.isoformat(),
                    'filing_due_date': filing_due.isoformat(),
                    'days_remaining': max(0, days_remaining),
                }
        except Exception:
            pass
        
        # Fallback: Calculate based on current quarter
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        quarter_end_month = quarter_start_month + 2
        
        start_date = date(today.year, quarter_start_month, 1)
        if quarter_end_month == 12:
            end_date = date(today.year, 12, 31)
        else:
            end_date = date(today.year, quarter_end_month + 1, 1) - timedelta(days=1)
        
        filing_due = end_date + timedelta(days=30)
        days_remaining = (filing_due - today).days
        
        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'filing_due_date': filing_due.isoformat(),
            'days_remaining': max(0, days_remaining),
        }
    
    @classmethod
    def _format_currency(cls, value: Decimal) -> str:
        """Format decimal as currency string with commas."""
        return f"{value:,.2f}"
    
    @classmethod
    def _get_iso_timestamp(cls) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
