"""
Integration tests for Authentication API endpoints.

Tests: register, login, logout, refresh, profile, change-password
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.core.models import AppUser


@pytest.mark.django_db
def test_register_user_success(api_client):
    """Test successful user registration."""
    url = "/api/v1/auth/register/"
    data = {
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "full_name": "New Test User"
    }
    
    response = api_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["email"] == "newuser@example.com"
    assert response.data["full_name"] == "New Test User"
    assert "id" in response.data
    assert "password" not in response.data  # Password should not be returned
    
    # Verify user was created in database
    user = AppUser.objects.get(email="newuser@example.com")
    assert user.full_name == "New Test User"
    assert user.check_password("SecurePass123!")


@pytest.mark.django_db
def test_register_user_duplicate_email(api_client, test_user):
    """Test registration with duplicate email fails."""
    url = "/api/v1/auth/register/"
    data = {
        "email": test_user.email,  # Already exists
        "password": "SecurePass123!",
        "full_name": "Another User"
    }
    
    response = api_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data["error"]["details"] or "error" in response.data


@pytest.mark.django_db
def test_register_user_invalid_data(api_client):
    """Test registration with invalid data fails."""
    url = "/api/v1/auth/register/"
    
    # Missing required fields
    response = api_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Invalid email
    response = api_client.post(url, {
        "email": "not-an-email",
        "password": "pass123",
        "full_name": "Test"
    }, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Password too short
    response = api_client.post(url, {
        "email": "test@example.com",
        "password": "123",
        "full_name": "Test"
    }, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_login_user_success(api_client, test_user):
    """Test successful user login."""
    url = "/api/v1/auth/login/"
    data = {
        "email": test_user.email,
        "password": "testpassword123"
    }
    
    response = api_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data
    assert "refresh_token" in response.data
    assert response.data["user"]["email"] == test_user.email


@pytest.mark.django_db
def test_login_user_invalid_credentials(api_client, test_user):
    """Test login with invalid credentials fails."""
    url = "/api/v1/auth/login/"
    
    # Wrong password
    response = api_client.post(url, {
        "email": test_user.email,
        "password": "wrongpassword"
    }, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Non-existent user
    response = api_client.post(url, {
        "email": "nonexistent@example.com",
        "password": "password123"
    }, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_user_inactive(api_client, test_user):
    """Test login with inactive user fails."""
    test_user.is_active = False
    test_user.save()
    
    url = "/api/v1/auth/login/"
    response = api_client.post(url, {
        "email": test_user.email,
        "password": "testpassword123"
    }, format="json")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_profile_success(auth_client, test_user):
    """Test getting user profile when authenticated."""
    url = "/api/v1/auth/profile/"
    
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == test_user.email
    assert response.data["full_name"] == test_user.full_name
    assert "id" in response.data


@pytest.mark.django_db
def test_get_profile_unauthenticated(api_client):
    """Test getting profile without authentication fails."""
    url = "/api/v1/auth/profile/"
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_refresh_token_success(api_client, test_user):
    """Test refreshing access token."""
    from rest_framework_simplejwt.tokens import RefreshToken
    
    # Get initial tokens
    refresh = RefreshToken.for_user(test_user)
    
    url = "/api/v1/auth/refresh/"
    response = api_client.post(url, {
        "refresh_token": str(refresh)
    }, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data
    assert response.data["token_type"] == "Bearer"


@pytest.mark.django_db
def test_refresh_token_invalid(api_client):
    """Test refreshing with invalid token fails."""
    url = "/api/v1/auth/refresh/"
    
    response = api_client.post(url, {
        "refresh_token": "invalid.token.here"
    }, format="json")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_logout_success(auth_client, test_user):
    """Test user logout."""
    from rest_framework_simplejwt.tokens import RefreshToken
    
    refresh = RefreshToken.for_user(test_user)
    
    url = "/api/v1/auth/logout/"
    response = auth_client.post(url, {
        "refresh_token": str(refresh)
    }, format="json")
    
    # Should succeed even if token blacklisting isn't fully configured
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]


@pytest.mark.django_db
def test_change_password_success(auth_client, test_user):
    """Test changing password."""
    url = "/api/v1/auth/change-password/"
    
    response = auth_client.post(url, {
        "current_password": "testpassword123",
        "new_password": "NewSecurePass456!"
    }, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    
    # Verify password was changed
    test_user.refresh_from_db()
    assert test_user.check_password("NewSecurePass456!")


@pytest.mark.django_db
def test_change_password_wrong_current(auth_client, test_user):
    """Test changing password with wrong current password fails."""
    url = "/api/v1/auth/change-password/"
    
    response = auth_client.post(url, {
        "current_password": "wrongpassword",
        "new_password": "NewSecurePass456!"
    }, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Verify password was NOT changed
    test_user.refresh_from_db()
    assert test_user.check_password("testpassword123")


@pytest.mark.django_db
def test_change_password_unauthenticated(api_client):
    """Test changing password without authentication fails."""
    url = "/api/v1/auth/change-password/"
    
    response = api_client.post(url, {
        "current_password": "oldpass",
        "new_password": "newpass"
    }, format="json")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_token_expiration(api_client, test_user):
    """Test that expired tokens are rejected."""
    import time
    from rest_framework_simplejwt.tokens import AccessToken
    from datetime import datetime, timedelta
    
    # Create a token that's already expired
    token = AccessToken.for_user(test_user)
    token.set_exp(from_time=datetime.utcnow() - timedelta(hours=1))
    
    url = "/api/v1/auth/profile/"
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")
    
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
