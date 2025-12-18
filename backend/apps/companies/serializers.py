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
    subscription_status = serializers.ChoiceField(
        choices=Subscription.STATUS_CHOICES,
        required=False,
        write_only=True,
        help_text='Estado de la suscripción (solo escritura)'
    )

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
            # Subscription
            'subscription_status',
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

    def update(self, instance, validated_data):
        """Update company and optionally update subscription status."""
        subscription_status = validated_data.pop('subscription_status', None)
        company = super().update(instance, validated_data)

        # Update subscription status if provided
        if subscription_status and hasattr(company, 'subscription'):
            subscription = company.subscription
            subscription.status = subscription_status
            subscription.save(update_fields=['status'])

        return company


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
    billing_cycle = serializers.ChoiceField(
        choices=Subscription.BILLING_CYCLE_CHOICES,
        default='monthly',
        write_only=True,
        help_text='Ciclo de facturación para la suscripción'
    )
    subscription_status = serializers.ChoiceField(
        choices=Subscription.STATUS_CHOICES,
        default='trial',
        write_only=True,
        help_text='Estado inicial de la suscripción'
    )

    class Meta:
        model = Company
        fields = [
            'name', 'slug', 'legal_name', 'tax_id',
            'logo', 'primary_color', 'secondary_color',
            'email', 'phone', 'website', 'address',
            'plan', 'max_branches', 'max_users', 'max_products',
            'is_active', 'owner',
            'billing_cycle', 'subscription_status',
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

    def create(self, validated_data):
        """Create company and mark it to skip signal subscription creation."""
        billing_cycle = validated_data.pop('billing_cycle', 'monthly')
        subscription_status = validated_data.pop('subscription_status', 'trial')
        company = super().create(validated_data)
        # Store for signal to use
        company._billing_cycle = billing_cycle
        company._subscription_status = subscription_status
        return company


class CompanySimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for dropdowns and selections."""

    class Meta:
        model = Company
        fields = ['id', 'name', 'slug', 'primary_color', 'is_active']


class SubscriptionListSerializer(serializers.ModelSerializer):
    """Serializer for subscription listings with company info."""
    company_id = serializers.IntegerField(source='company.id', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_email = serializers.EmailField(source='company.email', read_only=True)
    company_is_active = serializers.BooleanField(source='company.is_active', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    billing_cycle_display = serializers.CharField(source='get_billing_cycle_display', read_only=True)
    plan_display = serializers.CharField(source='get_plan_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_until_payment = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'company_id', 'company_name', 'company_email', 'company_is_active',
            'plan', 'plan_display', 'status', 'status_display',
            'billing_cycle', 'billing_cycle_display',
            'start_date', 'next_payment_date', 'trial_ends_at',
            'amount', 'currency',
            'is_active', 'days_until_payment',
            'created_at', 'updated_at',
        ]


class CompanyAdminSerializer(serializers.Serializer):
    """Serializer for company administrators list.

    Used by SuperAdmin to view all company admins across the platform.
    """
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.CharField()
    is_company_admin = serializers.BooleanField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    # Company info
    company_id = serializers.IntegerField(source='company.id')
    company_name = serializers.CharField(source='company.name')
    company_slug = serializers.CharField(source='company.slug')
    company_plan = serializers.CharField(source='company.plan')
    company_is_active = serializers.BooleanField(source='company.is_active')

    # Role info
    role_id = serializers.IntegerField(source='role.id', allow_null=True)
    role_name = serializers.CharField(source='role.name', allow_null=True)
    role_type = serializers.CharField(source='role.role_type', allow_null=True)

    # Permission to create new roles (configurable by SuperAdmin)
    can_create_roles = serializers.BooleanField()

    # Computed field: can this admin manage (edit) roles for their company?
    can_manage_roles = serializers.SerializerMethodField()

    def get_can_manage_roles(self, obj):
        """Check if this admin can manage (edit) roles for their company.

        Company admins can edit roles for their company.
        Creating new roles depends on can_create_roles flag.
        """
        if obj.is_company_admin:
            return True
        if obj.role and obj.role.role_type == 'admin':
            return True
        return False
