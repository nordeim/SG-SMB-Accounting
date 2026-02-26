"""
Banking views for LedgerSG.

Bank accounts and payments API.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status

from apps.core.permissions import IsOrgMember
from common.views import wrap_response


class BankAccountListView(APIView):
    """
    GET: List bank accounts.
    POST: Create bank account.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """List bank accounts (stub implementation)."""
        # TODO: Implement actual bank account listing
        return Response(
            {
                "results": [],
                "count": 0,
                "next": None,
                "previous": None,
            }
        )

    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Create bank account (stub implementation)."""
        # TODO: Implement actual bank account creation
        return Response(
            {
                "id": "bank-account-uuid",
                "org_id": org_id,
                "account_name": request.data.get("account_name", ""),
                "account_number": request.data.get("account_number", ""),
                "bank_name": request.data.get("bank_name", ""),
                "currency": request.data.get("currency", "SGD"),
                "current_balance": "0.00",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
            },
            status=status.HTTP_201_CREATED,
        )


class BankAccountDetailView(APIView):
    """
    GET: Get bank account details.
    PATCH: Update bank account.
    DELETE: Deactivate bank account.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str, account_id: str) -> Response:
        """Get bank account details (stub implementation)."""
        # TODO: Implement actual bank account retrieval
        return Response(
            {
                "id": account_id,
                "org_id": org_id,
                "account_name": "Main Account",
                "account_number": "1234567890",
                "bank_name": "DBS Bank",
                "currency": "SGD",
                "current_balance": "0.00",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
            }
        )

    @wrap_response
    def patch(self, request, org_id: str, account_id: str) -> Response:
        """Update bank account (stub implementation)."""
        # TODO: Implement actual bank account update
        return Response(
            {
                "id": account_id,
                "org_id": org_id,
                "account_name": request.data.get("account_name", "Main Account"),
                "updated_at": "2024-01-01T00:00:00Z",
            }
        )

    @wrap_response
    def delete(self, request, org_id: str, account_id: str) -> Response:
        """Deactivate bank account (stub implementation)."""
        # TODO: Implement actual bank account deactivation
        return Response(
            {
                "message": "Bank account deactivated",
                "id": account_id,
            }
        )


class PaymentListView(APIView):
    """
    GET: List payments.
    POST: Create payment.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """List payments (stub implementation)."""
        # TODO: Implement actual payment listing
        return Response(
            {
                "results": [],
                "count": 0,
                "next": None,
                "previous": None,
            }
        )

    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Create payment (stub implementation)."""
        # TODO: Implement actual payment creation
        return Response(
            {
                "id": "payment-uuid",
                "org_id": org_id,
                "payment_type": request.data.get("payment_type", "RECEIVE"),
                "amount": request.data.get("amount", "0.00"),
                "currency": request.data.get("currency", "SGD"),
                "description": request.data.get("description", ""),
                "payment_date": request.data.get("payment_date", "2024-01-01"),
                "status": "PENDING",
                "created_at": "2024-01-01T00:00:00Z",
            },
            status=status.HTTP_201_CREATED,
        )


class ReceivePaymentView(APIView):
    """
    POST: Receive payment from customer.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Receive payment from customer (stub implementation)."""
        # TODO: Implement actual payment receipt
        return Response(
            {
                "id": "payment-uuid",
                "org_id": org_id,
                "payment_type": "RECEIVE",
                "amount": request.data.get("amount", "0.00"),
                "customer_id": request.data.get("customer_id"),
                "invoice_ids": request.data.get("invoice_ids", []),
                "description": request.data.get("description", ""),
                "payment_method": request.data.get("payment_method", "BANK_TRANSFER"),
                "reference_number": request.data.get("reference_number", ""),
                "status": "COMPLETED",
                "created_at": "2024-01-01T00:00:00Z",
            }
        )


class MakePaymentView(APIView):
    """
    POST: Make payment to supplier.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Make payment to supplier (stub implementation)."""
        # TODO: Implement actual payment processing
        return Response(
            {
                "id": "payment-uuid",
                "org_id": org_id,
                "payment_type": "MAKE",
                "amount": request.data.get("amount", "0.00"),
                "supplier_id": request.data.get("supplier_id"),
                "bill_ids": request.data.get("bill_ids", []),
                "description": request.data.get("description", ""),
                "payment_method": request.data.get("payment_method", "BANK_TRANSFER"),
                "reference_number": request.data.get("reference_number", ""),
                "status": "PENDING",
                "created_at": "2024-01-01T00:00:00Z",
            }
        )
