"""
Banking URL configuration.

Bank accounts and payments endpoints.
"""

from django.urls import path

from .views import (
    BankAccountListView,
    BankAccountDetailView,
    PaymentListView,
    ReceivePaymentView,
    MakePaymentView,
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
]
