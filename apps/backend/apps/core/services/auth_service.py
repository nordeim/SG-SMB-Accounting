"""
Authentication service for LedgerSG.

Handles user registration, login, and token management.
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta

from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import AppUser
from common.exceptions import ValidationError


def register_user(email: str, password: str, full_name: str, phone: str = "") -> AppUser:
    """
    Register a new user.
    
    Args:
        email: User email address
        password: User password (min 12 chars)
        full_name: User full name
        phone: Optional phone number
        
    Returns:
        Created AppUser instance
        
    Raises:
        ValidationError: If email already exists or password invalid
    """
    # Check if email exists
    if AppUser.objects.filter(email=email.lower()).exists():
        raise ValidationError("Email already registered.")
    
    # Create user
    with transaction.atomic():
        user = AppUser.objects.create_user(
            email=email.lower(),
            password=password,
            full_name=full_name,
        )
        if phone:
            user.phone = phone
            user.save()
    
    return user


def login_user(email: str, password: str) -> Tuple[AppUser, dict]:
    """
    Authenticate user and generate JWT tokens.
    
    Args:
        email: User email address
        password: User password
        
    Returns:
        Tuple of (user, token_dict)
        
    Raises:
        ValidationError: If credentials invalid
    """
    # Authenticate
    user = authenticate(email=email.lower(), password=password)
    
    if not user:
        raise ValidationError("Invalid email or password.")
    
    if not user.is_active:
        raise ValidationError("Account is disabled.")
    
    # Generate tokens
    tokens = generate_tokens(user)
    
    return user, tokens


def generate_tokens(user: AppUser) -> dict:
    """
    Generate JWT tokens for user.
    
    Args:
        user: AppUser instance
        
    Returns:
        Dict with access, refresh tokens and expiry
    """
    refresh = RefreshToken.for_user(user)
    
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "access_expires": datetime.now() + timedelta(minutes=15),
    }


def refresh_access_token(refresh_token: str) -> dict:
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Refresh token string
        
    Returns:
        Dict with new access token
        
    Raises:
        ValidationError: If token invalid
    """
    try:
        refresh = RefreshToken(refresh_token)
        
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "access_expires": datetime.now() + timedelta(minutes=15),
        }
    except Exception as e:
        raise ValidationError(f"Invalid refresh token: {str(e)}")


def change_password(user: AppUser, old_password: str, new_password: str) -> None:
    """
    Change user password.
    
    Args:
        user: AppUser instance
        old_password: Current password
        new_password: New password
        
    Raises:
        ValidationError: If old password incorrect or new password invalid
    """
    # Verify old password
    if not user.check_password(old_password):
        raise ValidationError("Current password is incorrect.")
    
    # Set new password
    user.set_password(new_password)
    user.save()


def get_user_organisations(user: AppUser):
    """
    Get organisations the user belongs to.
    
    Args:
        user: AppUser instance
        
    Returns:
        QuerySet of UserOrganisation
    """
    from apps.core.models import UserOrganisation
    
    return UserOrganisation.objects.filter(
        user=user,
        accepted_at__isnull=False,
    ).select_related("org", "role").order_by("-is_default", "org__name")


def logout_user(refresh_token: str) -> None:
    """
    Blacklist refresh token on logout.
    
    Args:
        refresh_token: Refresh token string
    """
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        # Token may already be blacklisted or invalid
        pass
