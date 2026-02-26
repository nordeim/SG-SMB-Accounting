"""
Reporting views for LedgerSG.

Dashboard metrics and alerts API.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status

from apps.core.permissions import IsOrgMember, CanViewReports
from common.views import wrap_response
from common.exceptions import ValidationError


class DashboardMetricsView(APIView):
    """
    GET: Dashboard metrics.

    Returns key financial metrics for the dashboard.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """Return dashboard metrics (stub implementation)."""
        # TODO: Implement actual metrics calculation
        # For now, return placeholder data

        from datetime import date
        from uuid import UUID

        return Response(
            {
                "period": {
                    "start": str(date.today().replace(day=1)),
                    "end": str(date.today()),
                },
                "revenue": {
                    "current_month": "0.00",
                    "previous_month": "0.00",
                    "change": "0.00",
                    "change_pct": "0.00",
                },
                "expenses": {
                    "current_month": "0.00",
                    "previous_month": "0.00",
                    "change": "0.00",
                    "change_pct": "0.00",
                },
                "profit": {
                    "current_month": "0.00",
                    "previous_month": "0.00",
                    "change": "0.00",
                    "change_pct": "0.00",
                },
                "outstanding": {
                    "total": "0.00",
                    "count": 0,
                    "overdue": "0.00",
                    "overdue_count": 0,
                },
                "bank_balance": {
                    "total": "0.00",
                    "accounts": [],
                },
                "gst_summary": {
                    "registered": False,
                    "next_filing_date": None,
                    "next_filing_amount": "0.00",
                },
                "invoice_summary": {
                    "draft": 0,
                    "sent": 0,
                    "approved": 0,
                    "paid": 0,
                    "overdue": 0,
                    "void": 0,
                },
            }
        )


class DashboardAlertsView(APIView):
    """
    GET: Dashboard alerts.

    Returns active alerts and warnings.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """Return dashboard alerts (stub implementation)."""

        # TODO: Implement actual alerts calculation
        # For now, return placeholder data

        return Response(
            {
                "alerts": [],
                "gst_threshold_warning": False,
                "gst_threshold_amount": "1000000.00",
                "overdue_invoices_count": 0,
                "unreconciled_transactions_count": 0,
                "unpaid_bills_count": 0,
                "upcoming_deadlines": [],
            }
        )


class FinancialReportView(APIView):
    """
    GET: Financial reports (P&L, Balance Sheet).

    Returns financial reports for the organization.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanViewReports]

    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """Return financial reports (stub implementation)."""

        report_type = request.query_params.get("type", "profit_loss")

        if report_type not in ["profit_loss", "balance_sheet", "trial_balance"]:
            raise ValidationError(f"Invalid report type: {report_type}")

        # TODO: Implement actual report generation
        # For now, return placeholder data

        return Response(
            {
                "report_type": report_type,
                "period_start": "2024-01-01",
                "period_end": "2024-12-31",
                "currency": "SGD",
                "generated_at": "2024-01-01T00:00:00Z",
                "data": {
                    "summary": {},
                    "accounts": [],
                    "totals": {
                        "debit": "0.00",
                        "credit": "0.00",
                    },
                },
            }
        )
