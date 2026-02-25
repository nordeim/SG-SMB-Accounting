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
)

app_name = "invoicing"

urlpatterns = [
    # Contacts
    path("contacts/", ContactListCreateView.as_view(), name="contact-list-create"),
    path("contacts/<str:contact_id>/", ContactDetailView.as_view(), name="contact-detail"),
    
    # Documents
    path("documents/", InvoiceDocumentListCreateView.as_view(), name="document-list-create"),
    path("documents/summary/", DocumentSummaryView.as_view(), name="document-summary"),
    path("documents/status-transitions/", ValidStatusTransitionsView.as_view(), name="status-transitions"),
    path("documents/<str:document_id>/", InvoiceDocumentDetailView.as_view(), name="document-detail"),
    path("documents/<str:document_id>/status/", InvoiceDocumentStatusView.as_view(), name="document-status"),
    path("documents/<str:document_id>/lines/", InvoiceLineAddView.as_view(), name="document-line-add"),
    path("documents/<str:document_id>/lines/<str:line_id>/", InvoiceLineRemoveView.as_view(), name="document-line-remove"),
    
    # Quote conversion
    path("quotes/convert/", QuoteConvertView.as_view(), name="quote-convert"),
]
