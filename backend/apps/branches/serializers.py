"""
Serializers for branches app.
"""
from rest_framework import serializers
from .models import Branch


class BranchSerializer(serializers.ModelSerializer):
    """Full serializer for Branch model."""
    full_address = serializers.CharField(read_only=True)
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'id', 'name', 'code', 'address', 'city', 'state',
            'postal_code', 'country', 'phone', 'email',
            'manager_name', 'manager_phone', 'is_active', 'is_main',
            'opening_time', 'closing_time', 'full_address',
            'employee_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_employee_count(self, obj):
        return obj.default_users.count() if hasattr(obj, 'default_users') else 0


class BranchSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for Branch (dropdown lists, etc.)."""

    class Meta:
        model = Branch
        fields = ['id', 'name', 'code', 'is_main']


class BranchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating branches."""

    class Meta:
        model = Branch
        fields = [
            'name', 'code', 'address', 'city', 'state',
            'postal_code', 'country', 'phone', 'email',
            'manager_name', 'manager_phone', 'is_active', 'is_main',
            'opening_time', 'closing_time'
        ]

    def validate_code(self, value):
        """Ensure code is uppercase."""
        return value.upper()


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
