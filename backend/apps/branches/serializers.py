"""
Serializers for branches app.
"""
from rest_framework import serializers
from .models import Branch


class BranchSerializer(serializers.ModelSerializer):
    """Full serializer for Branch model."""
    full_address = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    logo_url = serializers.CharField(read_only=True)
    favicon_url = serializers.CharField(read_only=True)
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'id', 'name', 'code', 'address', 'city', 'state',
            'postal_code', 'country', 'phone', 'email',
            'manager_name', 'manager_phone', 'is_active', 'is_main',
            'opening_time', 'closing_time', 'full_address',
            # Branding fields
            'store_name', 'display_name', 'logo', 'logo_url', 'favicon', 'favicon_url',
            'primary_color', 'secondary_color', 'accent_color',
            # Business config
            'tax_rate', 'currency', 'currency_symbol',
            'receipt_header', 'receipt_footer',
            # Meta
            'employee_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'display_name', 'logo_url', 'favicon_url']

    def get_employee_count(self, obj):
        return obj.default_users.count() if hasattr(obj, 'default_users') else 0


class BranchSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for Branch (dropdown lists, etc.)."""
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = Branch
        fields = ['id', 'name', 'code', 'is_main', 'display_name', 'primary_color']


class BranchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating branches."""

    class Meta:
        model = Branch
        fields = [
            'name', 'code', 'address', 'city', 'state',
            'postal_code', 'country', 'phone', 'email',
            'manager_name', 'manager_phone', 'is_active', 'is_main',
            'opening_time', 'closing_time',
            # Branding
            'store_name', 'logo', 'favicon',
            'primary_color', 'secondary_color', 'accent_color',
            # Business config
            'tax_rate', 'currency', 'currency_symbol',
            'receipt_header', 'receipt_footer'
        ]

    def validate_code(self, value):
        """Ensure code is uppercase."""
        return value.upper()

    def validate_primary_color(self, value):
        """Ensure color is valid hex format."""
        if value and not value.startswith('#'):
            value = f'#{value}'
        if value and len(value) != 7:
            raise serializers.ValidationError('Color must be in hex format (e.g., #2563eb)')
        return value

    validate_secondary_color = validate_primary_color
    validate_accent_color = validate_primary_color


class BranchBrandingSerializer(serializers.ModelSerializer):
    """Serializer for branch theming/branding data only."""
    display_name = serializers.CharField(read_only=True)
    logo_url = serializers.CharField(read_only=True)
    favicon_url = serializers.CharField(read_only=True)

    class Meta:
        model = Branch
        fields = [
            'id', 'store_name', 'display_name',
            'logo', 'logo_url', 'favicon', 'favicon_url',
            'primary_color', 'secondary_color', 'accent_color',
            'tax_rate', 'currency', 'currency_symbol'
        ]

    def validate_primary_color(self, value):
        """Ensure color is valid hex format."""
        if value and not value.startswith('#'):
            value = f'#{value}'
        if value and len(value) != 7:
            raise serializers.ValidationError('Color must be in hex format (e.g., #2563eb)')
        return value

    validate_secondary_color = validate_primary_color
    validate_accent_color = validate_primary_color


class BranchStatsSerializer(serializers.Serializer):
    """Serializer for branch statistics."""
    total_products = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    sales_today = serializers.IntegerField()
    sales_amount_today = serializers.DecimalField(max_digits=12, decimal_places=2)
    sales_this_month = serializers.IntegerField()
    sales_amount_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_employees = serializers.IntegerField()
    low_stock_alerts = serializers.IntegerField()
