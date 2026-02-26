"""
Organisation views for LedgerSG.

Organisation CRUD, GST registration, fiscal year management.
"""

from datetime import date
from typing import List

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import connection

from apps.core.serializers import (
    OrganisationSerializer,
    OrganisationCreateSerializer,
    GSTRegistrationSerializer,
    FiscalYearSerializer,
)
from apps.core.services import organisation_service
from apps.core.permissions import (
    IsOrgMember,
    CanManageOrg,
    CanCreateJournals,
    CanViewReports,
)
from apps.core.models import (
    Organisation,
    FiscalYear,
    FiscalPeriod,
    Account,
)
from common.exceptions import ValidationError, DuplicateResource, UnauthorizedOrgAccess
from common.views import wrap_response


class OrganisationListCreateView(APIView):
    """
    GET: List user's organisations
    POST: Create new organisation
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @wrap_response
    def get(self, request) -> Response:
        """List organisations where user is a member."""
        orgs = Organisation.objects.filter(
            user_memberships__user=request.user
        ).distinct()
        
        serializer = OrganisationSerializer(orgs, many=True)
        return Response({
            "data": serializer.data,
            "count": len(serializer.data)
        })
    
    @wrap_response
    def post(self, request) -> Response:
        """Create new organisation with full setup."""
        serializer = OrganisationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create organisation
        org = organisation_service.create_organisation(
            user=request.user,
            **serializer.validated_data
        )
        
        return Response(
            OrganisationSerializer(org).data,
            status=status.HTTP_201_CREATED
        )


class OrganisationDetailView(APIView):
    """
    GET: Get organisation details
    PATCH: Update organisation
    DELETE: Deactivate organisation (soft delete)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """Get organisation details."""
        org = self._get_org(org_id)
        serializer = OrganisationSerializer(org)
        
        # Add additional data
        data = serializer.data
        data["member_count"] = org.user_memberships.count()
        data["fiscal_year_count"] = org.fiscalyear_set.count()
        data["account_count"] = org.account_set.filter(is_system=False).count()
        
        return Response(data)
    
    @wrap_response
    def patch(self, request, org_id: str) -> Response:
        """Update organisation settings."""
        org = self._get_org(org_id)
        
        # Check permission
        self._check_permission(request, "can_manage_org")
        
        # Update allowed fields
        allowed_fields = [
            "name", "legal_name", "uen", "entity_type",
            "address", "contact_email", "contact_phone",
            "base_currency", "peppol_participant_id", "invoicenow_enabled"
        ]
        
        updates = {
            k: v for k, v in request.data.items()
            if k in allowed_fields
        }
        
        org = organisation_service.update_organisation(org, **updates)
        return Response(OrganisationSerializer(org).data)
    
    @wrap_response
    def delete(self, request, org_id: str) -> Response:
        """Deactivate organisation (soft delete)."""
        org = self._get_org(org_id)
        
        # Check permission
        self._check_permission(request, "can_manage_org")
        
        # Deactivate
        org.is_active = False
        org.save()
        
        return Response(
            {"message": "Organisation deactivated successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
    
    def _get_org(self, org_id: str) -> Organisation:
        """Get organisation by ID or raise 404."""
        try:
            return Organisation.objects.get(id=org_id)
        except Organisation.DoesNotExist:
            raise UnauthorizedOrgAccess("Organisation not found")
    
    def _check_permission(self, request, permission: str) -> bool:
        """Check if user has specific permission."""
        org_role = getattr(request, "org_role", {})
        if org_role.get(permission) or getattr(request.user, "is_superadmin", False):
            return True
        raise UnauthorizedOrgAccess("Insufficient permissions")


class GSTRegistrationView(APIView):
    """
    POST: Register for GST
    DELETE: Deregister from GST
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanManageOrg]
    
    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Register organisation for GST."""
        org = self._get_org(org_id)
        
        serializer = GSTRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        org = organisation_service.toggle_gst_registration(
            org,
            registered=True,
            reg_number=serializer.validated_data["gst_reg_number"],
            reg_date=serializer.validated_data["gst_reg_date"]
        )
        
        return Response(OrganisationSerializer(org).data)
    
    @wrap_response
    def delete(self, request, org_id: str) -> Response:
        """Deregister from GST."""
        org = self._get_org(org_id)
        
        org = organisation_service.toggle_gst_registration(org, registered=False)
        
        return Response(OrganisationSerializer(org).data)
    
    def _get_org(self, org_id: str) -> Organisation:
        """Get organisation by ID or raise 404."""
        try:
            return Organisation.objects.get(id=org_id)
        except Organisation.DoesNotExist:
            raise UnauthorizedOrgAccess("Organisation not found")


class FiscalYearListView(APIView):
    """
    GET: List fiscal years
    POST: Create new fiscal year
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanCreateJournals]
    
    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """List fiscal years for organisation."""
        fiscal_years = FiscalYear.objects.filter(
            org_id=org_id
        ).order_by("-start_date")
        
        serializer = FiscalYearSerializer(fiscal_years, many=True)
        return Response({
            "data": serializer.data,
            "count": len(serializer.data)
        })


class OrganisationSummaryView(APIView):
    """
    GET: Get organisation summary/dashboard data
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanViewReports]
    
    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """Get organisation summary."""
        org = Organisation.objects.get(id=org_id)
        
        # Get current fiscal year
        current_fy = FiscalYear.objects.filter(
            org_id=org_id,
            is_closed=False
        ).order_by("start_date").first()
        
        # Get open periods count
        open_periods = FiscalPeriod.objects.filter(
            org_id=org_id,
            is_open=True
        ).count()
        
        # Get account counts
        total_accounts = Account.objects.filter(org_id=org_id).count()
        active_accounts = Account.objects.filter(
            org_id=org_id, is_active=True
        ).count()
        
        # Get member count
        member_count = org.user_memberships.count()
        
        return Response({
            "organisation": OrganisationSerializer(org).data,
            "current_fiscal_year": FiscalYearSerializer(current_fy).data if current_fy else None,
            "open_periods": open_periods,
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "member_count": member_count,
        })
