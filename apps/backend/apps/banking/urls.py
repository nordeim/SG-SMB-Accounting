"""
Banking URL configuration.

Bank accounts, payments, and reconciliation endpoints.
SEC-001 Remediation: All endpoints use validated implementations.
"""

from django.urls import path

from .views import (
    BankAccountListView,
    BankAccountDetailView,
    PaymentListView,
    PaymentDetailView,
    ReceivePaymentView,
    MakePaymentView,
    PaymentAllocateView,
    PaymentVoidView,
    BankTransactionListView,
    BankTransactionImportView,
    BankTransactionReconcileView,
    BankTransactionUnreconcileView,
    BankTransactionSuggestMatchesView,
)

app_name = "banking"

urlpatterns = [
    # Bank accounts
    path("bank-accounts/", BankAccountListView.as_view(), name="bank-account-list"),
    path(
        "bank-accounts/<str:account_id>/",
        BankAccountDetailView.as_view(),
        name="bank-account-detail",
    ),
    # Payments
    path("payments/", PaymentListView.as_view(), name="payment-list"),
    path("payments/receive/", ReceivePaymentView.as_view(), name="payment-receive"),
    path("payments/make/", MakePaymentView.as_view(), name="payment-make"),
    path(
        "payments/<str:payment_id>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),
    path(
        "payments/<str:payment_id>/allocate/",
        PaymentAllocateView.as_view(),
        name="payment-allocate",
    ),
    path(
        "payments/<str:payment_id>/void/",
        PaymentVoidView.as_view(),
        name="payment-void",
    ),
    # Bank transactions (imported bank feed)
    path(
        "bank-transactions/",
        BankTransactionListView.as_view(),
        name="bank-transaction-list",
    ),
    path(
        "bank-transactions/import/",
        BankTransactionImportView.as_view(),
        name="bank-transaction-import",
    ),
    path(
        "bank-transactions/<str:transaction_id>/reconcile/",
        BankTransactionReconcileView.as_view(),
        name="bank-transaction-reconcile",
    ),
    path(
        "bank-transactions/<str:transaction_id>/unreconcile/",
        BankTransactionUnreconcileView.as_view(),
        name="bank-transaction-unreconcile",
    ),
    path(
        "bank-transactions/<str:transaction_id>/suggest-matches/",
        BankTransactionSuggestMatchesView.as_view(),
        name="bank-transaction-suggest-matches",
    ),
]
