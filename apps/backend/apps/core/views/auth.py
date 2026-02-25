"""
Authentication views for LedgerSG.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from apps.core.serializers.auth import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)
from apps.core.services import auth_service
from common.exceptions import ValidationError


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request: Request) -> Response:
    """
    Register a new user.
    
    POST /api/v1/auth/register/
    """
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        user = auth_service.register_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            full_name=serializer.validated_data["full_name"],
        )
        
        # Generate tokens
        tokens = auth_service.generate_tokens(user)
        
        return Response({
            "user": UserProfileSerializer(user).data,
            "tokens": tokens,
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response(
            {"error": {"code": e.code, "message": e.message}},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request: Request) -> Response:
    """
    Login user and return JWT tokens.
    
    POST /api/v1/auth/login/
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        user, tokens = auth_service.login_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        
        return Response({
            "user": UserProfileSerializer(user).data,
            "tokens": tokens,
        })
        
    except ValidationError as e:
        return Response(
            {"error": {"code": e.code, "message": e.message}},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_view(request: Request) -> Response:
    """
    Refresh access token.
    
    POST /api/v1/auth/refresh/
    """
    refresh_token = request.data.get("refresh")
    
    if not refresh_token:
        return Response(
            {"error": {"code": "missing_token", "message": "Refresh token is required"}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tokens = auth_service.refresh_access_token(refresh_token)
        return Response({"tokens": tokens})
        
    except ValidationError as e:
        return Response(
            {"error": {"code": e.code, "message": e.message}},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request: Request) -> Response:
    """
    Logout user (blacklist refresh token).
    
    POST /api/v1/auth/logout/
    """
    refresh_token = request.data.get("refresh")
    
    if refresh_token:
        auth_service.logout_user(refresh_token)
    
    return Response({"message": "Logged out successfully"})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me_view(request: Request) -> Response:
    """
    Get or update current user profile.
    
    GET /api/v1/auth/me/
    PATCH /api/v1/auth/me/
    """
    if request.method == "GET":
        return Response(UserProfileSerializer(request.user).data)
    
    # PATCH - update profile
    serializer = UserProfileSerializer(
        request.user,
        data=request.data,
        partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request: Request) -> Response:
    """
    Change user password.
    
    POST /api/v1/auth/change-password/
    """
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        auth_service.change_password(
            user=request.user,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
        )
        
        return Response({"message": "Password changed successfully"})
        
    except ValidationError as e:
        return Response(
            {"error": {"code": e.code, "message": e.message}},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_organisations_view(request: Request) -> Response:
    """
    Get current user's organisations.
    
    GET /api/v1/auth/organisations/
    """
    memberships = auth_service.get_user_organisations(request.user)
    
    data = []
    for membership in memberships:
        data.append({
            "id": membership.org.id,
            "name": membership.org.name,
            "role": {
                "id": membership.role.id,
                "name": membership.role.name,
            },
            "is_default": membership.is_default,
            "joined_at": membership.accepted_at,
        })
    
    return Response(data)
