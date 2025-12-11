"""
Serializers for Sales API.
"""
from rest_framework import serializers
from decimal import Decimal

from .models import Sale, SaleItem, DailyCashRegister


class SaleItemSerializer(serializers.ModelSerializer):
    """Serializer for individual sale items."""
    profit = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    profit_margin = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = SaleItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_sku',
            'quantity',
            'unit_price',
            'cost_price',
            'discount_amount',
            'subtotal',
            'profit',
            'profit_margin',
        ]
        read_only_fields = [
            'id',
            'product_name',
            'product_sku',
            'cost_price',
            'subtotal',
        ]


class SaleItemInputSerializer(serializers.Serializer):
    """Serializer for creating sale items."""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal('0.00')
    )
    custom_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )


class SaleSerializer(serializers.ModelSerializer):
    """Serializer for Sale list view."""
    items = SaleItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    profit = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    is_voided = serializers.BooleanField(read_only=True)
    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True
    )
    cashier_name = serializers.CharField(
        source='cashier.full_name',
        read_only=True
    )
    voided_by_name = serializers.CharField(
        source='voided_by.full_name',
        read_only=True,
        allow_null=True
    )
    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Sale
        fields = [
            'id',
            'sale_number',
            'branch',
            'branch_name',
            'cashier',
            'cashier_name',
            'subtotal',
            'discount_amount',
            'discount_percent',
            'tax_amount',
            'total',
            'payment_method',
            'payment_method_display',
            'amount_tendered',
            'change_amount',
            'payment_reference',
            'status',
            'status_display',
            'voided_at',
            'voided_by',
            'voided_by_name',
            'void_reason',
            'customer_name',
            'customer_phone',
            'customer_email',
            'notes',
            'items',
            'items_count',
            'total_quantity',
            'profit',
            'is_voided',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'sale_number',
            'subtotal',
            'tax_amount',
            'total',
            'change_amount',
            'status',
            'voided_at',
            'voided_by',
            'created_at',
            'updated_at',
        ]


class CreateSaleSerializer(serializers.Serializer):
    """Serializer for creating a new sale."""
    items = SaleItemInputSerializer(many=True)
    payment_method = serializers.ChoiceField(
        choices=Sale.PAYMENT_METHOD_CHOICES
    )
    amount_tendered = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal('0.00')
    )
    discount_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        default=Decimal('0.00'),
        min_value=Decimal('0.00'),
        max_value=Decimal('100.00')
    )
    discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal('0.00'),
        min_value=Decimal('0.00')
    )
    customer_name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        default=''
    )
    customer_phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        default=''
    )
    customer_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        default=''
    )
    payment_reference = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default=''
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "La venta debe tener al menos un producto"
            )
        return value


class VoidSaleSerializer(serializers.Serializer):
    """Serializer for voiding a sale."""
    reason = serializers.CharField(
        min_length=10,
        max_length=500,
        help_text="Razón de anulación (mínimo 10 caracteres)"
    )


class RefundItemSerializer(serializers.Serializer):
    """Serializer for refund item."""
    sale_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class RefundSaleSerializer(serializers.Serializer):
    """Serializer for creating a refund."""
    items = RefundItemSerializer(many=True)
    reason = serializers.CharField(
        min_length=10,
        max_length=500,
        help_text="Razón del reembolso (mínimo 10 caracteres)"
    )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "Debe especificar al menos un item para reembolsar"
            )
        return value


class DailyCashRegisterSerializer(serializers.ModelSerializer):
    """Serializer for daily cash register."""
    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True
    )
    opened_by_name = serializers.CharField(
        source='opened_by.full_name',
        read_only=True
    )
    closed_by_name = serializers.CharField(
        source='closed_by.full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = DailyCashRegister
        fields = [
            'id',
            'branch',
            'branch_name',
            'date',
            'opening_amount',
            'opened_by',
            'opened_by_name',
            'opened_at',
            'closing_amount',
            'closed_by',
            'closed_by_name',
            'closed_at',
            'expected_amount',
            'cash_sales_total',
            'card_sales_total',
            'transfer_sales_total',
            'difference',
            'is_closed',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'opened_by',
            'opened_at',
            'closed_by',
            'closed_at',
            'expected_amount',
            'cash_sales_total',
            'card_sales_total',
            'transfer_sales_total',
            'difference',
            'is_closed',
            'created_at',
            'updated_at',
        ]


class OpenRegisterSerializer(serializers.Serializer):
    """Serializer for opening a cash register."""
    opening_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00')
    )


class CloseRegisterSerializer(serializers.Serializer):
    """Serializer for closing a cash register."""
    closing_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00')
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )


class DailySummarySerializer(serializers.Serializer):
    """Serializer for daily sales summary."""
    date = serializers.DateField()
    branch = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_items_sold = serializers.IntegerField()
    sale_count = serializers.IntegerField()
    average_sale = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_discounts = serializers.DecimalField(max_digits=12, decimal_places=2)
    cash_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    card_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    transfer_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    voided_count = serializers.IntegerField()


class TopProductSerializer(serializers.Serializer):
    """Serializer for top selling products."""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    total_quantity = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
