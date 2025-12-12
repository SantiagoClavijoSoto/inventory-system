from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q

from apps.users.permissions import HasPermission, CanAccessBranch
from core.mixins import TenantQuerySetMixin
from .models import Category, Product, BranchStock, StockMovement, StockAlert
from .serializers import (
    CategorySerializer,
    CategoryTreeSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    BranchStockSerializer,
    StockMovementSerializer,
    StockAdjustmentSerializer,
    StockTransferSerializer,
    StockAlertSerializer,
    ActiveAlertSerializer,
)
from .services import StockService
from .filters import ProductFilter, StockMovementFilter


class CategoryViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """
    ViewSet for product categories.
    Supports hierarchical category management.
    Auto-filtered by company via TenantQuerySetMixin.
    """
    queryset = Category.active.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), HasPermission('inventory:manage')]
        return [IsAuthenticated(), HasPermission('inventory:view')]

    def get_serializer_class(self):
        if self.action == 'tree':
            return CategoryTreeSerializer
        return CategorySerializer

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get categories as flat list for dropdowns"""
        categories = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def root(self, request):
        """Get only root categories (no parent)"""
        categories = self.get_queryset().filter(parent__isnull=True, is_active=True)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.save()


class ProductViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """
    ViewSet for products with barcode search and stock management.
    Auto-filtered by company via TenantQuerySetMixin.
    """
    queryset = Product.active.select_related(
        'category', 'supplier'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'sku', 'barcode', 'description']
    ordering_fields = ['name', 'sku', 'sale_price', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), HasPermission('inventory:manage')]
        return [IsAuthenticated(), HasPermission('inventory:view')]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.save()

    @action(detail=False, methods=['get'], url_path='barcode/(?P<code>[^/.]+)')
    def by_barcode(self, request, code=None):
        """
        Search product by barcode or SKU.
        Returns product with stock info for the current branch.
        """
        branch_id = request.query_params.get('branch_id')
        if not branch_id:
            return Response(
                {'error': 'branch_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.active.filter(is_active=True).get(
                Q(barcode=code) | Q(sku=code)
            )
        except Product.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get stock for the specific branch
        stock_in_branch = product.get_stock_for_branch(int(branch_id))
        try:
            branch_stock = BranchStock.objects.get(
                product=product,
                branch_id=branch_id
            )
            available = branch_stock.available_quantity
        except BranchStock.DoesNotExist:
            available = 0

        serializer = ProductDetailSerializer(product)
        return Response({
            'product': serializer.data,
            'stock_in_branch': stock_in_branch,
            'available_in_branch': available
        })

    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        """Get stock levels across all branches for a product"""
        product = self.get_object()
        stocks = BranchStock.objects.filter(product=product).select_related('branch')
        serializer = BranchStockSerializer(stocks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def movements(self, request, pk=None):
        """Get stock movement history for a product"""
        product = self.get_object()
        branch_id = request.query_params.get('branch_id')

        movements = StockMovement.objects.filter(product=product)
        if branch_id:
            movements = movements.filter(branch_id=branch_id)

        movements = movements.select_related(
            'branch', 'related_branch', 'created_by'
        ).order_by('-created_at')[:100]

        serializer = StockMovementSerializer(movements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock"""
        branch_id = request.query_params.get('branch_id')

        # Filter through active products by joining with is_active filter
        query = BranchStock.objects.select_related('product', 'branch').filter(
            product__is_active=True,
            product__is_deleted=False  # Keep explicit for join query
        )

        if branch_id:
            query = query.filter(branch_id=branch_id)

        # Filter products below minimum stock
        low_stock_items = []
        for stock in query:
            if stock.is_low_stock:
                low_stock_items.append({
                    'product_id': stock.product.id,
                    'product_name': stock.product.name,
                    'product_sku': stock.product.sku,
                    'branch_id': stock.branch.id,
                    'branch_name': stock.branch.name,
                    'current_quantity': stock.quantity,
                    'min_stock': stock.product.min_stock,
                    'is_out_of_stock': stock.is_out_of_stock
                })

        return Response(low_stock_items)

    @action(detail=False, methods=['get'])
    def search_pos(self, request):
        """
        Search products for POS with stock info.
        Returns products with branch-specific stock levels.
        Only returns products belonging to the same company as the branch.
        """
        from apps.branches.models import Branch

        branch_id = request.query_params.get('branch')
        search = request.query_params.get('search', '').strip()

        if not branch_id:
            return Response(
                {'error': 'branch es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not search:
            return Response([])

        # Get the branch to filter products by its company
        try:
            branch = Branch.objects.get(id=branch_id, is_active=True)
        except Branch.DoesNotExist:
            return Response(
                {'error': 'Sucursal no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Search by name, SKU, or barcode - filtered by branch's company
        products = self.get_queryset().filter(
            is_active=True
        ).filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(barcode__icontains=search)
        )

        # Filter by branch's company if the branch has one
        if branch.company_id:
            products = products.filter(company_id=branch.company_id)

        products = products[:20]

        # Build response with stock info for each product
        result = []
        for product in products:
            try:
                branch_stock = BranchStock.objects.get(
                    product=product,
                    branch_id=branch_id
                )
                stock_quantity = branch_stock.quantity
                available_quantity = branch_stock.available_quantity
            except BranchStock.DoesNotExist:
                stock_quantity = 0
                available_quantity = 0

            serializer = ProductDetailSerializer(product)
            result.append({
                **serializer.data,
                'stock_in_branch': stock_quantity,
                'available_in_branch': available_quantity,
            })

        return Response(result)


class StockViewSet(viewsets.ViewSet):
    """
    ViewSet for stock operations: adjustments, transfers.
    """
    permission_classes = [IsAuthenticated, HasPermission('inventory:manage')]

    @action(detail=False, methods=['post'])
    def adjust(self, request):
        """Manual stock adjustment"""
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            product = Product.active.get(id=data['product_id'])
        except Product.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        movement = StockService.manual_adjustment(
            product=product,
            branch_id=data['branch_id'],
            adjustment_type=data['adjustment_type'],
            quantity=data['quantity'],
            user=request.user,
            reason=data['reason'],
            notes=data.get('notes', '')
        )

        return Response(
            StockMovementSerializer(movement).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'])
    def transfer(self, request):
        """Transfer stock between branches"""
        serializer = StockTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            product = Product.active.get(id=data['product_id'])
        except Product.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        out_movement, in_movement = StockService.transfer_stock(
            product=product,
            from_branch_id=data['from_branch_id'],
            to_branch_id=data['to_branch_id'],
            quantity=data['quantity'],
            user=request.user,
            notes=data.get('notes', '')
        )

        return Response({
            'outgoing': StockMovementSerializer(out_movement).data,
            'incoming': StockMovementSerializer(in_movement).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def by_branch(self, request):
        """Get all stock for a specific branch"""
        branch_id = request.query_params.get('branch_id')
        if not branch_id:
            return Response(
                {'error': 'branch_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stocks = BranchStock.objects.filter(
            branch_id=branch_id,
            product__is_active=True,
            product__is_deleted=False  # Keep explicit for join query
        ).select_related('product', 'product__category')

        serializer = BranchStockSerializer(stocks, many=True)
        return Response(serializer.data)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing stock movement history.
    Read-only - movements are created through stock operations.
    """
    queryset = StockMovement.objects.select_related(
        'product', 'branch', 'related_branch', 'created_by'
    ).order_by('-created_at')
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, HasPermission('inventory:view')]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = StockMovementFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class StockAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for stock alert configuration.
    """
    queryset = StockAlert.objects.select_related('product', 'category', 'branch')
    serializer_class = StockAlertSerializer
    permission_classes = [IsAuthenticated, HasPermission('alerts:manage')]

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all currently active alerts (products below threshold)"""
        branch_id = request.query_params.get('branch_id')

        active_alerts = []
        stocks = BranchStock.objects.select_related(
            'product', 'branch'
        ).filter(
            product__is_active=True,
            product__is_deleted=False  # Keep explicit for join query
        )

        if branch_id:
            stocks = stocks.filter(branch_id=branch_id)

        for stock in stocks:
            if stock.is_out_of_stock:
                active_alerts.append({
                    'product_id': stock.product.id,
                    'product_name': stock.product.name,
                    'product_sku': stock.product.sku,
                    'branch_id': stock.branch.id,
                    'branch_name': stock.branch.name,
                    'alert_type': 'out_of_stock',
                    'current_quantity': stock.quantity,
                    'threshold': 0
                })
            elif stock.is_low_stock:
                active_alerts.append({
                    'product_id': stock.product.id,
                    'product_name': stock.product.name,
                    'product_sku': stock.product.sku,
                    'branch_id': stock.branch.id,
                    'branch_name': stock.branch.name,
                    'alert_type': 'low_stock',
                    'current_quantity': stock.quantity,
                    'threshold': stock.product.min_stock
                })

        return Response(active_alerts)
