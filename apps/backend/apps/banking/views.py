"""
Banking views for LedgerSG.

SEC-001 Remediation: All stubs replaced with validated implementations.
Bank accounts, payments, and reconciliation API.
"""

from uuid import UUID
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.utils import timezone

from apps.core.permissions import IsOrgMember, CanManageBanking
from apps.banking.serializers import (
    BankAccountSerializer,
    BankAccountCreateSerializer,
    BankAccountUpdateSerializer,
    PaymentSerializer,
    PaymentReceiveSerializer,
    PaymentMakeSerializer,
    PaymentVoidSerializer,
    PaymentAllocationSerializer,
    AllocationCreateSerializer,
    BulkAllocationSerializer,
    BankTransactionSerializer,
    BankTransactionImportSerializer,
    BankTransactionReconcileSerializer,
)
from apps.banking.services import BankAccountService, PaymentService, ReconciliationService
from common.views import wrap_response
from common.exceptions import ValidationError as AppValidationError


class BankAccountListView(APIView):
    """
    GET: List bank accounts.
    POST: Create bank account.

    SEC-001 Remediation: Uses validated serializers and services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """List bank accounts for the organisation."""
        is_active = request.query_params.get("is_active")
        currency = request.query_params.get("currency")
        search = request.query_params.get("search")

        is_active_bool = None
        if is_active is not None:
            is_active_bool = is_active.lower() in ("true", "1", "yes")

        accounts = BankAccountService.list(
            org_id=UUID(org_id),
            is_active=is_active_bool,
            currency=currency,
            search=search,
        )

        serializer = BankAccountSerializer(accounts, many=True)
        return Response(serializer.data)

    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Create a new bank account."""
        if not CanManageBanking().has_permission(request, self):
            return Response(
                {"error": "You do not have permission to manage bank accounts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BankAccountCreateSerializer(
            data=request.data,
            context={"org_id": UUID(org_id)},
        )
        serializer.is_valid(raise_exception=True)

        account = BankAccountService.create(
            org_id=UUID(org_id),
            data=serializer.validated_data,
            user_id=request.user.id if request.user else None,
        )

        response_serializer = BankAccountSerializer(account)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class BankAccountDetailView(APIView):
    """
    GET: Get bank account details.
    PATCH: Update bank account.
    DELETE: Deactivate bank account.

    SEC-001 Remediation: Uses validated serializers and services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str, account_id: str) -> Response:
        """Get a single bank account."""
        account = BankAccountService.get(
            org_id=UUID(org_id),
            account_id=UUID(account_id),
        )

        serializer = BankAccountSerializer(account)
        return Response(serializer.data)

    @wrap_response
    def patch(self, request, org_id: str, account_id: str) -> Response:
        """Update a bank account."""
        if not CanManageBanking().has_permission(request, self):
            return Response(
                {"error": "You do not have permission to manage bank accounts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BankAccountUpdateSerializer(
            data=request.data,
            partial=True,
            context={"org_id": UUID(org_id)},
        )
        serializer.is_valid(raise_exception=True)

        account = BankAccountService.update(
            org_id=UUID(org_id),
            account_id=UUID(account_id),
            data=serializer.validated_data,
            user_id=request.user.id if request.user else None,
        )

        response_serializer = BankAccountSerializer(account)
        return Response(response_serializer.data)

    @wrap_response
    def delete(self, request, org_id: str, account_id: str) -> Response:
        """Deactivate a bank account (soft delete)."""
        if not CanManageBanking().has_permission(request, self):
            return Response(
                {"error": "You do not have permission to manage bank accounts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        account = BankAccountService.deactivate(
            org_id=UUID(org_id),
            account_id=UUID(account_id),
            user_id=request.user.id if request.user else None,
        )

        return Response(
            {
                "message": "Bank account deactivated successfully.",
                "id": str(account.id),
                "is_active": account.is_active,
            }
        )


class PaymentListView(APIView):
    """
    GET: List payments.
    POST: Create payment (deprecated - use /receive/ or /make/).

    SEC-001 Remediation: Uses validated serializers and services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """List payments for the organisation."""
        payment_type = request.query_params.get("payment_type")
        contact_id = request.query_params.get("contact_id")
        bank_account_id = request.query_params.get("bank_account_id")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        is_reconciled = request.query_params.get("is_reconciled")
        is_voided = request.query_params.get("is_voided")

        is_reconciled_bool = None
        if is_reconciled is not None:
            is_reconciled_bool = is_reconciled.lower() in ("true", "1", "yes")

        is_voided_bool = None
        if is_voided is not None:
            is_voided_bool = is_voided.lower() in ("true", "1", "yes")

        from datetime import datetime as dt

        date_from_parsed = None
        if date_from:
            date_from_parsed = dt.strptime(date_from, "%Y-%m-%d").date()

        date_to_parsed = None
        if date_to:
            date_to_parsed = dt.strptime(date_to, "%Y-%m-%d").date()

        payments = PaymentService.list(
            org_id=UUID(org_id),
            payment_type=payment_type,
            contact_id=UUID(contact_id) if contact_id else None,
            bank_account_id=UUID(bank_account_id) if bank_account_id else None,
            date_from=date_from_parsed,
            date_to=date_to_parsed,
            is_reconciled=is_reconciled_bool,
            is_voided=is_voided_bool,
        )

        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """
        Create payment (deprecated).

        Use /payments/receive/ for customer payments.
        Use /payments/make/ for supplier payments.
        """
        return Response(
            {
                "error": "Use /payments/receive/ or /payments/make/ to create payments.",
                "hint": "POST to /payments/receive/ for customer payments, "
                "/payments/make/ for supplier payments.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ReceivePaymentView(APIView):
    """
    POST: Receive payment from customer.

    SEC-001 Remediation: Uses validated serializers and services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Create a received payment from a customer."""
        if not CanManageBanking().has_permission(request, self):
            return Response(
                {"error": "You do not have permission to manage payments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PaymentReceiveSerializer(
            data=request.data,
            context={"org_id": UUID(org_id)},
        )
        serializer.is_valid(raise_exception=True)

        payment = PaymentService.create_received(
            org_id=UUID(org_id),
            data=serializer.validated_data,
            user_id=request.user.id if request.user else None,
        )

        if serializer.validated_data.get("allocations"):
            PaymentService.allocate(
                org_id=UUID(org_id),
                payment_id=payment.id,
                allocations=serializer.validated_data["allocations"],
                user_id=request.user.id if request.user else None,
            )

        response_serializer = PaymentSerializer(payment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class MakePaymentView(APIView):
    """
    POST: Make payment to supplier.

    SEC-001 Remediation: Uses validated serializers and services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Create a payment made to a supplier."""
        if not CanManageBanking().has_permission(request, self):
            return Response(
                {"error": "You do not have permission to manage payments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PaymentMakeSerializer(
            data=request.data,
            context={"org_id": UUID(org_id)},
        )
        serializer.is_valid(raise_exception=True)

        payment = PaymentService.create_made(
            org_id=UUID(org_id),
            data=serializer.validated_data,
            user_id=request.user.id if request.user else None,
        )

        if serializer.validated_data.get("allocations"):
            PaymentService.allocate(
                org_id=UUID(org_id),
                payment_id=payment.id,
                allocations=serializer.validated_data["allocations"],
                user_id=request.user.id if request.user else None,
            )

        response_serializer = PaymentSerializer(payment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PaymentDetailView(APIView):
    """
    GET: Get payment details.

    SEC-001 Remediation: Uses validated services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str, payment_id: str) -> Response:
        """Get a single payment with allocations."""
        payment = PaymentService.get(
            org_id=UUID(org_id),
            payment_id=UUID(payment_id),
        )

        allocations = PaymentService.get_allocations(payment_id=payment.id)
        serializer = PaymentSerializer(payment)
        data = serializer.data
        data["allocations"] = PaymentAllocationSerializer(allocations, many=True).data

        return Response(data)


class PaymentAllocateView(APIView):
    """
    POST: Allocate payment to invoices/bills.

    SEC-001 Remediation: Uses validated serializers and services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def post(self, request, org_id: str, payment_id: str) -> Response:
        """Allocate a payment to one or more documents."""
        if not CanManageBanking().has_permission(request, self):
            return Response(
                {"error": "You do not have permission to manage payments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BulkAllocationSerializer(
            data={
                "payment_id": payment_id,
                "allocations": request.data.get("allocations", []),
            },
            context={"org_id": UUID(org_id)},
        )
        serializer.is_valid(raise_exception=True)

        payment = PaymentService.allocate(
            org_id=UUID(org_id),
            payment_id=UUID(payment_id),
            allocations=serializer.validated_data["allocations"],
            user_id=request.user.id if request.user else None,
        )

        response_serializer = PaymentSerializer(payment)
        return Response(response_serializer.data)


class PaymentVoidView(APIView):
    """
    POST: Void a payment.

    SEC-001 Remediation: Uses validated serializers and services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def post(self, request, org_id: str, payment_id: str) -> Response:
        """Void a payment."""
        if not CanManageBanking().has_permission(request, self):
            return Response(
                {"error": "You do not have permission to manage payments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PaymentVoidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = PaymentService.void(
            org_id=UUID(org_id),
            payment_id=UUID(payment_id),
            reason=serializer.validated_data["reason"],
            user_id=request.user.id if request.user else None,
        )

        response_serializer = PaymentSerializer(payment)
        return Response(response_serializer.data)


class BankTransactionListView(APIView):
    """
    GET: List bank transactions (imported bank feed).

    SEC-001 Remediation: Uses validated services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str) -> Response:
        """List imported bank transactions."""
        bank_account_id = request.query_params.get("bank_account_id")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        is_reconciled = request.query_params.get("is_reconciled")
        unreconciled_only = request.query_params.get("unreconciled_only", "false").lower() in (
            "true",
            "1",
        )

        is_reconciled_bool = None
        if is_reconciled is not None:
            is_reconciled_bool = is_reconciled.lower() in ("true", "1", "yes")

        from datetime import datetime as dt

        date_from_parsed = None
        if date_from:
            date_from_parsed = dt.strptime(date_from, "%Y-%m-%d").date()

        date_to_parsed = None
        if date_to:
            date_to_parsed = dt.strptime(date_to, "%Y-%m-%d").date()

        transactions = ReconciliationService.list_transactions(
            org_id=UUID(org_id),
            bank_account_id=UUID(bank_account_id) if bank_account_id else None,
            date_from=date_from_parsed,
            date_to=date_to_parsed,
            is_reconciled=is_reconciled_bool,
            unreconciled_only=unreconciled_only,
        )

        serializer = BankTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class BankTransactionImportView(APIView):
    """
    POST: Import bank transactions from CSV.

    SEC-001 Remediation: Uses validated serializers and services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def post(self, request, org_id: str) -> Response:
        """Import bank transactions from a CSV file."""
        if not CanManageBanking().has_permission(request, self):
            return Response(
                {"error": "You do not have permission to manage bank transactions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BankTransactionImportSerializer(
            data=request.data,
            context={"org_id": UUID(org_id)},
        )
        serializer.is_valid(raise_exception=True)

        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response(
                {"error": "CSV file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = ReconciliationService.import_csv(
            org_id=UUID(org_id),
            bank_account_id=serializer.validated_data["bank_account_id"],
            csv_file=csv_file,
            user_id=request.user.id if request.user else None,
        )

        return Response(result, status=status.HTTP_201_CREATED)


class BankTransactionReconcileView(APIView):
    """
    POST: Reconcile a bank transaction to a payment.

    SEC-001 Remediation: Uses validated serializers and services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def post(self, request, org_id: str, transaction_id: str) -> Response:
        """Reconcile a bank transaction to a payment."""
        if not CanManageBanking().has_permission(request, self):
            return Response(
                {"error": "You do not have permission to reconcile transactions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BankTransactionReconcileSerializer(
            data=request.data,
            context={"org_id": UUID(org_id)},
        )
        serializer.is_valid(raise_exception=True)

        transaction_obj = ReconciliationService.reconcile(
            org_id=UUID(org_id),
            transaction_id=UUID(transaction_id),
            payment_id=serializer.validated_data["payment_id"],
            user_id=request.user.id if request.user else None,
        )

        response_serializer = BankTransactionSerializer(transaction_obj)
        return Response(response_serializer.data)


class BankTransactionUnreconcileView(APIView):
    """
    POST: Remove reconciliation from a bank transaction.

    SEC-001 Remediation: Uses validated services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def post(self, request, org_id: str, transaction_id: str) -> Response:
        """Remove reconciliation from a bank transaction."""
        if not CanManageBanking().has_permission(request, self):
            return Response(
                {"error": "You do not have permission to reconcile transactions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        transaction_obj = ReconciliationService.unreconcile(
            org_id=UUID(org_id),
            transaction_id=UUID(transaction_id),
            user_id=request.user.id if request.user else None,
        )

        response_serializer = BankTransactionSerializer(transaction_obj)
        return Response(response_serializer.data)


class BankTransactionSuggestMatchesView(APIView):
    """
    GET: Suggest payment matches for a bank transaction.

    SEC-001 Remediation: Uses validated services.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgMember]

    @wrap_response
    def get(self, request, org_id: str, transaction_id: str) -> Response:
        """Suggest payment matches for a bank transaction."""
        from decimal import Decimal

        tolerance_str = request.query_params.get("tolerance", "1.00")
        try:
            tolerance = Decimal(tolerance_str)
        except:
            tolerance = Decimal("1.00")

        suggestions = ReconciliationService.suggest_matches(
            org_id=UUID(org_id),
            transaction_id=UUID(transaction_id),
            tolerance=tolerance,
        )

        return Response(suggestions)
