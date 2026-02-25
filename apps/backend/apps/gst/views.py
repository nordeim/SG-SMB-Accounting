"""
GST views for LedgerSG.

Tax code management, GST calculation, and GST return filing.
"""

from typing import Optional

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.core.permissions import IsOrgMember, CanManageCoA, CanFileGST, CanViewReports
from apps.core.models import TaxCode, GSTReturn
from common.exceptions import ValidationError, ResourceNotFound
from common.views import wrap_response
from common.decimal_utils import money

from apps.gst.services import (
    TaxCodeService,
    GSTCalculationService,
    GSTReturnService,
)
from apps.gst.serializers import (
    TaxCodeListSerializer,
    TaxCodeDetailSerializer,
    TaxCodeCreateSerializer,
    TaxCodeUpdateSerializer,
    GSTCalculationRequestSerializer,
    GSTCalculationResponseSerializer,
    DocumentGSTCalculationSerializer,
    DocumentGSTSummarySerializer,
    GSTReturnListSerializer,
    GSTReturnDetailSerializer,
    GSTReturnCreateSerializer,
    GSTReturnFileSerializer,
    GSTReturnAmendSerializer,
    GSTReturnPaymentSerializer,
)


class TaxCodeListCreateView(APIView):
    """
    GET: List tax codes
    POST: Create custom tax code
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """List tax codes."""
        is_active = request.query_params.get("is_active")
        is_gst_charged = request.query_params.get("is_gst_charged")
        include_system = request.query_params.get("include_system", "true").lower() == "true"
        
        if is_active is not None:
            is_active = is_active.lower() == "true"
        if is_gst_charged is not None:
            is_gst_charged = is_gst_charged.lower() == "true"
        
        from uuid import UUID
        tax_codes = TaxCodeService.list_tax_codes(
            org_id=UUID(org_id),
            is_active=is_active,
            is_gst_charged=is_gst_charged,
            include_system=include_system
        )
        
        serializer = TaxCodeListSerializer(tax_codes, many=True)
        return Response({
            "data": serializer.data,
            "count": len(serializer.data)
        })
    
    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Create custom tax code."""
        # Check permission
        self._check_permission(request, "can_manage_coa")
        
        serializer = TaxCodeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from uuid import UUID
        from decimal import Decimal
        
        data = serializer.validated_data
        rate = data.get("rate")
        if rate is not None:
            rate = Decimal(str(rate))
        
        tax_code = TaxCodeService.create_tax_code(
            org_id=UUID(org_id),
            code=data["code"],
            name=data["name"],
            rate=rate,
            is_gst_charged=data["is_gst_charged"],
            description=data.get("description", ""),
            box_mapping=data.get("box_mapping") or None
        )
        
        return Response(
            TaxCodeDetailSerializer(tax_code).data,
            status=status.HTTP_201_CREATED
        )
    
    def _check_permission(self, request, permission: str) -> bool:
        """Check if user has specific permission."""
        org_role = getattr(request, "org_role", {})
        if org_role.get(permission) or getattr(request.user, "is_superadmin", False):
            return True
        from common.exceptions import UnauthorizedOrgAccess
        raise UnauthorizedOrgAccess("Insufficient permissions")


class TaxCodeDetailView(APIView):
    """
    GET: Get tax code details
    PATCH: Update tax code
    DELETE: Deactivate tax code
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    @wrap_response
    def get(self, request, org_id: str, tax_code_id: str) -> Response:
        """Get tax code details."""
        from uuid import UUID
        tax_code = TaxCodeService.get_tax_code(UUID(org_id), UUID(tax_code_id))
        return Response(TaxCodeDetailSerializer(tax_code).data)
    
    @wrap_response
    def patch(self, request, org_id: str, tax_code_id: str) -> Response:
        """Update tax code."""
        self._check_permission(request, "can_manage_coa")
        
        from uuid import UUID
        serializer = TaxCodeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tax_code = TaxCodeService.update_tax_code(
            UUID(org_id),
            UUID(tax_code_id),
            **serializer.validated_data
        )
        
        return Response(TaxCodeDetailSerializer(tax_code).data)
    
    @wrap_response
    def delete(self, request, org_id: str, tax_code_id: str) -> Response:
        """Deactivate tax code."""
        self._check_permission(request, "can_manage_coa")
        
        from uuid import UUID
        tax_code = TaxCodeService.deactivate_tax_code(UUID(org_id), UUID(tax_code_id))
        
        return Response({
            "message": "Tax code deactivated",
            "tax_code": TaxCodeDetailSerializer(tax_code).data
        })
    
    def _check_permission(self, request, permission: str) -> bool:
        """Check if user has specific permission."""
        org_role = getattr(request, "org_role", {})
        if org_role.get(permission) or getattr(request.user, "is_superadmin", False):
            return True
        from common.exceptions import UnauthorizedOrgAccess
        raise UnauthorizedOrgAccess("Insufficient permissions")


class TaxCodeIrasInfoView(APIView):
    """
    GET: Get IRAS-defined tax code information
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @wrap_response
    def get(self, request) -> Response:
        """Get IRAS tax code definitions."""
        info = TaxCodeService.get_iras_tax_codes_info()
        return Response({
            "data": info,
            "count": len(info)
        })


class GSTCalculateView(APIView):
    """
    POST: Calculate GST for a line item
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @wrap_response
    def post(self, request) -> Response:
        """Calculate GST for a line."""
        serializer = GSTCalculationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        amount = money(data["amount"])
        is_bcrs = data.get("is_bcrs_deposit", False)
        
        # Get rate from tax code or use provided rate
        if data.get("tax_code_id"):
            from uuid import UUID
            tax_code = TaxCodeService.get_tax_code_by_code(
                UUID(request.data.get("org_id", "00000000-0000-0000-0000-000000000000")),
                str(data["tax_code_id"])  # Actually expects code, not ID
            )
            rate = tax_code.rate if tax_code else Decimal("0.09")
        else:
            from decimal import Decimal
            rate = Decimal(str(data.get("rate", "0.09")))
        
        result = GSTCalculationService.calculate_line_gst(
            amount=amount,
            rate=rate,
            is_bcrs_deposit=is_bcrs
        )
        
        return Response({
            "net_amount": str(result["net_amount"]),
            "gst_amount": str(result["gst_amount"]),
            "total_amount": str(result["total_amount"]),
            "rate": str(rate) if rate else "0.00",
            "is_bcrs_exempt": result["is_bcrs_exempt"]
        })


class GSTCalculateDocumentView(APIView):
    """
    POST: Calculate GST for a document with multiple lines
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @wrap_response
    def post(self, request) -> Response:
        """Calculate GST for a document."""
        serializer = DocumentGSTCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        from decimal import Decimal
        default_rate = Decimal(str(data.get("default_rate", "0.09")))
        
        result = GSTCalculationService.calculate_document_gst(
            lines=data["lines"],
            default_rate=default_rate
        )
        
        return Response(result)


class GSTReturnListCreateView(APIView):
    """
    GET: List GST returns
    POST: Create GST return periods
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanFileGST]
    
    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """List GST returns."""
        status_filter = request.query_params.get("status")
        year = request.query_params.get("year")
        
        if year:
            year = int(year)
        
        from uuid import UUID
        returns = GSTReturnService.list_returns(
            org_id=UUID(org_id),
            status=status_filter,
            year=year
        )
        
        serializer = GSTReturnListSerializer(returns, many=True)
        return Response({
            "data": serializer.data,
            "count": len(serializer.data)
        })
    
    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Create GST return periods."""
        from datetime import date
        from uuid import UUID
        
        serializer = GSTReturnCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        created = GSTReturnService.create_return_periods(
            org_id=UUID(org_id),
            filing_frequency=data["filing_frequency"],
            start_date=data["start_date"],
            periods=data["periods"]
        )
        
        return Response({
            "message": f"Created {len(created)} return periods",
            "data": GSTReturnListSerializer(created, many=True).data
        }, status=status.HTTP_201_CREATED)


class GSTReturnDetailView(APIView):
    """
    GET: Get GST return details
    POST: Generate F5 data
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanFileGST]
    
    @wrap_response
    def get(self, request, org_id: str, return_id: str) -> Response:
        """Get GST return with F5 data."""
        from uuid import UUID
        gst_return = GSTReturnService.get_return(UUID(org_id), UUID(return_id))
        return Response(GSTReturnDetailSerializer(gst_return).data)
    
    @wrap_response
    def post(self, request, org_id: str, return_id: str) -> Response:
        """Generate/regenerate F5 data."""
        from uuid import UUID
        force = request.query_params.get("force", "false").lower() == "true"
        
        gst_return = GSTReturnService.generate_f5(
            org_id=UUID(org_id),
            return_id=UUID(return_id),
            force_recalculate=force
        )
        
        return Response(GSTReturnDetailSerializer(gst_return).data)


class GSTReturnFileView(APIView):
    """
    POST: File a GST return
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanFileGST]
    
    @wrap_response
    def post(self, request, org_id: str, return_id: str) -> Response:
        """File GST return."""
        from uuid import UUID
        from decimal import Decimal
        
        serializer = GSTReturnFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        boxes = data.get("boxes")
        if boxes:
            boxes = {
                k: Decimal(str(v)) for k, v in boxes.items()
            }
        
        gst_return = GSTReturnService.file_return(
            org_id=UUID(org_id),
            return_id=UUID(return_id),
            filed_by_id=request.user.id,
            filing_reference=data.get("filing_reference"),
            boxes=boxes
        )
        
        return Response({
            "message": "GST return filed successfully",
            "return": GSTReturnDetailSerializer(gst_return).data
        })


class GSTReturnAmendView(APIView):
    """
    POST: Mark return for amendment
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanFileGST]
    
    @wrap_response
    def post(self, request, org_id: str, return_id: str) -> Response:
        """Amend GST return."""
        from uuid import UUID
        
        serializer = GSTReturnAmendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        gst_return = GSTReturnService.amend_return(
            org_id=UUID(org_id),
            return_id=UUID(return_id),
            reason=serializer.validated_data["reason"]
        )
        
        return Response({
            "message": "GST return marked for amendment",
            "return": GSTReturnDetailSerializer(gst_return).data
        })


class GSTReturnPayView(APIView):
    """
    POST: Record payment for GST return
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanFileGST]
    
    @wrap_response
    def post(self, request, org_id: str, return_id: str) -> Response:
        """Record GST payment."""
        from uuid import UUID
        from decimal import Decimal
        
        serializer = GSTReturnPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        gst_return = GSTReturnService.pay_return(
            org_id=UUID(org_id),
            return_id=UUID(return_id),
            payment_date=data["payment_date"],
            payment_amount=Decimal(str(data["payment_amount"])),
            payment_reference=data["payment_reference"]
        )
        
        return Response({
            "message": "Payment recorded",
            "return": GSTReturnDetailSerializer(gst_return).data
        })


class GSTReturnDeadlinesView(APIView):
    """
    GET: Get upcoming filing deadlines
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """Get upcoming deadlines."""
        from uuid import UUID
        
        days = int(request.query_params.get("days", 30))
        
        deadlines = GSTReturnService.get_upcoming_deadlines(
            org_id=UUID(org_id),
            days=days
        )
        
        return Response({
            "data": GSTReturnListSerializer(deadlines, many=True).data,
            "count": len(deadlines)
        })
