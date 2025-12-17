"""
Report views - API endpoints for business reports.

All report endpoints require authentication and filter data by the user's company
to ensure proper multi-tenant data isolation.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.users.permissions import HasPermission
from .services import (
    DashboardService,
    SalesReportService,
    InventoryReportService,
    EmployeeReportService,
    BranchReportService
)
from .serializers import (
    DateRangeSerializer,
    SalesPeriodSerializer,
    TopProductsSerializer,
    PeriodComparisonSerializer,
    HourlySalesSerializer,
    ProductMovementSerializer,
    LowStockSerializer,
    TodaySummaryResponseSerializer,
    PeriodComparisonResponseSerializer,
    LowStockCountResponseSerializer,
    TopProductResponseSerializer,
    SalesByPeriodResponseSerializer,
    StockSummaryResponseSerializer
)


class TenantReportMixin:
    """
    Mixin that provides company_id extraction for multi-tenant reports.
    """

    def get_company_id(self):
        """Get the company_id from the authenticated user."""
        return getattr(self.request.user, 'company_id', None)


class DashboardViewSet(TenantReportMixin, viewsets.ViewSet):
    """
    Dashboard KPIs and quick metrics endpoints.

    Permission logic:
    - reports:view: Full access to all dashboard metrics
    - inventory:view: Access to inventory-related metrics (stock summary, low stock count)
    - Any authenticated user: Access to basic dashboard metrics
    """
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        """Allow dashboard access for authenticated users with relevant permissions."""
        super().check_permissions(request)

        user = request.user
        if user.is_superuser:
            return

        # Check for any relevant permission
        has_reports = user.has_permission('reports:view') if hasattr(user, 'has_permission') else False
        has_inventory = user.has_permission('inventory:view') if hasattr(user, 'has_permission') else False
        has_sales = user.has_permission('sales:view') if hasattr(user, 'has_permission') else False

        # Allow if user has any of these permissions
        if has_reports or has_inventory or has_sales:
            return

        # Allow basic dashboard access for all authenticated users
        # (they can at least see their own metrics)
        return

    @extend_schema(
        summary="Get today's sales summary",
        description="Returns key metrics for today including total sales, transactions, and average ticket.",
        parameters=[
            OpenApiParameter(
                name='branch_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter by branch ID'
            )
        ],
        responses={200: TodaySummaryResponseSerializer}
    )
    @action(detail=False, methods=['get'], url_path='today')
    def today_summary(self, request):
        """Get today's sales summary."""
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            branch_id = int(branch_id)

        data = DashboardService.get_today_summary(
            company_id=self.get_company_id(),
            branch_id=branch_id
        )
        return Response(data)

    @extend_schema(
        summary="Compare current period with previous",
        description="Compares sales between current period and same previous period.",
        parameters=[
            OpenApiParameter('days', OpenApiTypes.INT, OpenApiParameter.QUERY, description='Number of days to compare (default: 7)'),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ],
        responses={200: PeriodComparisonResponseSerializer}
    )
    @action(detail=False, methods=['get'], url_path='comparison')
    def period_comparison(self, request):
        """Compare current period with previous period."""
        serializer = PeriodComparisonSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = DashboardService.get_period_comparison(
            company_id=self.get_company_id(),
            branch_id=serializer.validated_data.get('branch_id'),
            days=serializer.validated_data['days']
        )
        return Response(data)

    @extend_schema(
        summary="Get low stock alerts count",
        description="Returns count of products with low stock and out of stock.",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ],
        responses={200: LowStockCountResponseSerializer}
    )
    @action(detail=False, methods=['get'], url_path='low-stock-count')
    def low_stock_count(self, request):
        """Get count of low stock products."""
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            branch_id = int(branch_id)

        data = DashboardService.get_low_stock_count(
            company_id=self.get_company_id(),
            branch_id=branch_id
        )
        return Response(data)

    @extend_schema(
        summary="Get top selling products",
        description="Returns top N products by quantity sold.",
        parameters=[
            OpenApiParameter('days', OpenApiTypes.INT, OpenApiParameter.QUERY, description='Period in days (default: 30)'),
            OpenApiParameter('limit', OpenApiTypes.INT, OpenApiParameter.QUERY, description='Number of products (default: 10)'),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ],
        responses={200: TopProductResponseSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='top-products')
    def top_products(self, request):
        """Get top selling products."""
        serializer = TopProductsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = DashboardService.get_top_products(
            company_id=self.get_company_id(),
            branch_id=serializer.validated_data.get('branch_id'),
            days=serializer.validated_data['days'],
            limit=serializer.validated_data['limit']
        )
        return Response(data)


class SalesReportViewSet(TenantReportMixin, viewsets.ViewSet):
    """
    Sales report endpoints.
    """
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'reports:view'

    @extend_schema(
        summary="Get sales by time period",
        description="Returns sales aggregated by day, week, or month.",
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('group_by', OpenApiTypes.STR, OpenApiParameter.QUERY, description='day, week, or month'),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ],
        responses={200: SalesByPeriodResponseSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='by-period')
    def by_period(self, request):
        """Get sales grouped by time period."""
        serializer = SalesPeriodSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = SalesReportService.get_sales_by_period(
            company_id=self.get_company_id(),
            date_from=serializer.validated_data['date_from'],
            date_to=serializer.validated_data['date_to'],
            branch_id=serializer.validated_data.get('branch_id'),
            group_by=serializer.validated_data['group_by']
        )
        return Response(data)

    @extend_schema(
        summary="Get sales by payment method",
        description="Returns sales breakdown by payment method.",
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-payment-method')
    def by_payment_method(self, request):
        """Get sales by payment method."""
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = SalesReportService.get_sales_by_payment_method(
            company_id=self.get_company_id(),
            date_from=serializer.validated_data['date_from'],
            date_to=serializer.validated_data['date_to'],
            branch_id=serializer.validated_data.get('branch_id')
        )
        return Response(data)

    @extend_schema(
        summary="Get sales by cashier",
        description="Returns sales performance by cashier.",
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-cashier')
    def by_cashier(self, request):
        """Get sales by cashier."""
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = SalesReportService.get_sales_by_cashier(
            company_id=self.get_company_id(),
            date_from=serializer.validated_data['date_from'],
            date_to=serializer.validated_data['date_to'],
            branch_id=serializer.validated_data.get('branch_id')
        )
        return Response(data)

    @extend_schema(
        summary="Get sales by category",
        description="Returns sales breakdown by product category.",
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-category')
    def by_category(self, request):
        """Get sales by category."""
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = SalesReportService.get_sales_by_category(
            company_id=self.get_company_id(),
            date_from=serializer.validated_data['date_from'],
            date_to=serializer.validated_data['date_to'],
            branch_id=serializer.validated_data.get('branch_id')
        )
        return Response(data)

    @extend_schema(
        summary="Get hourly sales distribution",
        description="Returns sales distribution by hour for a specific date.",
        parameters=[
            OpenApiParameter('target_date', OpenApiTypes.DATE, OpenApiParameter.QUERY, description='Date to analyze (default: today)'),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ]
    )
    @action(detail=False, methods=['get'], url_path='hourly')
    def hourly(self, request):
        """Get hourly sales distribution."""
        serializer = HourlySalesSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = SalesReportService.get_hourly_sales(
            company_id=self.get_company_id(),
            target_date=serializer.validated_data['target_date'],
            branch_id=serializer.validated_data.get('branch_id')
        )
        return Response(data)

    @extend_schema(
        summary="Get top selling products",
        description="Returns top selling products by quantity within date range.",
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('limit', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Number of products (default: 10)')
        ]
    )
    @action(detail=False, methods=['get'], url_path='top-products')
    def top_products(self, request):
        """Get top selling products within date range."""
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        limit = int(request.query_params.get('limit', 10))

        data = SalesReportService.get_top_products(
            company_id=self.get_company_id(),
            date_from=serializer.validated_data['date_from'],
            date_to=serializer.validated_data['date_to'],
            branch_id=serializer.validated_data.get('branch_id'),
            limit=limit
        )
        return Response(data)


class InventoryReportViewSet(TenantReportMixin, viewsets.ViewSet):
    """
    Inventory report endpoints.

    Permission logic:
    - reports:view: Full access to all inventory reports
    - inventory:view: Access to inventory-related reports (stock summary, low stock, etc.)
    """
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        """Allow inventory report access for users with inventory or reports permission."""
        super().check_permissions(request)

        user = request.user
        if user.is_superuser:
            return

        # Check for relevant permissions
        has_reports = user.has_permission('reports:view') if hasattr(user, 'has_permission') else False
        has_inventory = user.has_permission('inventory:view') if hasattr(user, 'has_permission') else False

        if has_reports or has_inventory:
            return

        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("No tiene permiso para ver reportes de inventario.")

    @extend_schema(
        summary="Get stock summary",
        description="Returns overall stock statistics including value and alerts.",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ],
        responses={200: StockSummaryResponseSerializer}
    )
    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Get stock summary."""
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            branch_id = int(branch_id)

        data = InventoryReportService.get_stock_summary(
            company_id=self.get_company_id(),
            branch_id=branch_id
        )
        return Response(data)

    @extend_schema(
        summary="Get stock by category",
        description="Returns stock breakdown by product category.",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-category')
    def by_category(self, request):
        """Get stock by category."""
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            branch_id = int(branch_id)

        data = InventoryReportService.get_stock_by_category(
            company_id=self.get_company_id(),
            branch_id=branch_id
        )
        return Response(data)

    @extend_schema(
        summary="Get low stock products",
        description="Returns list of products with low or no stock.",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('limit', OpenApiTypes.INT, OpenApiParameter.QUERY, description='Max results (default: 50)')
        ]
    )
    @action(detail=False, methods=['get'], url_path='low-stock')
    def low_stock(self, request):
        """Get low stock products."""
        serializer = LowStockSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = InventoryReportService.get_low_stock_products(
            company_id=self.get_company_id(),
            branch_id=serializer.validated_data.get('branch_id'),
            limit=serializer.validated_data['limit']
        )
        return Response(data)

    @extend_schema(
        summary="Get stock movements summary",
        description="Returns stock movements aggregated by type.",
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ]
    )
    @action(detail=False, methods=['get'], url_path='movements-summary')
    def movements_summary(self, request):
        """Get stock movements summary."""
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = InventoryReportService.get_stock_movements_summary(
            company_id=self.get_company_id(),
            date_from=serializer.validated_data['date_from'],
            date_to=serializer.validated_data['date_to'],
            branch_id=serializer.validated_data.get('branch_id')
        )
        return Response(data)

    @extend_schema(
        summary="Get sales for a specific date",
        description="Returns list of individual sales for a specific date.",
        parameters=[
            OpenApiParameter('target_date', OpenApiTypes.DATE, OpenApiParameter.QUERY, required=True),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ]
    )
    @action(detail=False, methods=['get'], url_path='sales-by-date')
    def sales_by_date(self, request):
        """Get individual sales for a specific date."""
        from datetime import datetime

        target_date_str = request.query_params.get('target_date')
        if not target_date_str:
            return Response({'error': 'target_date is required'}, status=400)

        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        branch_id = request.query_params.get('branch_id')
        if branch_id:
            branch_id = int(branch_id)

        data = InventoryReportService.get_sales_by_date(
            company_id=self.get_company_id(),
            target_date=target_date,
            branch_id=branch_id
        )
        return Response(data)

    @extend_schema(
        summary="Get all sales within date range",
        description="Returns list of all individual sales within a date range (for month filtering).",
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY, required=True),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY, required=True),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ]
    )
    @action(detail=False, methods=['get'], url_path='all-sales')
    def all_sales(self, request):
        """Get all sales within a date range."""
        from datetime import datetime

        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        if not date_from_str or not date_to_str:
            return Response({'error': 'date_from and date_to are required'}, status=400)

        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        branch_id = request.query_params.get('branch_id')
        if branch_id:
            branch_id = int(branch_id)

        data = InventoryReportService.get_all_sales(
            company_id=self.get_company_id(),
            date_from=date_from,
            date_to=date_to,
            branch_id=branch_id
        )
        return Response(data)

    @extend_schema(
        summary="Get product movement history",
        description="Returns movement history for a specific product.",
        parameters=[
            OpenApiParameter('product_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=True),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('days', OpenApiTypes.INT, OpenApiParameter.QUERY, description='Period in days (default: 30)')
        ]
    )
    @action(detail=False, methods=['get'], url_path='product-history')
    def product_history(self, request):
        """Get product movement history."""
        serializer = ProductMovementSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = InventoryReportService.get_product_movement_history(
            company_id=self.get_company_id(),
            product_id=serializer.validated_data['product_id'],
            branch_id=serializer.validated_data.get('branch_id'),
            days=serializer.validated_data['days']
        )
        return Response(data)


class EmployeeReportViewSet(TenantReportMixin, viewsets.ViewSet):
    """
    Employee report endpoints.
    """
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'reports:view'

    @extend_schema(
        summary="Get employee performance",
        description="Returns employee performance metrics including sales and hours worked.",
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ]
    )
    @action(detail=False, methods=['get'], url_path='performance')
    def performance(self, request):
        """Get employee performance report."""
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = EmployeeReportService.get_employee_performance(
            company_id=self.get_company_id(),
            date_from=serializer.validated_data['date_from'],
            date_to=serializer.validated_data['date_to'],
            branch_id=serializer.validated_data.get('branch_id')
        )
        return Response(data)

    @extend_schema(
        summary="Get shift summary",
        description="Returns shift statistics and distribution by weekday.",
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False)
        ]
    )
    @action(detail=False, methods=['get'], url_path='shifts')
    def shifts(self, request):
        """Get shift summary."""
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = EmployeeReportService.get_shift_summary(
            company_id=self.get_company_id(),
            date_from=serializer.validated_data['date_from'],
            date_to=serializer.validated_data['date_to'],
            branch_id=serializer.validated_data.get('branch_id')
        )
        return Response(data)


class BranchReportViewSet(TenantReportMixin, viewsets.ViewSet):
    """
    Branch comparison report endpoints.
    """
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'reports:view'

    @extend_schema(
        summary="Compare branches",
        description="Returns performance comparison across all branches.",
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY)
        ]
    )
    @action(detail=False, methods=['get'], url_path='comparison')
    def comparison(self, request):
        """Compare all branches."""
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = BranchReportService.get_branch_comparison(
            company_id=self.get_company_id(),
            date_from=serializer.validated_data['date_from'],
            date_to=serializer.validated_data['date_to']
        )
        return Response(data)
