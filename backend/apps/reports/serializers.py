"""
Serializers for report parameters and responses.
"""
from rest_framework import serializers
from datetime import date, timedelta


class DateRangeSerializer(serializers.Serializer):
    """
    Serializer for date range parameters.
    """
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    branch_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')

        # Default to last 30 days if not provided
        if not date_to:
            attrs['date_to'] = date.today()
        if not date_from:
            attrs['date_from'] = attrs['date_to'] - timedelta(days=30)

        if attrs['date_from'] > attrs['date_to']:
            raise serializers.ValidationError({
                'date_from': 'La fecha inicial no puede ser mayor que la fecha final.'
            })

        # Limit range to 1 year
        if (attrs['date_to'] - attrs['date_from']).days > 365:
            raise serializers.ValidationError({
                'date_from': 'El rango máximo es de 1 año.'
            })

        return attrs


class SalesPeriodSerializer(DateRangeSerializer):
    """
    Serializer for sales period report parameters.
    """
    GROUP_CHOICES = [
        ('day', 'Día'),
        ('week', 'Semana'),
        ('month', 'Mes'),
    ]

    group_by = serializers.ChoiceField(
        choices=GROUP_CHOICES,
        default='day',
        required=False
    )


class TopProductsSerializer(serializers.Serializer):
    """
    Serializer for top products report parameters.
    """
    days = serializers.IntegerField(default=30, min_value=1, max_value=365)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=100)
    branch_id = serializers.IntegerField(required=False, allow_null=True)


class PeriodComparisonSerializer(serializers.Serializer):
    """
    Serializer for period comparison parameters.
    """
    days = serializers.IntegerField(default=7, min_value=1, max_value=90)
    branch_id = serializers.IntegerField(required=False, allow_null=True)


class HourlySalesSerializer(serializers.Serializer):
    """
    Serializer for hourly sales report parameters.
    """
    target_date = serializers.DateField(required=False)
    branch_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_target_date(self, value):
        if not value:
            return date.today()
        return value


class ProductMovementSerializer(serializers.Serializer):
    """
    Serializer for product movement history parameters.
    """
    product_id = serializers.IntegerField()
    branch_id = serializers.IntegerField(required=False, allow_null=True)
    days = serializers.IntegerField(default=30, min_value=1, max_value=365)


class LowStockSerializer(serializers.Serializer):
    """
    Serializer for low stock report parameters.
    """
    branch_id = serializers.IntegerField(required=False, allow_null=True)
    limit = serializers.IntegerField(default=50, min_value=1, max_value=200)


# Response Serializers (for documentation purposes)

class TodaySummaryResponseSerializer(serializers.Serializer):
    """Response serializer for today's summary."""
    date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_transactions = serializers.IntegerField()
    total_items = serializers.IntegerField()
    avg_ticket = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()


class PeriodComparisonResponseSerializer(serializers.Serializer):
    """Response serializer for period comparison."""

    class PeriodDataSerializer(serializers.Serializer):
        start = serializers.DateField()
        end = serializers.DateField()
        total = serializers.DecimalField(max_digits=12, decimal_places=2)
        transactions = serializers.IntegerField()

    current_period = PeriodDataSerializer()
    previous_period = PeriodDataSerializer()
    change_percent = serializers.DecimalField(max_digits=6, decimal_places=2)
    trend = serializers.ChoiceField(choices=['up', 'down', 'stable'])


class LowStockCountResponseSerializer(serializers.Serializer):
    """Response serializer for low stock count."""
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    total_alerts = serializers.IntegerField()


class TopProductResponseSerializer(serializers.Serializer):
    """Response serializer for top products."""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    total_quantity = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=12, decimal_places=2)


class SalesByPeriodResponseSerializer(serializers.Serializer):
    """Response serializer for sales by period."""
    period = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_transactions = serializers.IntegerField()
    total_items = serializers.IntegerField()
    avg_ticket = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_discounts = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_tax = serializers.DecimalField(max_digits=10, decimal_places=2)


class StockSummaryResponseSerializer(serializers.Serializer):
    """Response serializer for stock summary."""
    total_products = serializers.IntegerField()
    total_units = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_retail_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    potential_profit = serializers.DecimalField(max_digits=14, decimal_places=2)
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
