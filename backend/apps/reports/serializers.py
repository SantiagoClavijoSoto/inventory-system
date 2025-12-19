"""
Serializers for report parameters and responses.
"""
from rest_framework import serializers
from datetime import date, timedelta

from .models import UserReport
from apps.employees.models import Employee


class DateRangeSerializer(serializers.Serializer):
    """
    Serializer for date range parameters.
    """
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    branch_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')

        # Default to last 30 days if not provided
        if not date_to:
            attrs['date_to'] = date.today()
        if not date_from:
            attrs['date_from'] = attrs['date_to'] - timedelta(days=30)

        if attrs['date_from'] > attrs['date_to']:
            raise serializers.ValidationError({
                'date_from': 'La fecha inicial no puede ser mayor que la fecha final.'
            })

        # Limit range to 1 year
        if (attrs['date_to'] - attrs['date_from']).days > 365:
            raise serializers.ValidationError({
                'date_from': 'El rango máximo es de 1 año.'
            })

        return attrs


class SalesPeriodSerializer(DateRangeSerializer):
    """
    Serializer for sales period report parameters.
    """
    GROUP_CHOICES = [
        ('day', 'Día'),
        ('week', 'Semana'),
        ('month', 'Mes'),
    ]

    group_by = serializers.ChoiceField(
        choices=GROUP_CHOICES,
        default='day',
        required=False
    )


class TopProductsSerializer(serializers.Serializer):
    """
    Serializer for top products report parameters.
    """
    days = serializers.IntegerField(default=30, min_value=1, max_value=365)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=100)
    branch_id = serializers.IntegerField(required=False, allow_null=True)


class PeriodComparisonSerializer(serializers.Serializer):
    """
    Serializer for period comparison parameters.
    """
    days = serializers.IntegerField(default=7, min_value=1, max_value=90)
    branch_id = serializers.IntegerField(required=False, allow_null=True)


class HourlySalesSerializer(serializers.Serializer):
    """
    Serializer for hourly sales report parameters.
    """
    target_date = serializers.DateField(required=False)
    branch_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_target_date(self, value):
        if not value:
            return date.today()
        return value


class ProductMovementSerializer(serializers.Serializer):
    """
    Serializer for product movement history parameters.
    """
    product_id = serializers.IntegerField()
    branch_id = serializers.IntegerField(required=False, allow_null=True)
    days = serializers.IntegerField(default=30, min_value=1, max_value=365)


class LowStockSerializer(serializers.Serializer):
    """
    Serializer for low stock report parameters.
    """
    branch_id = serializers.IntegerField(required=False, allow_null=True)
    limit = serializers.IntegerField(default=50, min_value=1, max_value=200)


# Response Serializers (for documentation purposes)

class TodaySummaryResponseSerializer(serializers.Serializer):
    """Response serializer for today's summary."""
    date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_transactions = serializers.IntegerField()
    total_items = serializers.IntegerField()
    avg_ticket = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()


class PeriodComparisonResponseSerializer(serializers.Serializer):
    """Response serializer for period comparison."""

    class PeriodDataSerializer(serializers.Serializer):
        start = serializers.DateField()
        end = serializers.DateField()
        total = serializers.DecimalField(max_digits=12, decimal_places=2)
        transactions = serializers.IntegerField()

    current_period = PeriodDataSerializer()
    previous_period = PeriodDataSerializer()
    change_percent = serializers.DecimalField(max_digits=6, decimal_places=2)
    trend = serializers.ChoiceField(choices=['up', 'down', 'stable'])


class LowStockCountResponseSerializer(serializers.Serializer):
    """Response serializer for low stock count."""
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    total_alerts = serializers.IntegerField()


class TopProductResponseSerializer(serializers.Serializer):
    """Response serializer for top products."""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    total_quantity = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=12, decimal_places=2)


class SalesByPeriodResponseSerializer(serializers.Serializer):
    """Response serializer for sales by period."""
    period = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_transactions = serializers.IntegerField()
    total_items = serializers.IntegerField()
    avg_ticket = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_discounts = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_tax = serializers.DecimalField(max_digits=10, decimal_places=2)


class StockSummaryResponseSerializer(serializers.Serializer):
    """Response serializer for stock summary."""
    total_products = serializers.IntegerField()
    total_units = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_retail_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    potential_profit = serializers.DecimalField(max_digits=14, decimal_places=2)
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()


# =============================================================================
# USER REPORT SERIALIZERS
# =============================================================================

class UserReportSerializer(serializers.ModelSerializer):
    """Full serializer for UserReport model."""
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    reviewed_by_name = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()
    assigned_employee_names = serializers.SerializerMethodField()
    can_change_status = serializers.SerializerMethodField()

    class Meta:
        model = UserReport
        fields = [
            'id',
            'title',
            'description',
            'category',
            'category_display',
            'priority',
            'priority_display',
            'status',
            'status_display',
            'created_by',
            'created_by_name',
            'assign_to_all',
            'assigned_employees',
            'assigned_employee_names',
            'reviewed_at',
            'reviewed_by',
            'reviewed_by_name',
            'resolved_at',
            'resolved_by',
            'resolved_by_name',
            'resolution_notes',
            'can_change_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'created_by', 'reviewed_at', 'reviewed_by',
            'resolved_at', 'resolved_by', 'created_at', 'updated_at'
        ]

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name()
        return None

    def get_resolved_by_name(self, obj):
        if obj.resolved_by:
            return obj.resolved_by.get_full_name()
        return None

    def get_assigned_employee_names(self, obj):
        if obj.assign_to_all:
            return ['Todos los empleados']
        employees = obj.assigned_employees.all()
        return [emp.full_name for emp in employees]

    def get_can_change_status(self, obj):
        """Check if current user can change the status of this report."""
        request = self.context.get('request')
        if not request or not request.user:
            return False

        user = request.user

        # Already resolved - no one can change
        if obj.status == 'resuelto':
            return False

        # Admins can always change status
        is_admin = user.is_superuser or (
            user.role and user.role.role_type == 'admin'
        ) or getattr(user, 'is_platform_admin', False)

        if is_admin:
            return True

        # Assigned employees can change status of reports assigned to them
        employee_profile = getattr(user, 'employee_profile', None)
        if employee_profile and obj.category == 'empleados':
            if obj.assign_to_all:
                return True
            if obj.assigned_employees.filter(id=employee_profile.id).exists():
                return True

        return False


class UserReportListSerializer(serializers.ModelSerializer):
    """Compact serializer for report lists."""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = UserReport
        fields = [
            'id', 'title', 'category', 'category_display',
            'priority', 'priority_display', 'status', 'status_display',
            'created_by_name', 'created_at',
        ]


class UserReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reports."""
    assigned_employees = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Employee.objects.all(),
        required=False
    )

    class Meta:
        model = UserReport
        fields = [
            'title', 'description', 'category', 'priority',
            'assign_to_all', 'assigned_employees'
        ]

    def validate_category(self, value):
        """Validate category based on user permissions."""
        request = self.context.get('request')
        if not request:
            return value

        user = request.user
        is_admin = user.is_superuser or (
            user.role and user.role.role_type == 'admin'
        )

        # Regular users cannot create 'empleados' reports
        if value == 'empleados' and not is_admin:
            raise serializers.ValidationError(
                "No tiene permiso para crear reportes de empleados."
            )
        return value

    def validate(self, attrs):
        """Validate assignment fields."""
        category = attrs.get('category')
        assign_to_all = attrs.get('assign_to_all', False)
        assigned_employees = attrs.get('assigned_employees', [])

        # Assignment only valid for 'empleados' category
        if category != 'empleados':
            attrs['assign_to_all'] = False
            attrs['assigned_employees'] = []
        else:
            # If specific employees are assigned, force assign_to_all=False
            # This ensures mutual exclusivity between the two assignment modes
            if assigned_employees:
                attrs['assign_to_all'] = False

        return attrs


class UserReportFilterSerializer(serializers.Serializer):
    """Serializer for filtering reports."""
    category = serializers.ChoiceField(
        choices=UserReport.CATEGORY_CHOICES,
        required=False
    )
    status = serializers.ChoiceField(
        choices=UserReport.STATUS_CHOICES,
        required=False
    )
    priority = serializers.ChoiceField(
        choices=UserReport.PRIORITY_CHOICES,
        required=False
    )
    mine_only = serializers.BooleanField(required=False, default=False)


class StatusChangeSerializer(serializers.Serializer):
    """Serializer for status change actions."""
    notes = serializers.CharField(required=False, allow_blank=True, default='')
