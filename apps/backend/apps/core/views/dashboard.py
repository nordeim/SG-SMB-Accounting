"""
Dashboard API Views for LedgerSG.

Provides comprehensive dashboard data for the frontend.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.core.services.dashboard_service import DashboardService
from apps.core.permissions import IsOrgMember, CanViewReports
from common.exceptions import UnauthorizedOrgAccess
from common.views import wrap_response


class DashboardView(APIView):
    """
    GET: Get comprehensive dashboard data for an organisation.
    
    Returns aggregated metrics including:
    - GST payable and threshold monitoring
    - Cash on hand and outstanding receivables
    - Revenue (MTD and YTD)
    - Invoice statistics (pending, overdue)
    - Compliance alerts
    - Current GST period information
    
    Authentication: JWT Bearer token required
    Permission: User must be org member with can_view_reports
    """
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanViewReports]
    
    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """
        Get dashboard data for organisation.
        
        Args:
            request: HTTP request
            org_id: Organisation UUID from URL
            
        Returns:
            Response with dashboard metrics
        """
        # Get dashboard data from service
        data = DashboardService.get_dashboard_data(org_id)
        
        return Response(data, status=status.HTTP_200_OK)
