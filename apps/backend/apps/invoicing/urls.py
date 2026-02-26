"""
Invoicing URL configuration.

Routes for contacts and invoice documents.
"""

from django.urls import path

from .views import (
    ContactListCreateView,
    ContactDetailView,
    InvoiceDocumentListCreateView,
    InvoiceDocumentDetailView,
    InvoiceDocumentStatusView,
    InvoiceLineAddView,
    InvoiceLineRemoveView,
    QuoteConvertView,
    DocumentSummaryView,
    ValidStatusTransitionsView,
    # Phase 2: Invoice workflow operations
    InvoiceApproveView,
    InvoiceVoidView,
    InvoicePDFView,
    InvoiceSendView,
    InvoiceSendInvoiceNowView,
    InvoiceInvoiceNowStatusView,
)

app_name = "invoicing"

urlpatterns = [
    # Contacts
    path("contacts/", ContactListCreateView.as_view(), name="contact-list-create"),
    path("contacts/<str:contact_id>/", ContactDetailView.as_view(), name="contact-detail"),
    # Documents
    path("documents/", InvoiceDocumentListCreateView.as_view(), name="document-list-create"),
    path("documents/summary/", DocumentSummaryView.as_view(), name="document-summary"),
    path(
        "documents/status-transitions/",
        ValidStatusTransitionsView.as_view(),
        name="status-transitions",
    ),
    path(
        "documents/<str:document_id>/", InvoiceDocumentDetailView.as_view(), name="document-detail"
    ),
    path(
        "documents/<str:document_id>/status/",
        InvoiceDocumentStatusView.as_view(),
        name="document-status",
    ),
    path(
        "documents/<str:document_id>/lines/", InvoiceLineAddView.as_view(), name="document-line-add"
    ),
    path(
        "documents/<str:document_id>/lines/<str:line_id>/",
        InvoiceLineRemoveView.as_view(),
        name="document-line-remove",
    ),
    # Phase 2: Document workflow operations
    path(
        "documents/<str:document_id>/approve/",
        InvoiceApproveView.as_view(),
        name="document-approve",
    ),
    path("documents/<str:document_id>/void/", InvoiceVoidView.as_view(), name="document-void"),
    path("documents/<str:document_id>/pdf/", InvoicePDFView.as_view(), name="document-pdf"),
    path("documents/<str:document_id>/send/", InvoiceSendView.as_view(), name="document-send"),
    path(
        "documents/<str:document_id>/send-invoicenow/",
        InvoiceSendInvoiceNowView.as_view(),
        name="document-send-invoicenow",
    ),
    path(
        "documents/<str:document_id>/invoicenow-status/",
        InvoiceInvoiceNowStatusView.as_view(),
        name="document-invoicenow-status",
    ),
    # Quote conversion
    path("quotes/convert/", QuoteConvertView.as_view(), name="quote-convert"),
]
