"""
Views for branches app.
"""
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.users.permissions import HasPermission
from .models import Branch
from .serializers import (
    BranchSerializer,
    BranchSimpleSerializer,
    BranchCreateSerializer,
    BranchStatsSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=['Sucursales']),
    create=extend_schema(tags=['Sucursales']),
    retrieve=extend_schema(tags=['Sucursales']),
    update=extend_schema(tags=['Sucursales']),
    partial_update=extend_schema(tags=['Sucursales']),
    destroy=extend_schema(tags=['Sucursales']),
)
class BranchViewSet(viewsets.ModelViewSet):
    """ViewSet for branch management."""
    queryset = Branch.active.all()
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'branches:view'
    filterset_fields = ['is_active', 'is_main', 'city', 'state']
    search_fields = ['name', 'code', 'city']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'create':
            return BranchCreateSerializer
        if self.action == 'list' and self.request.query_params.get('simple'):
            return BranchSimpleSerializer
        return BranchSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.required_permission = 'branches:edit'
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()

        # Non-admin users only see their allowed branches
        user = self.request.user
        if not user.is_superuser and hasattr(user, 'allowed_branches'):
            allowed = user.allowed_branches.values_list('id', flat=True)
            if allowed:
                queryset = queryset.filter(id__in=allowed)

        return queryset

    @extend_schema(
        tags=['Sucursales'],
        responses={200: BranchStatsSerializer}
    )
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for a specific branch."""
        branch = self.get_object()
        today = timezone.now().date()
        first_of_month = today.replace(day=1)

        # Calculate statistics (placeholder values until inventory/sales apps are implemented)
        # These will be updated when the related models exist
        stats = {
            'total_products': 0,
            'total_stock_value': Decimal('0.00'),
            'sales_today': 0,
            'sales_amount_today': Decimal('0.00'),
            'sales_this_month': 0,
            'sales_amount_this_month': Decimal('0.00'),
            'active_employees': branch.default_users.filter(is_active=True).count(),
            'low_stock_alerts': 0,
        }

        # Try to get actual stats if models exist
        try:
            from apps.inventory.models import BranchStock
            stock_data = BranchStock.objects.filter(branch=branch).aggregate(
                total_products=Count('id'),
                total_value=Sum('quantity' * 'product__cost_price')
            )
            stats['total_products'] = stock_data.get('total_products', 0) or 0
        except ImportError:
            pass

        try:
            from apps.sales.models import Sale
            sales_today = Sale.objects.filter(
                branch=branch,
                created_at__date=today,
                is_voided=False
            ).aggregate(
                count=Count('id'),
                total=Sum('total_amount')
            )
            sales_month = Sale.objects.filter(
                branch=branch,
                created_at__date__gte=first_of_month,
                is_voided=False
            ).aggregate(
                count=Count('id'),
                total=Sum('total_amount')
            )
            stats['sales_today'] = sales_today.get('count', 0) or 0
            stats['sales_amount_today'] = sales_today.get('total') or Decimal('0.00')
            stats['sales_this_month'] = sales_month.get('count', 0) or 0
            stats['sales_amount_this_month'] = sales_month.get('total') or Decimal('0.00')
        except ImportError:
            pass

        serializer = BranchStatsSerializer(stats)
        return Response(serializer.data)

    @extend_schema(tags=['Sucursales'])
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """Get simple list of branches for dropdowns."""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = BranchSimpleSerializer(queryset, many=True)
        return Response(serializer.data)
