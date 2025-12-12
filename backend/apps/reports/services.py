"""
Report generation services.
Aggregates data from various models to generate business insights.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone

from apps.sales.models import Sale, SaleItem
from apps.inventory.models import Product, BranchStock, StockMovement, Category
from apps.employees.models import Employee, Shift
from apps.branches.models import Branch


class DashboardService:
    """
    Service for generating dashboard KPIs and quick metrics.
    """

    @staticmethod
    def get_today_summary(branch_id: Optional[int] = None) -> dict:
        """
        Get today's sales summary.
        """
        today = timezone.now().date()
        queryset = Sale.objects.filter(
            created_at__date=today,
            status='completed'
        )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        totals = queryset.aggregate(
            total_sales=Sum('total'),
            total_transactions=Count('id'),
            total_items=Sum('items__quantity'),
            total_profit=Sum(
                (F('items__unit_price') - F('items__cost_price')) * F('items__quantity')
            ),
            avg_ticket=Avg('total')
        )

        return {
            'date': today.isoformat(),
            'total_sales': totals['total_sales'] or Decimal('0.00'),
            'total_transactions': totals['total_transactions'] or 0,
            'total_items': totals['total_items'] or 0,
            'avg_ticket': totals['avg_ticket'] or Decimal('0.00'),
            'currency': 'MXN'
        }

    @staticmethod
    def get_period_comparison(
        branch_id: Optional[int] = None,
        days: int = 7
    ) -> dict:
        """
        Compare current period with previous period.
        """
        today = timezone.now().date()
        current_start = today - timedelta(days=days - 1)
        previous_start = current_start - timedelta(days=days)
        previous_end = current_start - timedelta(days=1)

        base_query = Sale.objects.filter(status='completed')
        if branch_id:
            base_query = base_query.filter(branch_id=branch_id)

        current_data = base_query.filter(
            created_at__date__gte=current_start,
            created_at__date__lte=today
        ).aggregate(
            total=Sum('total'),
            count=Count('id')
        )

        previous_data = base_query.filter(
            created_at__date__gte=previous_start,
            created_at__date__lte=previous_end
        ).aggregate(
            total=Sum('total'),
            count=Count('id')
        )

        current_total = current_data['total'] or Decimal('0')
        previous_total = previous_data['total'] or Decimal('0')

        if previous_total > 0:
            change_percent = ((current_total - previous_total) / previous_total) * 100
        else:
            change_percent = Decimal('100') if current_total > 0 else Decimal('0')

        return {
            'current_period': {
                'start': current_start.isoformat(),
                'end': today.isoformat(),
                'total': current_total,
                'transactions': current_data['count'] or 0
            },
            'previous_period': {
                'start': previous_start.isoformat(),
                'end': previous_end.isoformat(),
                'total': previous_total,
                'transactions': previous_data['count'] or 0
            },
            'change_percent': round(change_percent, 2),
            'trend': 'up' if change_percent > 0 else ('down' if change_percent < 0 else 'stable')
        }

    @staticmethod
    def get_low_stock_count(branch_id: Optional[int] = None) -> dict:
        """
        Get count of products with low stock.
        """
        queryset = BranchStock.objects.filter(
            quantity__lte=F('product__min_stock'),
            product__is_active=True,
            product__is_deleted=False
        )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        low_stock = queryset.filter(quantity__gt=0).count()
        out_of_stock = queryset.filter(quantity__lte=0).count()

        return {
            'low_stock_count': low_stock,
            'out_of_stock_count': out_of_stock,
            'total_alerts': low_stock + out_of_stock
        }

    @staticmethod
    def get_top_products(
        branch_id: Optional[int] = None,
        days: int = 30,
        limit: int = 10
    ) -> list:
        """
        Get top selling products by quantity.
        """
        start_date = timezone.now().date() - timedelta(days=days)

        queryset = SaleItem.objects.filter(
            sale__status='completed',
            sale__created_at__date__gte=start_date
        )

        if branch_id:
            queryset = queryset.filter(sale__branch_id=branch_id)

        top_products = queryset.values(
            'product_id',
            'product_name',
            'product_sku'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('subtotal'),
            total_profit=Sum(
                (F('unit_price') - F('cost_price')) * F('quantity')
            )
        ).order_by('-total_quantity')[:limit]

        return list(top_products)


class SalesReportService:
    """
    Service for generating detailed sales reports.
    """

    @staticmethod
    def get_sales_by_period(
        date_from: date,
        date_to: date,
        branch_id: Optional[int] = None,
        group_by: str = 'day'
    ) -> list:
        """
        Get sales grouped by period (day, week, month).
        """
        queryset = Sale.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
            status='completed'
        )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        # Select truncation function based on grouping
        if group_by == 'week':
            trunc_func = TruncWeek('created_at')
        elif group_by == 'month':
            trunc_func = TruncMonth('created_at')
        else:
            trunc_func = TruncDate('created_at')

        results = queryset.annotate(
            period=trunc_func
        ).values('period').annotate(
            total_sales=Sum('total'),
            total_transactions=Count('id'),
            total_items=Sum('items__quantity'),
            avg_ticket=Avg('total'),
            total_discounts=Sum('discount_amount'),
            total_tax=Sum('tax_amount')
        ).order_by('period')

        return [
            {
                'period': r['period'].isoformat() if r['period'] else None,
                'total_sales': r['total_sales'] or Decimal('0.00'),
                'total_transactions': r['total_transactions'] or 0,
                'total_items': r['total_items'] or 0,
                'avg_ticket': r['avg_ticket'] or Decimal('0.00'),
                'total_discounts': r['total_discounts'] or Decimal('0.00'),
                'total_tax': r['total_tax'] or Decimal('0.00')
            }
            for r in results
        ]

    @staticmethod
    def get_sales_by_payment_method(
        date_from: date,
        date_to: date,
        branch_id: Optional[int] = None
    ) -> list:
        """
        Get sales breakdown by payment method.
        """
        queryset = Sale.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
            status='completed'
        )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        results = queryset.values('payment_method').annotate(
            total_sales=Sum('total'),
            transaction_count=Count('id'),
            avg_ticket=Avg('total')
        ).order_by('-total_sales')

        # Add payment method display names
        payment_labels = dict(Sale.PAYMENT_METHOD_CHOICES)

        return [
            {
                'payment_method': r['payment_method'],
                'payment_method_display': payment_labels.get(r['payment_method'], r['payment_method']),
                'total_sales': r['total_sales'] or Decimal('0.00'),
                'transaction_count': r['transaction_count'] or 0,
                'avg_ticket': r['avg_ticket'] or Decimal('0.00')
            }
            for r in results
        ]

    @staticmethod
    def get_sales_by_cashier(
        date_from: date,
        date_to: date,
        branch_id: Optional[int] = None
    ) -> list:
        """
        Get sales performance by cashier.
        """
        queryset = Sale.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
            status='completed'
        )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        results = queryset.values(
            'cashier_id',
            'cashier__first_name',
            'cashier__last_name',
            'cashier__email'
        ).annotate(
            total_sales=Sum('total'),
            transaction_count=Count('id'),
            total_items=Sum('items__quantity'),
            avg_ticket=Avg('total'),
            voided_count=Count('id', filter=Q(status='voided'))
        ).order_by('-total_sales')

        return [
            {
                'cashier_id': r['cashier_id'],
                'cashier_name': f"{r['cashier__first_name']} {r['cashier__last_name']}",
                'cashier_email': r['cashier__email'],
                'total_sales': r['total_sales'] or Decimal('0.00'),
                'transaction_count': r['transaction_count'] or 0,
                'total_items': r['total_items'] or 0,
                'avg_ticket': r['avg_ticket'] or Decimal('0.00'),
                'voided_count': r['voided_count'] or 0
            }
            for r in results
        ]

    @staticmethod
    def get_sales_by_category(
        date_from: date,
        date_to: date,
        branch_id: Optional[int] = None
    ) -> list:
        """
        Get sales breakdown by product category.
        """
        queryset = SaleItem.objects.filter(
            sale__created_at__date__gte=date_from,
            sale__created_at__date__lte=date_to,
            sale__status='completed'
        )

        if branch_id:
            queryset = queryset.filter(sale__branch_id=branch_id)

        results = queryset.values(
            'product__category_id',
            'product__category__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('subtotal'),
            total_profit=Sum(
                (F('unit_price') - F('cost_price')) * F('quantity')
            ),
            unique_products=Count('product_id', distinct=True)
        ).order_by('-total_revenue')

        return [
            {
                'category_id': r['product__category_id'],
                'category_name': r['product__category__name'],
                'total_quantity': r['total_quantity'] or 0,
                'total_revenue': r['total_revenue'] or Decimal('0.00'),
                'total_profit': r['total_profit'] or Decimal('0.00'),
                'unique_products': r['unique_products'] or 0
            }
            for r in results
        ]

    @staticmethod
    def get_hourly_sales(
        target_date: date,
        branch_id: Optional[int] = None
    ) -> list:
        """
        Get sales distribution by hour for a specific date.
        """
        from django.db.models.functions import ExtractHour

        queryset = Sale.objects.filter(
            created_at__date=target_date,
            status='completed'
        )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        results = queryset.annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            total_sales=Sum('total'),
            transaction_count=Count('id')
        ).order_by('hour')

        # Fill in missing hours with zeros
        hourly_data = {r['hour']: r for r in results}
        complete_hours = []
        for hour in range(24):
            if hour in hourly_data:
                complete_hours.append({
                    'hour': hour,
                    'hour_label': f"{hour:02d}:00",
                    'total_sales': hourly_data[hour]['total_sales'],
                    'transaction_count': hourly_data[hour]['transaction_count']
                })
            else:
                complete_hours.append({
                    'hour': hour,
                    'hour_label': f"{hour:02d}:00",
                    'total_sales': Decimal('0.00'),
                    'transaction_count': 0
                })

        return complete_hours


class InventoryReportService:
    """
    Service for generating inventory reports.
    """

    @staticmethod
    def get_stock_summary(branch_id: Optional[int] = None) -> dict:
        """
        Get overall stock summary statistics.
        """
        queryset = BranchStock.objects.filter(
            product__is_active=True,
            product__is_deleted=False
        )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        totals = queryset.aggregate(
            total_products=Count('product_id', distinct=True),
            total_units=Sum('quantity'),
            total_value=Sum(F('quantity') * F('product__cost_price')),
            total_retail_value=Sum(F('quantity') * F('product__sale_price'))
        )

        low_stock = queryset.filter(
            quantity__lte=F('product__min_stock'),
            quantity__gt=0
        ).count()

        out_of_stock = queryset.filter(quantity__lte=0).count()

        return {
            'total_products': totals['total_products'] or 0,
            'total_units': totals['total_units'] or 0,
            'total_cost_value': totals['total_value'] or Decimal('0.00'),
            'total_retail_value': totals['total_retail_value'] or Decimal('0.00'),
            'potential_profit': (totals['total_retail_value'] or Decimal('0')) - (totals['total_value'] or Decimal('0')),
            'low_stock_count': low_stock,
            'out_of_stock_count': out_of_stock
        }

    @staticmethod
    def get_stock_by_category(branch_id: Optional[int] = None) -> list:
        """
        Get stock breakdown by category.
        """
        queryset = BranchStock.objects.filter(
            product__is_active=True,
            product__is_deleted=False
        )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        results = queryset.values(
            'product__category_id',
            'product__category__name'
        ).annotate(
            product_count=Count('product_id', distinct=True),
            total_units=Sum('quantity'),
            total_value=Sum(F('quantity') * F('product__cost_price')),
            low_stock_count=Count(
                'id',
                filter=Q(quantity__lte=F('product__min_stock'), quantity__gt=0)
            )
        ).order_by('-total_value')

        return [
            {
                'category_id': r['product__category_id'],
                'category_name': r['product__category__name'],
                'product_count': r['product_count'] or 0,
                'total_units': r['total_units'] or 0,
                'total_value': r['total_value'] or Decimal('0.00'),
                'low_stock_count': r['low_stock_count'] or 0
            }
            for r in results
        ]

    @staticmethod
    def get_low_stock_products(
        branch_id: Optional[int] = None,
        limit: int = 50
    ) -> list:
        """
        Get list of products with low or no stock.
        """
        queryset = BranchStock.objects.filter(
            quantity__lte=F('product__min_stock'),
            product__is_active=True,
            product__is_deleted=False
        ).select_related('product', 'product__category', 'branch')

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        results = queryset.order_by('quantity')[:limit]

        return [
            {
                'product_id': bs.product_id,
                'product_name': bs.product.name,
                'product_sku': bs.product.sku,
                'category': bs.product.category.name,
                'branch_id': bs.branch_id,
                'branch_name': bs.branch.name,
                'current_stock': bs.quantity,
                'min_stock': bs.product.min_stock,
                'deficit': bs.product.min_stock - bs.quantity,
                'status': 'out_of_stock' if bs.quantity <= 0 else 'low_stock'
            }
            for bs in results
        ]

    @staticmethod
    def get_stock_movements_summary(
        date_from: date,
        date_to: date,
        branch_id: Optional[int] = None
    ) -> list:
        """
        Get stock movements summary by type.
        """
        queryset = StockMovement.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        results = queryset.values('movement_type').annotate(
            movement_count=Count('id'),
            total_quantity=Sum('quantity'),
            unique_products=Count('product_id', distinct=True)
        ).order_by('-movement_count')

        movement_labels = dict(StockMovement.MOVEMENT_TYPES)

        return [
            {
                'movement_type': r['movement_type'],
                'movement_type_display': movement_labels.get(r['movement_type'], r['movement_type']),
                'movement_count': r['movement_count'] or 0,
                'total_quantity': r['total_quantity'] or 0,
                'unique_products': r['unique_products'] or 0
            }
            for r in results
        ]

    @staticmethod
    def get_product_movement_history(
        product_id: int,
        branch_id: Optional[int] = None,
        days: int = 30
    ) -> list:
        """
        Get movement history for a specific product.
        """
        start_date = timezone.now().date() - timedelta(days=days)

        queryset = StockMovement.objects.filter(
            product_id=product_id,
            created_at__date__gte=start_date
        ).select_related('branch', 'created_by')

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        results = queryset.order_by('-created_at')

        movement_labels = dict(StockMovement.MOVEMENT_TYPES)

        return [
            {
                'id': m.id,
                'date': m.created_at.isoformat(),
                'movement_type': m.movement_type,
                'movement_type_display': movement_labels.get(m.movement_type, m.movement_type),
                'quantity': m.quantity,
                'previous_quantity': m.previous_quantity,
                'new_quantity': m.new_quantity,
                'branch_name': m.branch.name,
                'reference': m.reference,
                'notes': m.notes,
                'created_by': m.created_by.full_name
            }
            for m in results
        ]


class EmployeeReportService:
    """
    Service for generating employee performance reports.
    """

    @staticmethod
    def get_employee_performance(
        date_from: date,
        date_to: date,
        branch_id: Optional[int] = None
    ) -> list:
        """
        Get employee performance metrics including shifts and sales.
        """
        queryset = Employee.objects.filter(
            status='active',
            is_deleted=False
        ).select_related('user', 'branch')

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        results = []
        for employee in queryset:
            # Get shift data
            shifts = Shift.objects.filter(
                employee=employee,
                clock_in__date__gte=date_from,
                clock_in__date__lte=date_to,
                clock_out__isnull=False
            )

            shift_data = shifts.aggregate(
                total_shifts=Count('id'),
                total_hours=Sum('worked_hours')
            )

            # Get sales data (if employee has associated user)
            sales = Sale.objects.filter(
                cashier=employee.user,
                created_at__date__gte=date_from,
                created_at__date__lte=date_to,
                status='completed'
            )

            sales_data = sales.aggregate(
                total_sales=Sum('total'),
                transaction_count=Count('id'),
                avg_ticket=Avg('total')
            )

            results.append({
                'employee_id': employee.id,
                'employee_code': employee.employee_code,
                'employee_name': employee.full_name,
                'position': employee.position,
                'branch_name': employee.branch.name,
                'total_shifts': shift_data['total_shifts'] or 0,
                'total_hours': float(shift_data['total_hours'] or 0),
                'total_sales': sales_data['total_sales'] or Decimal('0.00'),
                'transaction_count': sales_data['transaction_count'] or 0,
                'avg_ticket': sales_data['avg_ticket'] or Decimal('0.00'),
                'sales_per_hour': (
                    float(sales_data['total_sales'] or 0) / float(shift_data['total_hours'])
                    if shift_data['total_hours'] and shift_data['total_hours'] > 0
                    else 0
                )
            })

        return sorted(results, key=lambda x: x['total_sales'], reverse=True)

    @staticmethod
    def get_shift_summary(
        date_from: date,
        date_to: date,
        branch_id: Optional[int] = None
    ) -> dict:
        """
        Get shift summary statistics.
        """
        queryset = Shift.objects.filter(
            clock_in__date__gte=date_from,
            clock_in__date__lte=date_to,
            clock_out__isnull=False
        )

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        totals = queryset.aggregate(
            total_shifts=Count('id'),
            total_hours=Sum('worked_hours'),
            avg_shift_hours=Avg('worked_hours'),
            total_break_hours=Sum('break_hours')
        )

        # Count by day of week
        from django.db.models.functions import ExtractWeekDay
        by_weekday = queryset.annotate(
            weekday=ExtractWeekDay('clock_in')
        ).values('weekday').annotate(
            shift_count=Count('id')
        ).order_by('weekday')

        weekday_names = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        weekday_data = {r['weekday']: r['shift_count'] for r in by_weekday}

        return {
            'total_shifts': totals['total_shifts'] or 0,
            'total_hours': float(totals['total_hours'] or 0),
            'avg_shift_hours': float(totals['avg_shift_hours'] or 0),
            'total_break_hours': float(totals['total_break_hours'] or 0),
            'by_weekday': [
                {
                    'weekday': i,
                    'weekday_name': weekday_names[i],
                    'shift_count': weekday_data.get(i + 1, 0)  # Django weekday is 1-indexed
                }
                for i in range(7)
            ]
        }


class BranchReportService:
    """
    Service for generating branch comparison reports.
    """

    @staticmethod
    def get_branch_comparison(
        date_from: date,
        date_to: date
    ) -> list:
        """
        Compare performance across all branches.
        """
        branches = Branch.objects.filter(
            is_active=True,
            is_deleted=False
        )

        results = []
        for branch in branches:
            # Sales data
            sales = Sale.objects.filter(
                branch=branch,
                created_at__date__gte=date_from,
                created_at__date__lte=date_to,
                status='completed'
            )

            sales_data = sales.aggregate(
                total_sales=Sum('total'),
                transaction_count=Count('id'),
                avg_ticket=Avg('total'),
                total_items=Sum('items__quantity')
            )

            # Inventory data
            stock_data = BranchStock.objects.filter(
                branch=branch,
                product__is_active=True,
                product__is_deleted=False
            ).aggregate(
                total_products=Count('id'),
                total_stock_value=Sum(F('quantity') * F('product__cost_price')),
                low_stock_count=Count(
                    'id',
                    filter=Q(quantity__lte=F('product__min_stock'), quantity__gt=0)
                )
            )

            # Employee data
            employee_count = Employee.objects.filter(
                branch=branch,
                status='active',
                is_deleted=False
            ).count()

            results.append({
                'branch_id': branch.id,
                'branch_name': branch.name,
                'branch_code': branch.code,
                'total_sales': sales_data['total_sales'] or Decimal('0.00'),
                'transaction_count': sales_data['transaction_count'] or 0,
                'avg_ticket': sales_data['avg_ticket'] or Decimal('0.00'),
                'total_items_sold': sales_data['total_items'] or 0,
                'total_products': stock_data['total_products'] or 0,
                'stock_value': stock_data['total_stock_value'] or Decimal('0.00'),
                'low_stock_count': stock_data['low_stock_count'] or 0,
                'employee_count': employee_count
            })

        return sorted(results, key=lambda x: x['total_sales'], reverse=True)
