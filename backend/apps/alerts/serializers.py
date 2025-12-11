"""
Serializers for the Alerts app.
"""
from rest_framework import serializers
from .models import Alert, AlertConfiguration, UserAlertPreference


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model."""
    alert_type_display = serializers.CharField(
        source='get_alert_type_display',
        read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True,
        allow_null=True
    )
    product_name = serializers.CharField(
        source='product.name',
        read_only=True,
        allow_null=True
    )
    product_sku = serializers.CharField(
        source='product.sku',
        read_only=True,
        allow_null=True
    )
    employee_name = serializers.CharField(
        source='employee.full_name',
        read_only=True,
        allow_null=True
    )
    read_by_name = serializers.CharField(
        source='read_by.full_name',
        read_only=True,
        allow_null=True
    )
    resolved_by_name = serializers.CharField(
        source='resolved_by.full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Alert
        fields = [
            'id',
            'alert_type',
            'alert_type_display',
            'severity',
            'severity_display',
            'title',
            'message',
            'branch',
            'branch_name',
            'product',
            'product_name',
            'product_sku',
            'employee',
            'employee_name',
            'status',
            'status_display',
            'is_read',
            'read_at',
            'read_by',
            'read_by_name',
            'resolved_at',
            'resolved_by',
            'resolved_by_name',
            'resolution_notes',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'alert_type',
            'severity',
            'title',
            'message',
            'branch',
            'product',
            'employee',
            'is_read',
            'read_at',
            'read_by',
            'resolved_at',
            'resolved_by',
            'metadata',
            'created_at',
            'updated_at',
        ]


class AlertListSerializer(serializers.ModelSerializer):
    """Compact serializer for alert lists."""
    alert_type_display = serializers.CharField(
        source='get_alert_type_display',
        read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )
    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Alert
        fields = [
            'id',
            'alert_type',
            'alert_type_display',
            'severity',
            'severity_display',
            'title',
            'branch_name',
            'status',
            'is_read',
            'created_at',
        ]


class AlertConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for AlertConfiguration model."""
    scope_display = serializers.CharField(
        source='get_scope_display',
        read_only=True
    )
    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True,
        allow_null=True
    )
    category_name = serializers.CharField(
        source='category.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = AlertConfiguration
        fields = [
            'id',
            'scope',
            'scope_display',
            'branch',
            'branch_name',
            'category',
            'category_name',
            'low_stock_threshold',
            'overstock_threshold',
            'cash_difference_threshold',
            'void_rate_threshold',
            'overtime_threshold',
            'email_notifications',
            'dashboard_notifications',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        scope = attrs.get('scope', self.instance.scope if self.instance else 'global')

        if scope == 'branch' and not attrs.get('branch'):
            raise serializers.ValidationError({
                'branch': 'Se requiere una sucursal para configuración por sucursal.'
            })

        if scope == 'category' and not attrs.get('category'):
            raise serializers.ValidationError({
                'category': 'Se requiere una categoría para configuración por categoría.'
            })

        if scope == 'global':
            attrs['branch'] = None
            attrs['category'] = None

        return attrs


class UserAlertPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for UserAlertPreference model."""
    minimum_severity_display = serializers.CharField(
        source='get_minimum_severity_display',
        read_only=True
    )

    class Meta:
        model = UserAlertPreference
        fields = [
            'receive_low_stock',
            'receive_out_of_stock',
            'receive_cash_difference',
            'receive_void_alerts',
            'receive_shift_alerts',
            'receive_system_alerts',
            'minimum_severity',
            'minimum_severity_display',
            'email_digest',
        ]


class AlertActionSerializer(serializers.Serializer):
    """Serializer for alert actions."""
    notes = serializers.CharField(required=False, allow_blank=True)


class BulkAlertActionSerializer(serializers.Serializer):
    """Serializer for bulk alert actions."""
    alert_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class AlertFilterSerializer(serializers.Serializer):
    """Serializer for alert filtering parameters."""
    branch_id = serializers.IntegerField(required=False, allow_null=True)
    alert_type = serializers.ChoiceField(
        choices=Alert.ALERT_TYPE_CHOICES,
        required=False
    )
    status = serializers.ChoiceField(
        choices=Alert.STATUS_CHOICES,
        required=False
    )
    severity = serializers.ChoiceField(
        choices=Alert.SEVERITY_CHOICES,
        required=False
    )
    is_read = serializers.BooleanField(required=False, allow_null=True)
    limit = serializers.IntegerField(default=50, min_value=1, max_value=200)


class AlertCountResponseSerializer(serializers.Serializer):
    """Response serializer for alert counts."""
    total = serializers.IntegerField()
    critical = serializers.IntegerField()
    high = serializers.IntegerField()
    medium = serializers.IntegerField()
    low = serializers.IntegerField()
