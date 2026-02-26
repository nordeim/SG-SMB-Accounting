"""
Reporting URL configuration.

Dashboard and financial reporting endpoints.
"""

from django.urls import path

from .views import (
    DashboardMetricsView,
    DashboardAlertsView,
    FinancialReportView,
)

app_name = "reporting"

urlpatterns = [
    # Dashboard endpoints
    path("dashboard/metrics/", DashboardMetricsView.as_view(), name="dashboard-metrics"),
    path("dashboard/alerts/", DashboardAlertsView.as_view(), name="dashboard-alerts"),
    # Financial reports
    path("reports/financial/", FinancialReportView.as_view(), name="financial-report"),
]
