"""
Serializers for companies app.
"""
from rest_framework import serializers
from .models import Company, Subscription


class CompanySerializer(serializers.ModelSerializer):
    """Full serializer for Company model."""
    branch_count = serializers.IntegerField(read_only=True)
    user_count = serializers.IntegerField(read_only=True)
    product_count = serializers.IntegerField(read_only=True)
    plan_limits = serializers.SerializerMethodField()
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'legal_name', 'tax_id',
            # Branding
            'logo', 'primary_color', 'secondary_color',
            # Contact
            'email', 'phone', 'website', 'address',
            # Plan & Limits
            'plan', 'max_branches', 'max_users', 'max_products',
            # Status
            'is_active', 'owner', 'owner_email',
            # Computed
            'branch_count', 'user_count', 'product_count', 'plan_limits',
            # Timestamps
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'branch_count',
            'user_count', 'product_count', 'owner_email'
        ]

    def get_plan_limits(self, obj):
        return obj.get_plan_limits()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    billing_cycle_display = serializers.CharField(source='get_billing_cycle_display', read_only=True)
    plan_display = serializers.CharField(source='get_plan_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_until_payment = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'plan_display', 'status', 'status_display',
            'billing_cycle', 'billing_cycle_display',
            'start_date', 'next_payment_date', 'trial_ends_at',
            'amount', 'currency', 'notes',
            'is_active', 'days_until_payment',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class CompanyListSerializer(serializers.ModelSerializer):
    """Simplified serializer for company listings."""
    branch_count = serializers.IntegerField(read_only=True)
    user_count = serializers.IntegerField(read_only=True)
    subscription_status = serializers.CharField(
        source='subscription.status',
        read_only=True,
        default=None
    )
    subscription_status_display = serializers.CharField(
        source='subscription.get_status_display',
        read_only=True,
        default=None
    )
    next_payment_date = serializers.DateField(
        source='subscription.next_payment_date',
        read_only=True,
        default=None
    )

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'email', 'plan',
            'is_active', 'branch_count', 'user_count',
            'primary_color', 'created_at',
            'subscription_status', 'subscription_status_display', 'next_payment_date',
        ]


class CompanyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating companies."""

    class Meta:
        model = Company
        fields = [
            'name', 'slug', 'legal_name', 'tax_id',
            'logo', 'primary_color', 'secondary_color',
            'email', 'phone', 'website', 'address',
            'plan', 'max_branches', 'max_users', 'max_products',
            'is_active', 'owner'
        ]

    def validate_slug(self, value):
        """Ensure slug is lowercase and URL-safe."""
        return value.lower().replace(' ', '-')

    def validate_primary_color(self, value):
        """Ensure color is valid hex format."""
        if value and not value.startswith('#'):
            value = f'#{value}'
        if value and len(value) != 7:
            raise serializers.ValidationError(
                'Color must be in hex format (e.g., #2563eb)'
            )
        return value

    validate_secondary_color = validate_primary_color


class CompanySimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for dropdowns and selections."""

    class Meta:
        model = Company
        fields = ['id', 'name', 'slug', 'primary_color', 'is_active']
