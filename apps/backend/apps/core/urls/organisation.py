"""
Organisation URL configuration.
"""

from django.urls import path

from apps.core.views.organisations import (
    OrganisationListCreateView,
)


urlpatterns = [
    path("", OrganisationListCreateView.as_view(), name="org-list-create"),
]
