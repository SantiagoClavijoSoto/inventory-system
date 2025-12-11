"""
Serializers for Employee module.
"""
from rest_framework import serializers
from decimal import Decimal

from apps.users.models import User
from apps.branches.models import Branch
from .models import Employee, Shift


class EmployeeUserSerializer(serializers.ModelSerializer):
    """Nested serializer for User data in Employee."""
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'phone', 'avatar']
        read_only_fields = ['id', 'email', 'full_name']


class EmployeeBranchSerializer(serializers.ModelSerializer):
    """Nested serializer for Branch in Employee."""
    class Meta:
        model = Branch
        fields = ['id', 'name', 'code']


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer for employee list view."""
    user = EmployeeUserSerializer(read_only=True)
    branch = EmployeeBranchSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    is_clocked_in = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_code', 'user', 'branch', 'full_name',
            'position', 'department', 'employment_type', 'status',
            'hire_date', 'is_clocked_in'
        ]

    def get_is_clocked_in(self, obj):
        return obj.is_clocked_in()


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Serializer for employee detail view with all fields."""
    user = EmployeeUserSerializer(read_only=True)
    branch = EmployeeBranchSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    years_of_service = serializers.IntegerField(read_only=True)
    is_clocked_in = serializers.SerializerMethodField()
    current_shift = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_code', 'user', 'branch',
            'full_name', 'email', 'position', 'department',
            'employment_type', 'status', 'hire_date', 'termination_date',
            'salary', 'hourly_rate',
            'emergency_contact_name', 'emergency_contact_phone', 'address',
            'tax_id', 'social_security_number',
            'notes', 'years_of_service',
            'is_clocked_in', 'current_shift',
            'created_at', 'updated_at'
        ]

    def get_is_clocked_in(self, obj):
        return obj.is_clocked_in()

    def get_current_shift(self, obj):
        shift = obj.get_current_shift()
        if shift:
            return ShiftSerializer(shift).data
        return None


class CreateEmployeeSerializer(serializers.Serializer):
    """Serializer for creating a new employee with user."""
    # User fields
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    role_id = serializers.IntegerField(required=False, allow_null=True)

    # Employee fields
    branch_id = serializers.IntegerField()
    position = serializers.CharField(max_length=100)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    employment_type = serializers.ChoiceField(
        choices=Employee.EMPLOYMENT_TYPE_CHOICES,
        default='full_time'
    )
    hire_date = serializers.DateField()
    salary = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal('0.00')
    )
    hourly_rate = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal('0.00')
    )
    emergency_contact_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    tax_id = serializers.CharField(max_length=20, required=False, allow_blank=True)
    social_security_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este email")
        return value

    def validate_branch_id(self, value):
        if not Branch.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Sucursal no encontrada o inactiva")
        return value


class UpdateEmployeeSerializer(serializers.ModelSerializer):
    """Serializer for updating employee data."""
    # Allow updating some user fields
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'phone',
            'branch', 'position', 'department', 'employment_type',
            'status', 'termination_date',
            'salary', 'hourly_rate',
            'emergency_contact_name', 'emergency_contact_phone', 'address',
            'tax_id', 'social_security_number', 'notes'
        ]

    def update(self, instance, validated_data):
        # Extract and update user fields
        user_fields = ['first_name', 'last_name', 'phone']
        user_data = {}
        for field in user_fields:
            if field in validated_data:
                user_data[field] = validated_data.pop(field)

        if user_data:
            for key, value in user_data.items():
                setattr(instance.user, key, value)
            instance.user.save()

        # Update employee fields
        return super().update(instance, validated_data)


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift model."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    is_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = Shift
        fields = [
            'id', 'employee', 'employee_name', 'branch', 'branch_name',
            'clock_in', 'clock_out',
            'break_start', 'break_end',
            'total_hours', 'break_hours', 'worked_hours',
            'notes', 'is_manual_entry', 'adjusted_by',
            'is_complete', 'created_at'
        ]
        read_only_fields = [
            'id', 'total_hours', 'break_hours', 'worked_hours',
            'is_complete', 'created_at'
        ]


class ClockInSerializer(serializers.Serializer):
    """Serializer for clock-in action."""
    branch_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_branch_id(self, value):
        if value and not Branch.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Sucursal no encontrada o inactiva")
        return value


class ClockOutSerializer(serializers.Serializer):
    """Serializer for clock-out action."""
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class ManualShiftSerializer(serializers.ModelSerializer):
    """Serializer for creating/editing shifts manually."""
    class Meta:
        model = Shift
        fields = [
            'employee', 'branch', 'clock_in', 'clock_out',
            'break_start', 'break_end', 'notes'
        ]

    def create(self, validated_data):
        validated_data['is_manual_entry'] = True
        validated_data['adjusted_by'] = self.context['request'].user
        return super().create(validated_data)


class EmployeeStatsSerializer(serializers.Serializer):
    """Serializer for employee statistics."""
    total_shifts = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_sale = serializers.DecimalField(max_digits=12, decimal_places=2)
    period_start = serializers.DateField()
    period_end = serializers.DateField()


class ShiftSummarySerializer(serializers.Serializer):
    """Serializer for shift summary reports."""
    date = serializers.DateField()
    total_employees = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    shifts_count = serializers.IntegerField()
