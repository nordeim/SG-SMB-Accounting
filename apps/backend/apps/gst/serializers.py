"""
GST serializers for LedgerSG.

Serializers for TaxCode and GSTReturn models.
"""

from rest_framework import serializers
from decimal import Decimal

from apps.core.models import TaxCode, GSTReturn


class TaxCodeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for tax code list views."""
    
    rate_display = serializers.SerializerMethodField()
    
    class Meta:
        model = TaxCode
        fields = [
            "id", "code", "name", "rate", "rate_display",
            "is_gst_charged", "is_active", "is_system",
            "box_mapping", "effective_from"
        ]
        read_only_fields = ["id", "is_system"]
    
    def get_rate_display(self, obj: TaxCode) -> str:
        """Get formatted rate display."""
        if obj.rate is None:
            return "N/A"
        return f"{obj.rate * 100:.0f}%"


class TaxCodeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for tax code views."""
    
    class Meta:
        model = TaxCode
        fields = [
            "id", "code", "name", "rate", "is_gst_charged",
            "description", "box_mapping",
            "is_system", "is_active",
            "effective_from", "effective_to",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]


class TaxCodeCreateSerializer(serializers.Serializer):
    """Serializer for creating a tax code."""
    
    code = serializers.CharField(max_length=10)
    name = serializers.CharField(max_length=100)
    rate = serializers.DecimalField(
        max_digits=5, decimal_places=4,
        required=False, allow_null=True
    )
    is_gst_charged = serializers.BooleanField()
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    box_mapping = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    def validate_code(self, value: str) -> str:
        """Validate tax code format."""
        value = value.upper().strip()
        if not value:
            raise serializers.ValidationError("Tax code is required.")
        if len(value) < 2:
            raise serializers.ValidationError("Tax code must be at least 2 characters.")
        return value
    
    def validate_rate(self, value: Decimal) -> Decimal:
        """Validate GST rate."""
        if value is not None and (value < 0 or value > 1):
            raise serializers.ValidationError("Rate must be between 0 and 1 (e.g., 0.09 for 9%).")
        return value


class TaxCodeUpdateSerializer(serializers.Serializer):
    """Serializer for updating a tax code."""
    
    name = serializers.CharField(max_length=100, required=False)
    rate = serializers.DecimalField(
        max_digits=5, decimal_places=4,
        required=False, allow_null=True
    )
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class GSTCalculationRequestSerializer(serializers.Serializer):
    """Serializer for GST calculation request."""
    
    amount = serializers.DecimalField(max_digits=15, decimal_places=4)
    tax_code_id = serializers.UUIDField(required=False)
    rate = serializers.DecimalField(
        max_digits=5, decimal_places=4,
        required=False, allow_null=True
    )
    is_bcrs_deposit = serializers.BooleanField(default=False)
    
    def validate(self, data):
        """Validate that either tax_code_id or rate is provided."""
        if not data.get("tax_code_id") and data.get("rate") is None:
            raise serializers.ValidationError(
                "Either tax_code_id or rate must be provided."
            )
        return data


class GSTCalculationResponseSerializer(serializers.Serializer):
    """Serializer for GST calculation response."""
    
    net_amount = serializers.CharField()
    gst_amount = serializers.CharField()
    total_amount = serializers.CharField()
    rate = serializers.CharField()
    is_bcrs_exempt = serializers.BooleanField()
    tax_code = serializers.CharField(required=False)


class LineGSTCalculationSerializer(serializers.Serializer):
    """Serializer for line item GST calculation."""
    
    id = serializers.CharField(required=False)
    amount = serializers.DecimalField(max_digits=15, decimal_places=4)
    rate = serializers.DecimalField(max_digits=5, decimal_places=4, required=False)
    is_bcrs_deposit = serializers.BooleanField(default=False)


class DocumentGSTCalculationSerializer(serializers.Serializer):
    """Serializer for document GST calculation."""
    
    lines = LineGSTCalculationSerializer(many=True)
    default_rate = serializers.DecimalField(
        max_digits=5, decimal_places=4,
        required=False, default=Decimal("0.09")
    )


class DocumentGSTSummarySerializer(serializers.Serializer):
    """Serializer for document GST summary."""
    
    lines = serializers.ListField(child=serializers.DictField())
    summary = serializers.DictField()


class GSTReturnListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for GST return list views."""
    
    days_until_due = serializers.SerializerMethodField()
    net_gst = serializers.SerializerMethodField()
    
    class Meta:
        model = GSTReturn
        fields = [
            "id", "label", "period_start", "period_end", "due_date",
            "status", "filing_frequency", "days_until_due", "net_gst"
        ]
    
    def get_days_until_due(self, obj: GSTReturn) -> int:
        """Get days until due date."""
        from datetime import date
        return (obj.due_date - date.today()).days
    
    def get_net_gst(self, obj: GSTReturn) -> str:
        """Get net GST amount."""
        return str(obj.box8_net_gst or Decimal("0.00"))


class GSTReturnDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for GST return views."""
    
    boxes = serializers.SerializerMethodField()
    filing = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    
    class Meta:
        model = GSTReturn
        fields = [
            "id", "label", "period_start", "period_end", "due_date",
            "status", "filing_frequency", "amendment_reason",
            "boxes", "filing", "payment",
            "created_at", "updated_at"
        ]
    
    def get_boxes(self, obj: GSTReturn) -> dict:
        """Get F5 box values."""
        return {
            "box1_standard_rated_supplies": str(obj.box1_std_rated_supplies or 0),
            "box2_zero_rated_supplies": str(obj.box2_zero_rated_supplies or 0),
            "box3_exempt_supplies": str(obj.box3_exempt_supplies or 0),
            "box4_total_supplies": str(obj.box4_total_supplies or 0),
            "box5_output_tax": str(obj.box5_output_tax or 0),
            "box6_taxable_purchases": str(obj.box6_taxable_purchases or 0),
            "box7_input_tax": str(obj.box7_input_tax or 0),
            "box8_net_gst": str(obj.box8_net_gst or 0),
            "box9_goods_imported": str(obj.box9_goods_imported or 0),
            "box10_gst_imports_mg_igds": str(obj.box10_gst_imports_mg_igds or 0),
            "box11_service_imports": str(obj.box11_service_imports or 0),
            "box12_output_tax_reverse_charge": str(obj.box12_output_tax_reverse_charge or 0),
            "box13_revenue": str(obj.box13_revenue or 0),
            "box14_exempt_supplies": str(obj.box14_exempt_supplies or 0),
            "box15_indicator": obj.box15_indicator or "N",
        }
    
    def get_filing(self, obj: GSTReturn) -> dict:
        """Get filing information."""
        return {
            "filed_at": obj.filed_at.isoformat() if obj.filed_at else None,
            "filed_by": str(obj.filed_by_id) if obj.filed_by_id else None,
            "filing_reference": obj.filing_reference,
        }
    
    def get_payment(self, obj: GSTReturn) -> dict:
        """Get payment information."""
        return {
            "paid_at": obj.paid_at.isoformat() if obj.paid_at else None,
            "payment_amount": str(obj.payment_amount) if obj.payment_amount else None,
            "payment_reference": obj.payment_reference,
        }


class GSTReturnCreateSerializer(serializers.Serializer):
    """Serializer for creating GST return periods."""
    
    filing_frequency = serializers.ChoiceField(choices=["MONTHLY", "QUARTERLY"])
    start_date = serializers.DateField()
    periods = serializers.IntegerField(min_value=1, max_value=24, default=12)


class GSTReturnFileSerializer(serializers.Serializer):
    """Serializer for filing a GST return."""
    
    filing_reference = serializers.CharField(max_length=50, required=False, allow_blank=True)
    boxes = serializers.DictField(required=False)


class GSTReturnAmendSerializer(serializers.Serializer):
    """Serializer for amending a GST return."""
    
    reason = serializers.CharField(max_length=500)


class GSTReturnPaymentSerializer(serializers.Serializer):
    """Serializer for recording GST payment."""
    
    payment_date = serializers.DateField()
    payment_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payment_reference = serializers.CharField(max_length=100)


class F5BoxDataSerializer(serializers.Serializer):
    """Serializer for F5 box data."""
    
    box1_standard_rated_supplies = serializers.CharField()
    box2_zero_rated_supplies = serializers.CharField()
    box3_exempt_supplies = serializers.CharField()
    box4_total_supplies = serializers.CharField()
    box5_output_tax = serializers.CharField()
    box6_taxable_purchases = serializers.CharField()
    box7_input_tax = serializers.CharField()
    box8_net_gst = serializers.CharField()
    box9_goods_imported = serializers.CharField(required=False)
    box10_gst_imports_mg_igds = serializers.CharField(required=False)
    box11_service_imports = serializers.CharField(required=False)
    box12_output_tax_reverse_charge = serializers.CharField(required=False)
    box13_revenue = serializers.CharField()
    box14_exempt_supplies = serializers.CharField()
    box15_indicator = serializers.CharField(required=False)
