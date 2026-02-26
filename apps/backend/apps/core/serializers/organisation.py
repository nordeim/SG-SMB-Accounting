"""
Organisation serializers for LedgerSG.

Serializers for Organisation, FiscalYear, FiscalPeriod, Role, and UserOrganisation.
"""

from rest_framework import serializers
from datetime import date
from typing import Optional

from apps.core.models import (
    Organisation,
    FiscalYear,
    FiscalPeriod,
    Role,
    UserOrganisation,
)


class OrganisationSerializer(serializers.ModelSerializer):
    """Serializer for Organisation model."""
    
    fy_start_month = serializers.IntegerField(min_value=1, max_value=12)
    
    class Meta:
        model = Organisation
        fields = [
            "id", "name", "legal_name", "uen", "entity_type",
            "gst_registered", "gst_reg_number", "gst_reg_date",
            "peppol_participant_id", "invoicenow_enabled",
            "fy_start_month", "base_currency", "is_active",
            "address_line_1", "address_line_2", "city", "postal_code", "country",
            "contact_email", "contact_phone",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrganisationCreateSerializer(serializers.Serializer):
    """Serializer for creating a new organisation."""
    
    name = serializers.CharField(max_length=255)
    legal_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    uen = serializers.CharField(max_length=20, required=False, allow_blank=True)
    entity_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    gst_registered = serializers.BooleanField(default=False)
    gst_reg_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gst_reg_date = serializers.DateField(required=False, allow_null=True)
    fy_start_month = serializers.IntegerField(min_value=1, max_value=12, default=1)
    base_currency = serializers.CharField(max_length=3, default="SGD")
    address = serializers.CharField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate GST registration fields."""
        if data.get("gst_registered"):
            if not data.get("gst_reg_number"):
                raise serializers.ValidationError(
                    {"gst_reg_number": "GST registration number is required when GST is registered."}
                )
            if not data.get("gst_reg_date"):
                raise serializers.ValidationError(
                    {"gst_reg_date": "GST registration date is required when GST is registered."}
                )
        return data


class GSTRegistrationSerializer(serializers.Serializer):
    """Serializer for GST registration."""
    
    gst_reg_number = serializers.CharField(max_length=20)
    gst_reg_date = serializers.DateField()
    
    def validate_gst_reg_number(self, value):
        """Validate GST registration number format."""
        # Singapore GST numbers start with 'M' followed by digits
        if not value.startswith("M"):
            raise serializers.ValidationError(
                "Singapore GST registration number must start with 'M'."
            )
        return value.upper()


class FiscalYearSerializer(serializers.ModelSerializer):
    """Serializer for FiscalYear model."""
    
    class Meta:
        model = FiscalYear
        fields = [
            "id", "label", "start_date", "end_date",
            "is_closed", "closed_at", "created_at"
        ]
        read_only_fields = ["id", "created_at", "closed_at"]


class FiscalPeriodSerializer(serializers.ModelSerializer):
    """Serializer for FiscalPeriod model."""
    
    fiscal_year = FiscalYearSerializer(read_only=True)
    
    class Meta:
        model = FiscalPeriod
        fields = [
            "id", "fiscal_year", "label", "period_number",
            "start_date", "end_date", "is_open", "created_at"
        ]
        read_only_fields = ["id", "created_at"]


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    class Meta:
        model = Role
        fields = [
            "id", "name", "description",
            "can_manage_org", "can_manage_users", "can_manage_coa",
            "can_create_invoices", "can_approve_invoices", "can_void_invoices",
            "can_create_journals", "can_manage_banking",
            "can_file_gst", "can_view_reports", "can_export_data",
            "is_system", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]


class UserOrganisationSerializer(serializers.ModelSerializer):
    """Serializer for UserOrganisation model."""
    
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    
    class Meta:
        model = UserOrganisation
        fields = [
            "id", "user_email", "user_full_name", "role", "role_name",
            "is_default", "accepted_at", "created_at"
        ]
        read_only_fields = ["id", "created_at"]


class OrganisationMemberSerializer(serializers.ModelSerializer):
    """Serializer for organisation members."""
    
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    role = RoleSerializer(read_only=True)
    
    class Meta:
        model = UserOrganisation
        fields = [
            "id", "user_email", "user_full_name", "role",
            "is_default", "accepted_at", "created_at"
        ]
