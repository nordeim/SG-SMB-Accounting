"""
Invoicing views for LedgerSG.

Contact management and document (invoice/quote) operations.
"""

from typing import Optional
from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.core.permissions import (
    IsOrgMember, CanCreateInvoices, CanApproveInvoices, 
    CanVoidInvoices, CanViewReports
)
from apps.core.models import Contact, InvoiceDocument
from common.exceptions import ValidationError, ResourceNotFound
from common.views import wrap_response

from apps.invoicing.services import ContactService, DocumentService, STATUS_TRANSITIONS
from apps.invoicing.serializers import (
    ContactListSerializer,
    ContactDetailSerializer,
    ContactCreateSerializer,
    ContactUpdateSerializer,
    InvoiceDocumentListSerializer,
    InvoiceDocumentDetailSerializer,
    InvoiceDocumentCreateSerializer,
    InvoiceDocumentUpdateSerializer,
    InvoiceLineCreateSerializer,
    StatusTransitionSerializer,
    QuoteConversionSerializer,
    DocumentSummarySerializer,
)


class ContactListCreateView(APIView):
    """
    GET: List contacts
    POST: Create contact
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """List contacts with filters."""
        is_customer = request.query_params.get("is_customer")
        is_supplier = request.query_params.get("is_supplier")
        is_active = request.query_params.get("is_active", "true")
        search = request.query_params.get("search")
        
        # Parse booleans
        if is_customer is not None:
            is_customer = is_customer.lower() == "true"
        if is_supplier is not None:
            is_supplier = is_supplier.lower() == "true"
        is_active = is_active.lower() == "true"
        
        from uuid import UUID
        contacts = ContactService.list_contacts(
            org_id=UUID(org_id),
            is_customer=is_customer,
            is_supplier=is_supplier,
            is_active=is_active,
            search=search
        )
        
        serializer = ContactListSerializer(contacts, many=True)
        return Response({
            "data": serializer.data,
            "count": len(serializer.data)
        })
    
    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Create new contact."""
        serializer = ContactCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from uuid import UUID
        contact = ContactService.create_contact(
            org_id=UUID(org_id),
            **serializer.validated_data
        )
        
        return Response(
            ContactDetailSerializer(contact).data,
            status=status.HTTP_201_CREATED
        )


class ContactDetailView(APIView):
    """
    GET: Get contact details
    PATCH: Update contact
    DELETE: Deactivate contact
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    @wrap_response
    def get(self, request, org_id: str, contact_id: str) -> Response:
        """Get contact details."""
        from uuid import UUID
        contact = ContactService.get_contact(UUID(org_id), UUID(contact_id))
        return Response(ContactDetailSerializer(contact).data)
    
    @wrap_response
    def patch(self, request, org_id: str, contact_id: str) -> Response:
        """Update contact."""
        from uuid import UUID
        
        serializer = ContactUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact = ContactService.update_contact(
            UUID(org_id),
            UUID(contact_id),
            **serializer.validated_data
        )
        
        return Response(ContactDetailSerializer(contact).data)
    
    @wrap_response
    def delete(self, request, org_id: str, contact_id: str) -> Response:
        """Deactivate contact."""
        from uuid import UUID
        contact = ContactService.deactivate_contact(UUID(org_id), UUID(contact_id))
        
        return Response({
            "message": "Contact deactivated",
            "contact": ContactDetailSerializer(contact).data
        })


class InvoiceDocumentListCreateView(APIView):
    """
    GET: List documents
    POST: Create document
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """List documents with filters."""
        doc_type = request.query_params.get("type")
        status_filter = request.query_params.get("status")
        contact_id = request.query_params.get("contact_id")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        search = request.query_params.get("search")
        
        from uuid import UUID
        
        if contact_id:
            contact_id = UUID(contact_id)
        
        documents = DocumentService.list_documents(
            org_id=UUID(org_id),
            document_type=doc_type,
            status=status_filter,
            contact_id=contact_id,
            date_from=date_from,
            date_to=date_to,
            search=search
        )
        
        serializer = InvoiceDocumentListSerializer(documents, many=True)
        return Response({
            "data": serializer.data,
            "count": len(serializer.data)
        })
    
    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Create new document."""
        # Check permission
        self._check_permission(request, "can_create_invoices")
        
        serializer = InvoiceDocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from uuid import UUID
        data = serializer.validated_data
        
        document = DocumentService.create_document(
            org_id=UUID(org_id),
            document_type=data["document_type"],
            contact_id=data["contact_id"],
            issue_date=data["issue_date"],
            due_date=data.get("due_date"),
            reference=data.get("reference", ""),
            notes=data.get("notes", ""),
            lines=data["lines"],
            user_id=request.user.id
        )
        
        return Response(
            InvoiceDocumentDetailSerializer(document).data,
            status=status.HTTP_201_CREATED
        )
    
    def _check_permission(self, request, permission: str) -> bool:
        """Check if user has specific permission."""
        org_role = getattr(request, "org_role", {})
        if org_role.get(permission) or getattr(request.user, "is_superadmin", False):
            return True
        from common.exceptions import UnauthorizedOrgAccess
        raise UnauthorizedOrgAccess("Insufficient permissions")


class InvoiceDocumentDetailView(APIView):
    """
    GET: Get document details
    PATCH: Update document (DRAFT only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    @wrap_response
    def get(self, request, org_id: str, document_id: str) -> Response:
        """Get document details."""
        from uuid import UUID
        document = DocumentService.get_document(UUID(org_id), UUID(document_id))
        return Response(InvoiceDocumentDetailSerializer(document).data)
    
    @wrap_response
    def patch(self, request, org_id: str, document_id: str) -> Response:
        """Update document."""
        self._check_permission(request, "can_create_invoices")
        
        from uuid import UUID
        serializer = InvoiceDocumentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        document = DocumentService.update_document(
            UUID(org_id),
            UUID(document_id),
            **serializer.validated_data
        )
        
        return Response(InvoiceDocumentDetailSerializer(document).data)
    
    def _check_permission(self, request, permission: str) -> bool:
        """Check if user has specific permission."""
        org_role = getattr(request, "org_role", {})
        if org_role.get(permission) or getattr(request.user, "is_superadmin", False):
            return True
        from common.exceptions import UnauthorizedOrgAccess
        raise UnauthorizedOrgAccess("Insufficient permissions")


class InvoiceDocumentStatusView(APIView):
    """
    POST: Transition document status
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    @wrap_response
    def post(self, request, org_id: str, document_id: str) -> Response:
        """Transition document status."""
        from uuid import UUID
        
        serializer = StatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data["status"]
        
        # Check permission based on target status
        if new_status == "APPROVED":
            self._check_permission(request, "can_approve_invoices")
        elif new_status == "VOIDED":
            self._check_permission(request, "can_void_invoices")
        
        document = DocumentService.transition_status(
            UUID(org_id),
            UUID(document_id),
            new_status,
            user_id=request.user.id
        )
        
        return Response({
            "message": f"Status changed to {new_status}",
            "document": InvoiceDocumentDetailSerializer(document).data
        })
    
    def _check_permission(self, request, permission: str) -> bool:
        """Check if user has specific permission."""
        org_role = getattr(request, "org_role", {})
        if org_role.get(permission) or getattr(request.user, "is_superadmin", False):
            return True
        from common.exceptions import UnauthorizedOrgAccess
        raise UnauthorizedOrgAccess("Insufficient permissions")


class InvoiceLineAddView(APIView):
    """
    POST: Add line to document
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanCreateInvoices]
    
    @wrap_response
    def post(self, request, org_id: str, document_id: str) -> Response:
        """Add line to document."""
        from uuid import UUID
        
        serializer = InvoiceLineCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        line = DocumentService.add_line(
            org_id=UUID(org_id),
            document_id=UUID(document_id),
            account_id=data["account_id"],
            description=data["description"],
            quantity=data.get("quantity", 1),
            unit_price=data["unit_price"],
            tax_code_id=data["tax_code_id"],
            is_bcrs_deposit=data.get("is_bcrs_deposit", False)
        )
        
        from apps.invoicing.serializers import InvoiceLineSerializer
        return Response({
            "message": "Line added",
            "line": InvoiceLineSerializer(line).data
        }, status=status.HTTP_201_CREATED)


class InvoiceLineRemoveView(APIView):
    """
    DELETE: Remove line from document
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanCreateInvoices]
    
    @wrap_response
    def delete(self, request, org_id: str, document_id: str, line_id: str) -> Response:
        """Remove line from document."""
        from uuid import UUID
        
        DocumentService.remove_line(
            UUID(org_id),
            UUID(document_id),
            UUID(line_id)
        )
        
        return Response({"message": "Line removed"})


class QuoteConvertView(APIView):
    """
    POST: Convert quote to invoice
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanCreateInvoices]
    
    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Convert quote to invoice."""
        from uuid import UUID
        
        serializer = QuoteConversionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        invoice = DocumentService.convert_quote_to_invoice(
            UUID(org_id),
            serializer.validated_data["quote_id"],
            user_id=request.user.id
        )
        
        return Response({
            "message": "Quote converted to invoice",
            "invoice": InvoiceDocumentDetailSerializer(invoice).data
        }, status=status.HTTP_201_CREATED)


class DocumentSummaryView(APIView):
    """
    GET: Get document summary statistics
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember, CanViewReports]
    
    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """Get document summary."""
        from uuid import UUID
        from decimal import Decimal
        
        # Get counts by status
        status_counts = {}
        for status, _ in InvoiceDocument.STATUS_CHOICES:
            count = InvoiceDocument.objects.filter(
                org_id=org_id,
                status=status
            ).count()
            if count > 0:
                status_counts[status] = count
        
        # Get counts by type
        type_counts = {}
        for doc_type, _ in InvoiceDocument.DOCUMENT_TYPE_CHOICES:
            count = InvoiceDocument.objects.filter(
                org_id=org_id,
                document_type=doc_type
            ).count()
            if count > 0:
                type_counts[doc_type] = count
        
        # Get total outstanding
        outstanding = InvoiceDocument.objects.filter(
            org_id=org_id,
            status__in=["APPROVED", "PAID_PARTIAL"]
        )
        total_outstanding = sum(doc.total for doc in outstanding)
        
        # Get overdue count
        overdue_count = InvoiceDocument.objects.filter(
            org_id=org_id,
            status__in=["APPROVED", "PAID_PARTIAL"],
            due_date__lt=date.today()
        ).count()
        
        return Response({
            "total_count": InvoiceDocument.objects.filter(org_id=org_id).count(),
            "by_status": status_counts,
            "by_type": type_counts,
            "total_outstanding": str(total_outstanding.quantize(Decimal("0.01"))),
            "overdue_count": overdue_count
        })


class ValidStatusTransitionsView(APIView):
    """
    GET: Get valid status transitions
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @wrap_response
    def get(self, request) -> Response:
        """Get valid status transitions."""
        return Response({
            "transitions": STATUS_TRANSITIONS
        })
