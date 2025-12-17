"""
Views for companies app.
SuperAdmin only - platform-level company management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce

from .models import Company, Subscription
from .serializers import (
    CompanySerializer,
    CompanyListSerializer,
    CompanyCreateSerializer,
    CompanySimpleSerializer,
    SubscriptionSerializer,
    SubscriptionListSerializer,
    CompanyAdminSerializer,
)
from .permissions import IsSuperUser
from apps.users.models import User


@extend_schema_view(
    list=extend_schema(tags=['Empresas (Admin)']),
    create=extend_schema(tags=['Empresas (Admin)']),
    retrieve=extend_schema(tags=['Empresas (Admin)']),
    update=extend_schema(tags=['Empresas (Admin)']),
    partial_update=extend_schema(tags=['Empresas (Admin)']),
    destroy=extend_schema(tags=['Empresas (Admin)']),
)
class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for platform-level company management.
    Only accessible by SuperAdmins (platform administrators).
    """
    queryset = Company.active_objects.all()
    permission_classes = [IsAuthenticated, IsSuperUser]
    filterset_fields = ['plan', 'is_active']
    search_fields = ['name', 'slug', 'email', 'legal_name']
    ordering_fields = ['name', 'created_at', 'plan']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'create':
            return CompanyCreateSerializer
        if self.action == 'list':
            return CompanyListSerializer
        return CompanySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Include inactive if requested
        if self.request.query_params.get('include_inactive') == 'true':
            queryset = Company.objects.filter(is_deleted=False)

        return queryset

    def perform_destroy(self, instance):
        """Soft delete the company."""
        instance.soft_delete(user=self.request.user)

    @extend_schema(
        tags=['Empresas (Admin)'],
        responses={200: CompanySerializer}
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a company."""
        company = self.get_object()
        company.is_active = True
        company.save(update_fields=['is_active'])
        serializer = CompanySerializer(company)
        return Response(serializer.data)

    @extend_schema(
        tags=['Empresas (Admin)'],
        responses={200: CompanySerializer}
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a company (keeps data but blocks access)."""
        company = self.get_object()
        company.is_active = False
        company.save(update_fields=['is_active'])
        serializer = CompanySerializer(company)
        return Response(serializer.data)

    @extend_schema(tags=['Empresas (Admin)'])
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """Get simple list of companies for dropdowns."""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = CompanySimpleSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(tags=['Empresas (Admin)'])
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get detailed statistics for a company."""
        company = self.get_object()

        stats = {
            'company': CompanySerializer(company).data,
            'limits': company.get_plan_limits(),
            'usage': {
                'branches_used': company.branch_count,
                'branches_remaining': company.max_branches - company.branch_count,
                'users_used': company.user_count,
                'users_remaining': company.max_users - company.user_count,
                'products_used': company.product_count,
                'products_remaining': company.max_products - company.product_count,
            },
            'can_add': {
                'branch': company.can_add_branch(),
                'user': company.can_add_user(),
                'product': company.can_add_product(),
            }
        }

        return Response(stats)

    @extend_schema(
        tags=['Empresas (Admin)'],
        responses={200: CompanyAdminSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def admins(self, request):
        """Get all company administrators grouped by company.

        Returns a list of all users who are company admins or have admin role,
        along with their company information. Used by SuperAdmin to manage
        company administrators and their permissions.
        """
        # Get all company admins (users with is_company_admin=True or admin role)
        admins = User.objects.filter(
            Q(is_company_admin=True) | Q(role__role_type='admin'),
            company__isnull=False,
            is_active=True
        ).select_related('company', 'role').order_by('company__name', 'first_name')

        serializer = CompanyAdminSerializer(admins, many=True)
        return Response(serializer.data)

    @extend_schema(tags=['Empresas (Admin)'])
    @action(detail=True, methods=['get'])
    def company_admins(self, request, pk=None):
        """Get administrators for a specific company.

        Returns all admin users for a particular company, including
        their role and permissions status.
        """
        company = self.get_object()
        admins = User.objects.filter(
            Q(is_company_admin=True) | Q(role__role_type='admin'),
            company=company,
            is_active=True
        ).select_related('role')

        serializer = CompanyAdminSerializer(admins, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Empresas (Admin)'],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'can_create_roles': {'type': 'boolean'}
                }
            }
        },
        responses={200: CompanyAdminSerializer}
    )
    @action(detail=False, methods=['patch'], url_path='admins/(?P<user_id>[^/.]+)/permissions')
    def update_admin_permissions(self, request, user_id=None):
        """Update permissions for a company administrator.

        Allows SuperAdmin to enable/disable role creation permission
        for company administrators.
        """
        try:
            admin = User.objects.select_related('company', 'role').get(
                id=user_id,
                company__isnull=False
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is actually an admin
        if not (admin.is_company_admin or (admin.role and admin.role.role_type == 'admin')):
            return Response(
                {'error': 'El usuario no es administrador de empresa'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update can_create_roles if provided
        if 'can_create_roles' in request.data:
            admin.can_create_roles = request.data['can_create_roles']
            admin.save(update_fields=['can_create_roles'])

        serializer = CompanyAdminSerializer(admin)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Suscripciones (Admin)']),
    retrieve=extend_schema(tags=['Suscripciones (Admin)']),
    update=extend_schema(tags=['Suscripciones (Admin)']),
    partial_update=extend_schema(tags=['Suscripciones (Admin)']),
)
class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for platform-level subscription management.
    Only accessible by SuperAdmins (platform administrators).
    """
    queryset = Subscription.objects.select_related('company').all()
    permission_classes = [IsAuthenticated, IsSuperUser]
    http_method_names = ['get', 'patch', 'head', 'options']  # No create/delete
    filterset_fields = ['plan', 'status', 'billing_cycle']
    search_fields = ['company__name', 'company__email']
    ordering_fields = ['next_payment_date', 'amount', 'created_at', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return SubscriptionListSerializer
        return SubscriptionSerializer

    @extend_schema(tags=['Suscripciones (Admin)'])
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get subscription statistics for dashboard."""
        from django.db.models import Sum, Count, DecimalField, Value
        from datetime import date, timedelta

        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        # Base queryset
        subscriptions = Subscription.objects.all()

        # Calculate MRR safely (handle None from empty queryset)
        mrr_result = subscriptions.filter(
            status__in=['active'],
            billing_cycle='monthly'
        ).aggregate(
            total=Coalesce(
                Sum('amount'),
                Value(0, output_field=DecimalField())
            )
        )['total']

        # Calculate stats
        stats = {
            'total_subscriptions': subscriptions.count(),
            'active_subscriptions': subscriptions.filter(
                status__in=['trial', 'active']
            ).count(),
            'trial_subscriptions': subscriptions.filter(status='trial').count(),
            'past_due_subscriptions': subscriptions.filter(status='past_due').count(),
            'cancelled_subscriptions': subscriptions.filter(status='cancelled').count(),
            'new_this_month': subscriptions.filter(
                created_at__gte=thirty_days_ago
            ).count(),
            'mrr': float(mrr_result) if mrr_result is not None else 0.0,
            'by_plan': list(subscriptions.values('plan').annotate(
                count=Count('id')
            ).order_by('plan')),
            'by_status': list(subscriptions.values('status').annotate(
                count=Count('id')
            ).order_by('status')),
            'upcoming_payments': subscriptions.filter(
                next_payment_date__lte=today + timedelta(days=7),
                next_payment_date__gte=today,
                status='active'
            ).count(),
        }

        return Response(stats)

    @extend_schema(tags=['Suscripciones (Admin)'])
    @action(detail=False, methods=['get'])
    def platform_usage(self, request):
        """Get platform revenue and usage statistics for SuperAdmin dashboard.

        Shows SaaS revenue metrics (subscription income), NOT client sales data.
        """
        from django.db.models import Sum, Count, DecimalField, Value
        from django.utils import timezone
        from datetime import timedelta
        from apps.users.models import User

        now = timezone.now()
        today = now.date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)

        # All subscriptions
        subscriptions = Subscription.objects.select_related('company').all()
        active_subs = subscriptions.filter(status__in=['active', 'trial'])

        # === REVENUE METRICS (SaaS income) ===

        # MRR - Monthly Recurring Revenue (active monthly subscriptions)
        mrr = active_subs.filter(
            billing_cycle='monthly'
        ).aggregate(
            total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))
        )['total']

        # ARR approximation (MRR * 12 + annual subscriptions)
        annual_revenue = active_subs.filter(
            billing_cycle='annual'
        ).aggregate(
            total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))
        )['total']

        quarterly_revenue = active_subs.filter(
            billing_cycle='quarterly'
        ).aggregate(
            total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))
        )['total']

        # Expected revenue this month
        expected_this_month = subscriptions.filter(
            next_payment_date__gte=this_month_start,
            next_payment_date__lte=today.replace(day=28),  # Approximate month end
            status='active'
        ).aggregate(
            total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))
        )['total']

        # Upcoming payments (next 7 days)
        next_week = today + timedelta(days=7)
        upcoming_payments = subscriptions.filter(
            next_payment_date__gte=today,
            next_payment_date__lte=next_week,
            status='active'
        )
        upcoming_count = upcoming_payments.count()
        upcoming_amount = upcoming_payments.aggregate(
            total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))
        )['total']

        # Overdue payments (past_due status)
        overdue_subs = subscriptions.filter(status='past_due')
        overdue_count = overdue_subs.count()
        overdue_amount = overdue_subs.aggregate(
            total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))
        )['total']

        # New subscriptions this month
        new_this_month = subscriptions.filter(
            created_at__gte=this_month_start
        )
        new_count = new_this_month.count()
        new_revenue = new_this_month.filter(
            status__in=['active', 'trial']
        ).aggregate(
            total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))
        )['total']

        # Last month comparison
        new_last_month = subscriptions.filter(
            created_at__gte=last_month_start,
            created_at__lt=this_month_start
        ).count()

        # === SUBSCRIPTION DISTRIBUTION ===

        # Revenue by plan
        revenue_by_plan = list(
            active_subs.values('plan').annotate(
                count=Count('id'),
                total_revenue=Sum('amount')
            ).order_by('-total_revenue')
        )

        # Top paying companies
        top_subscribers = list(
            active_subs.filter(
                amount__gt=0
            ).values(
                'company__id',
                'company__name',
                'plan',
                'amount',
                'billing_cycle'
            ).order_by('-amount')[:5]
        )

        # === PLATFORM HEALTH ===

        # Total counts
        total_companies = Company.active_objects.count()
        total_users = User.objects.filter(is_active=True, company__isnull=False).count()

        # Subscription status distribution
        status_distribution = list(
            subscriptions.values('status').annotate(
                count=Count('id')
            ).order_by('status')
        )

        # Churn risk (trials ending in 7 days)
        trials_ending_soon = subscriptions.filter(
            status='trial',
            trial_ends_at__gte=today,
            trial_ends_at__lte=next_week
        ).count()

        # Calculate percentage changes
        def calc_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 1)

        usage_stats = {
            # Revenue metrics
            'mrr': {
                'total': float(mrr) if mrr else 0,
                'currency': 'COP',
            },
            'expected_revenue': {
                'this_month': float(expected_this_month) if expected_this_month else 0,
                'currency': 'COP',
            },
            'upcoming_payments': {
                'count': upcoming_count,
                'amount': float(upcoming_amount) if upcoming_amount else 0,
                'days': 7,
            },
            'overdue_payments': {
                'count': overdue_count,
                'amount': float(overdue_amount) if overdue_amount else 0,
            },
            'new_subscriptions': {
                'count': new_count,
                'revenue': float(new_revenue) if new_revenue else 0,
                'last_month_count': new_last_month,
                'change_percent': calc_change(new_count, new_last_month),
            },
            # Distribution
            'revenue_by_plan': [
                {
                    'plan': item['plan'],
                    'count': item['count'],
                    'revenue': float(item['total_revenue']) if item['total_revenue'] else 0,
                }
                for item in revenue_by_plan
            ],
            'top_subscribers': [
                {
                    'id': sub['company__id'],
                    'name': sub['company__name'],
                    'plan': sub['plan'],
                    'amount': float(sub['amount']) if sub['amount'] else 0,
                    'billing_cycle': sub['billing_cycle'],
                }
                for sub in top_subscribers
            ],
            # Platform health
            'total_companies': total_companies,
            'total_users': total_users,
            'status_distribution': [
                {'status': item['status'], 'count': item['count']}
                for item in status_distribution
            ],
            'trials_ending_soon': trials_ending_soon,
            # Summary totals
            'active_subscriptions': active_subs.count(),
            'total_subscriptions': subscriptions.count(),
        }

        return Response(usage_stats)
