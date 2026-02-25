"""
Auth URL configuration.
"""

from django.urls import path

from apps.core.views import auth


urlpatterns = [
    path("register/", auth.register_view, name="auth-register"),
    path("login/", auth.login_view, name="auth-login"),
    path("refresh/", auth.refresh_view, name="auth-refresh"),
    path("logout/", auth.logout_view, name="auth-logout"),
    path("me/", auth.me_view, name="auth-me"),
    path("change-password/", auth.change_password_view, name="auth-change-password"),
    path("organisations/", auth.my_organisations_view, name="auth-organisations"),
]
