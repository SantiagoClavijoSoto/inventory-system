"""
API Views for Supplier module.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Sum, Count, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Supplier, PurchaseOrder, PurchaseOrderItem
from core.mixins import TenantQuerySetMixin
from .serializers import (
    SupplierListSerializer,
    SupplierDetailSerializer,
    CreateSupplierSerializer,
    UpdateSupplierSerializer,
    PurchaseOrderListSerializer,
    PurchaseOrderDetailSerializer,
    CreatePurchaseOrderSerializer,
    UpdatePurchaseOrderSerializer,
    ReceiveItemSerializer,
)
from core.pagination import StandardResultsSetPagination
from apps.users.permissions import HasPermission


@extend_schema_view(
    list=extend_schema(description='List all suppliers'),
    retrieve=extend_schema(description='Get supplier details'),
    create=extend_schema(description='Create new supplier'),
    update=extend_schema(description='Update supplier'),
    destroy=extend_schema(description='Delete supplier (soft delete)'),
)
class SupplierViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing suppliers.
    Auto-filtered by company via TenantQuerySetMixin.

    list: Get all suppliers with search and filters
    retrieve: Get supplier details with statistics
    create: Create new supplier
    update: Update supplier information
    destroy: Soft delete supplier
    purchase_orders: Get all purchase orders for a supplier
    stats: Get supplier statistics
    """
    queryset = Supplier.active.all()
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return SupplierListSerializer
        elif self.action == 'create':
            return CreateSupplierSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateSupplierSerializer
        return SupplierDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(contact_name__icontains=search) |
                Q(email__icontains=search)
            )

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by city
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)

        return queryset.order_by('name')

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated, HasPermission('suppliers:create')]
        elif self.action in ['update', 'partial_update']:
            self.permission_classes = [IsAuthenticated, HasPermission('suppliers:edit')]
        elif self.action == 'destroy':
            self.permission_classes = [IsAuthenticated, HasPermission('suppliers:delete')]
        else:
            self.permission_classes = [IsAuthenticated, HasPermission('suppliers:view')]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Set company from authenticated user."""
        serializer.save(company=self.request.user.company)

    def destroy(self, request, *args, **kwargs):
        """Soft delete a supplier."""
        supplier = self.get_object()
        supplier.soft_delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def purchase_orders(self, request, pk=None):
        """Get all purchase orders for this supplier."""
        supplier = self.get_object()
        orders = supplier.purchase_orders.all().order_by('-created_at')

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)

        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = PurchaseOrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PurchaseOrderListSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get supplier statistics."""
        supplier = self.get_object()
        orders = supplier.purchase_orders.all()

        stats = {
            'total_orders': orders.count(),
            'total_amount': orders.aggregate(total=Sum('total'))['total'] or 0,
            'pending_orders': orders.filter(status__in=['draft', 'pending', 'approved', 'ordered']).count(),
            'ordered_count': orders.filter(status='ordered').count(),
            'partial_count': orders.filter(status='partial').count(),
            'received_orders': orders.filter(status='received').count(),
            'cancelled_orders': orders.filter(status='cancelled').count(),
        }
        return Response(stats)


@extend_schema_view(
    list=extend_schema(description='List all purchase orders'),
    retrieve=extend_schema(description='Get purchase order details'),
    create=extend_schema(description='Create new purchase order'),
    update=extend_schema(description='Update purchase order'),
)
class PurchaseOrderViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing purchase orders.
    Auto-filtered by company via TenantQuerySetMixin (through branch).

    list: Get all purchase orders (filtered by company/branch)
    retrieve: Get purchase order details with items
    create: Create new purchase order with items
    update: Update purchase order
    approve: Approve a purchase order
    receive: Receive items and update inventory
    cancel: Cancel a purchase order
    """
    queryset = PurchaseOrder.objects.select_related(
        'supplier', 'branch', 'created_by', 'approved_by', 'received_by'
    ).prefetch_related('items', 'items__product')
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    tenant_field = 'branch__company'  # Filter through branch's company

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        elif self.action == 'create':
            return CreatePurchaseOrderSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdatePurchaseOrderSerializer
        return PurchaseOrderDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Branch filtering based on user permissions
        if not user.is_superuser:
            if user.allowed_branches.exists():
                queryset = queryset.filter(branch__in=user.allowed_branches.all())
            elif user.default_branch:
                queryset = queryset.filter(branch=user.default_branch)

        # Query parameter filters
        supplier_id = self.request.query_params.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        branch_id = self.request.query_params.get('branch')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Date filters
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(order_date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(order_date__lte=date_to)

        return queryset.order_by('-created_at')

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated, HasPermission('purchase_orders:create')]
        elif self.action in ['update', 'partial_update']:
            self.permission_classes = [IsAuthenticated, HasPermission('purchase_orders:edit')]
        elif self.action == 'approve':
            self.permission_classes = [IsAuthenticated, HasPermission('purchase_orders:approve')]
        elif self.action == 'receive':
            self.permission_classes = [IsAuthenticated, HasPermission('purchase_orders:receive')]
        elif self.action == 'cancel':
            self.permission_classes = [IsAuthenticated, HasPermission('purchase_orders:cancel')]
        else:
            self.permission_classes = [IsAuthenticated, HasPermission('purchase_orders:view')]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Set created_by to current user."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a purchase order."""
        order = self.get_object()

        if order.status != 'pending':
            return Response(
                {'error': 'Solo se pueden aprobar órdenes en estado pendiente'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'approved'
        order.approved_by = request.user
        order.save()

        return Response(PurchaseOrderDetailSerializer(order).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def receive(self, request, pk=None):
        """Mark order as received and update inventory."""
        order = self.get_object()

        if order.status not in ['ordered', 'partial']:
            return Response(
                {'error': 'Solo se pueden recibir órdenes en estado ordenada o parcialmente recibida'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get items to receive from request
        items_to_receive = request.data.get('items', [])

        if not items_to_receive:
            return Response(
                {'error': 'Debe especificar los items a recibir'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate and receive items
        serializer = ReceiveItemSerializer(data=items_to_receive, many=True)
        serializer.is_valid(raise_exception=True)

        from apps.inventory.models import BranchStock

        for item_data in serializer.validated_data:
            # Lock the item row to prevent race conditions
            item = PurchaseOrderItem.objects.select_for_update().get(
                id=item_data['item_id'],
                purchase_order=order
            )

            quantity = item_data['quantity_received']

            # Validate quantity
            if item.quantity_received + quantity > item.quantity_ordered:
                return Response(
                    {'error': f'No se puede recibir más de lo ordenado para {item.product.name}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Atomic update of item quantity using F() expression
            PurchaseOrderItem.objects.filter(id=item.id).update(
                quantity_received=F('quantity_received') + quantity
            )

            # Update inventory stock with lock
            branch_stock, created = BranchStock.objects.select_for_update().get_or_create(
                product=item.product,
                branch_id=order.branch_id,
                defaults={'quantity': 0}
            )
            # Atomic update using F() expression
            BranchStock.objects.filter(id=branch_stock.id).update(
                quantity=F('quantity') + quantity
            )

        # Check if order is fully received - refresh items from DB
        order.refresh_from_db()
        all_items = order.items.all()
        if all(item.is_fully_received for item in all_items):
            order.status = 'received'
            order.received_date = timezone.now().date()
            order.received_by = request.user
        else:
            order.status = 'partial'

        order.save()

        return Response(PurchaseOrderDetailSerializer(order).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a purchase order."""
        order = self.get_object()

        if order.status == 'received':
            return Response(
                {'error': 'No se pueden cancelar órdenes ya recibidas'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status == 'cancelled':
            return Response(
                {'error': 'Esta orden ya está cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'cancelled'
        order.save()

        return Response(PurchaseOrderDetailSerializer(order).data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get purchase orders summary statistics."""
        queryset = self.get_queryset()

        summary = {
            'total_orders': queryset.count(),
            'total_amount': queryset.aggregate(total=Sum('total'))['total'] or 0,
            'by_status': {
                'draft': queryset.filter(status='draft').count(),
                'pending': queryset.filter(status='pending').count(),
                'approved': queryset.filter(status='approved').count(),
                'ordered': queryset.filter(status='ordered').count(),
                'partial': queryset.filter(status='partial').count(),
                'received': queryset.filter(status='received').count(),
                'cancelled': queryset.filter(status='cancelled').count(),
            }
        }

        return Response(summary)
