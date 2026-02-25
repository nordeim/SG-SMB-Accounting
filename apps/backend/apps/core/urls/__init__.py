"""
Core URL configuration.
"""

from django.urls import path, include

urlpatterns = [
    path("auth/", include("apps.core.urls.auth")),
    path("organisations/", include("apps.core.urls.organisation")),
    path("users/", include("apps.core.urls.user")),
    path("fiscal/", include("apps.core.urls.fiscal")),
]
