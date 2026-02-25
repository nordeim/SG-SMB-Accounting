"""
GST URL configuration.

Routes for tax codes, GST calculations, and GST returns.
"""

from django.urls import path

from .views import (
    TaxCodeListCreateView,
    TaxCodeDetailView,
    TaxCodeIrasInfoView,
    GSTCalculateView,
    GSTCalculateDocumentView,
    GSTReturnListCreateView,
    GSTReturnDetailView,
    GSTReturnFileView,
    GSTReturnAmendView,
    GSTReturnPayView,
    GSTReturnDeadlinesView,
)

app_name = "gst"

urlpatterns = [
    # Tax codes
    path("tax-codes/", TaxCodeListCreateView.as_view(), name="tax-code-list-create"),
    path("tax-codes/iras-info/", TaxCodeIrasInfoView.as_view(), name="tax-code-iras-info"),
    path("tax-codes/<str:tax_code_id>/", TaxCodeDetailView.as_view(), name="tax-code-detail"),
    
    # GST calculations
    path("calculate/", GSTCalculateView.as_view(), name="gst-calculate"),
    path("calculate/document/", GSTCalculateDocumentView.as_view(), name="gst-calculate-document"),
    
    # GST returns
    path("returns/", GSTReturnListCreateView.as_view(), name="gst-return-list-create"),
    path("returns/deadlines/", GSTReturnDeadlinesView.as_view(), name="gst-return-deadlines"),
    path("returns/<str:return_id>/", GSTReturnDetailView.as_view(), name="gst-return-detail"),
    path("returns/<str:return_id>/file/", GSTReturnFileView.as_view(), name="gst-return-file"),
    path("returns/<str:return_id>/amend/", GSTReturnAmendView.as_view(), name="gst-return-amend"),
    path("returns/<str:return_id>/pay/", GSTReturnPayView.as_view(), name="gst-return-pay"),
]
