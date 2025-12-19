"""
API Views for Sales module.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone

from apps.users.permissions import HasPermission
from apps.alerts.activity_mixin import ActivityLogMixin
from core.mixins import TenantQuerySetMixin
from .pdf_service import ReceiptPDFService
from apps.branches.models import Branch
from .models import Sale, DailyCashRegister
from .serializers import (
    SaleSerializer,
    CreateSaleSerializer,
    VoidSaleSerializer,
    RefundSaleSerializer,
    DailyCashRegisterSerializer,
    OpenRegisterSerializer,
    CloseRegisterSerializer,
    DailySummarySerializer,
    TopProductSerializer,
)
from .services import SaleService, CashRegisterService


class SaleViewSet(ActivityLogMixin, TenantQuerySetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing sales.
    Auto-filtered by company via TenantQuerySetMixin (through branch).

    list: Get all sales (filtered by company/branch)
    retrieve: Get sale details
    create: Create a new sale
    void: Void an existing sale
    refund: Create a partial refund
    daily_summary: Get sales summary for a day
    top_products: Get top selling products
    """
    queryset = Sale.objects.select_related(
        'branch',
        'cashier',
        'voided_by'
    ).prefetch_related('items')
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    tenant_field = 'branch__company'  # Filter through branch's company
    activity_model_name = 'Venta'
    activity_name_field = 'receipt_number'

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filter by branch if not admin
        if user.role and user.role.role_type != 'admin':
            if user.allowed_branches.exists():
                queryset = queryset.filter(branch_id__in=user.allowed_branches.all())
            elif user.default_branch:
                queryset = queryset.filter(branch_id=user.default_branch)

        # Apply filters
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        cashier_id = self.request.query_params.get('cashier')
        if cashier_id:
            queryset = queryset.filter(cashier_id=cashier_id)

        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        return queryset.order_by('-created_at')

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated, HasPermission('sales:create')]
        elif self.action == 'void':
            self.permission_classes = [IsAuthenticated, HasPermission('sales:void')]
        elif self.action == 'refund':
            self.permission_classes = [IsAuthenticated, HasPermission('sales:refund')]
        elif self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated, HasPermission('sales:view')]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Create a new sale."""
        serializer = CreateSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get branch from request or user's default
        branch_id = request.data.get('branch_id') or request.user.default_branch
        if not branch_id:
            return Response(
                {'error': 'No se especificó una sucursal'},
                status=status.HTTP_400_BAD_REQUEST
            )

        branch = get_object_or_404(Branch, id=branch_id, is_active=True)

        # Validar que el usuario tiene acceso a esta sucursal
        if not request.user.is_superuser:
            if not request.user.can_access_branch(branch.id):
                return Response(
                    {'error': 'No tienes acceso a esta sucursal'},
                    status=status.HTTP_403_FORBIDDEN
                )

        try:
            sale = SaleService.create_sale(
                branch=branch,
                cashier=request.user,
                items=serializer.validated_data['items'],
                payment_method=serializer.validated_data['payment_method'],
                amount_tendered=serializer.validated_data.get('amount_tendered', 0),
                discount_percent=serializer.validated_data.get('discount_percent', 0),
                discount_amount=serializer.validated_data.get('discount_amount', 0),
                customer_name=serializer.validated_data.get('customer_name', ''),
                customer_phone=serializer.validated_data.get('customer_phone', ''),
                customer_email=serializer.validated_data.get('customer_email', ''),
                payment_reference=serializer.validated_data.get('payment_reference', ''),
                notes=serializer.validated_data.get('notes', '')
            )
            return Response(
                SaleSerializer(sale).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        """Void an existing sale."""
        sale = self.get_object()
        serializer = VoidSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            sale = SaleService.void_sale(
                sale=sale,
                user=request.user,
                reason=serializer.validated_data['reason']
            )
            return Response(SaleSerializer(sale).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Create a partial refund."""
        sale = self.get_object()
        serializer = RefundSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refund = SaleService.refund_items(
                sale=sale,
                items_to_refund=serializer.validated_data['items'],
                user=request.user,
                reason=serializer.validated_data['reason']
            )
            return Response(
                SaleSerializer(refund).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get sales summary for a specific day."""
        branch_id = request.query_params.get('branch') or request.user.default_branch
        if not branch_id:
            return Response(
                {'error': 'No se especificó una sucursal'},
                status=status.HTTP_400_BAD_REQUEST
            )

        branch = get_object_or_404(Branch, id=branch_id)

        date_str = request.query_params.get('date')
        date = None
        if date_str:
            try:
                from datetime import datetime
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        summary = SaleService.get_daily_summary(branch, date)
        serializer = DailySummarySerializer(summary)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def top_products(self, request):
        """Get top selling products."""
        branch_id = request.query_params.get('branch') or request.user.default_branch
        if not branch_id:
            return Response(
                {'error': 'No se especificó una sucursal'},
                status=status.HTTP_400_BAD_REQUEST
            )

        branch = get_object_or_404(Branch, id=branch_id)

        limit = int(request.query_params.get('limit', 10))
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        products = SaleService.get_top_products(
            branch=branch,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        serializer = TopProductSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        """Get receipt data for printing."""
        sale = self.get_object()
        # Return data formatted for receipt printing
        receipt_data = {
            'sale_number': sale.sale_number,
            'date': sale.created_at.strftime('%Y-%m-%d %H:%M'),
            'branch': {
                'name': sale.branch.name,
                'address': sale.branch.full_address,
                'phone': sale.branch.phone,
            },
            'cashier': sale.cashier.full_name,
            'items': [
                {
                    'name': item.product_name,
                    'sku': item.product_sku,
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'discount': str(item.discount_amount),
                    'subtotal': str(item.subtotal),
                }
                for item in sale.items.all()
            ],
            'subtotal': str(sale.subtotal),
            'discount': str(sale.discount_amount),
            'tax': str(sale.tax_amount),
            'total': str(sale.total),
            'payment_method': sale.get_payment_method_display(),
            'amount_tendered': str(sale.amount_tendered),
            'change': str(sale.change_amount),
            'customer_name': sale.customer_name,
        }
        return Response(receipt_data)

    @action(detail=True, methods=['get'])
    def receipt_pdf(self, request, pk=None):
        """Generate and download receipt as PDF."""
        sale = self.get_object()

        # Generate PDF
        pdf_buffer = ReceiptPDFService.generate_receipt(sale)

        # Build response
        response = HttpResponse(
            pdf_buffer.getvalue(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="recibo_{sale.sale_number}.pdf"'
        )

        return response


class CashRegisterViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing daily cash registers.
    Auto-filtered by company via TenantQuerySetMixin (through branch).

    list: Get all registers (filtered by company/branch)
    retrieve: Get register details
    open: Open a new register
    close: Close an open register
    current: Get current open register
    """
    queryset = DailyCashRegister.objects.select_related(
        'branch',
        'opened_by',
        'closed_by'
    )
    serializer_class = DailyCashRegisterSerializer
    permission_classes = [IsAuthenticated]
    tenant_field = 'branch__company'  # Filter through branch's company

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['open', 'close', 'current']:
            # Users who can create sales can open/close registers
            self.permission_classes = [IsAuthenticated, HasPermission('sales:create')]
        elif self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated, HasPermission('sales:view')]
        else:
            # For other actions (update, delete), require register permission
            self.permission_classes = [IsAuthenticated, HasPermission('sales:register')]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filter by branch
        if user.role and user.role.role_type != 'admin':
            if user.allowed_branches.exists():
                queryset = queryset.filter(branch_id__in=user.allowed_branches.all())
            elif user.default_branch:
                queryset = queryset.filter(branch_id=user.default_branch)

        branch_id = self.request.query_params.get('branch')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        return queryset.order_by('-date')

    @action(detail=False, methods=['post'])
    def open(self, request):
        """Open a new cash register for today."""
        serializer = OpenRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        branch_id = request.data.get('branch_id') or request.user.default_branch
        if not branch_id:
            return Response(
                {'error': 'No se especificó una sucursal'},
                status=status.HTTP_400_BAD_REQUEST
            )

        branch = get_object_or_404(Branch, id=branch_id, is_active=True)

        # Validar que el usuario tiene acceso a esta sucursal
        if not request.user.is_superuser:
            if not request.user.can_access_branch(branch.id):
                return Response(
                    {'error': 'No tienes acceso a esta sucursal'},
                    status=status.HTTP_403_FORBIDDEN
                )

        try:
            register = CashRegisterService.open_register(
                branch=branch,
                user=request.user,
                opening_amount=serializer.validated_data['opening_amount']
            )
            return Response(
                DailyCashRegisterSerializer(register).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close an open cash register."""
        register = self.get_object()
        serializer = CloseRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            register = CashRegisterService.close_register(
                register=register,
                user=request.user,
                closing_amount=serializer.validated_data['closing_amount'],
                notes=serializer.validated_data.get('notes', '')
            )
            return Response(DailyCashRegisterSerializer(register).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the current open register for a branch."""
        branch_id = request.query_params.get('branch') or request.user.default_branch
        if not branch_id:
            return Response(
                {'error': 'No se especificó una sucursal'},
                status=status.HTTP_400_BAD_REQUEST
            )

        branch = get_object_or_404(Branch, id=branch_id)
        register = CashRegisterService.get_current_register(branch)

        if register:
            return Response(DailyCashRegisterSerializer(register).data)
        return Response(
            {'message': 'No hay caja abierta para esta sucursal'},
            status=status.HTTP_404_NOT_FOUND
        )
