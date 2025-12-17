from rest_framework import serializers
from decimal import Decimal

from .models import Category, Product, BranchStock, StockMovement, StockAlert


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    full_path = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'parent', 'is_active',
            'children', 'product_count', 'full_path',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_children(self, obj):
        # Only include active children, prevent recursion issues
        children = obj.children.filter(is_deleted=False, is_active=True)
        return CategorySerializer(children, many=True).data

    def get_product_count(self, obj):
        return obj.products.filter(is_deleted=False, is_active=True).count()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Simplified serializer for category dropdowns/trees"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'full_path']


class BranchStockSerializer(serializers.ModelSerializer):
    """Serializer for branch stock levels"""
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    branch_code = serializers.CharField(source='branch.code', read_only=True)
    available_quantity = serializers.ReadOnlyField()
    stock_status = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_out_of_stock = serializers.ReadOnlyField()

    class Meta:
        model = BranchStock
        fields = [
            'id', 'branch', 'branch_name', 'branch_code',
            'quantity', 'reserved_quantity', 'available_quantity',
            'stock_status', 'is_low_stock', 'is_out_of_stock',
            'updated_at'
        ]
        read_only_fields = ['updated_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    total_stock = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    profit_margin = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'barcode', 'category', 'category_name',
            'cost_price', 'sale_price', 'profit_margin', 'unit',
            'min_stock', 'total_stock', 'stock_status', 'is_active', 'is_sellable',
            'supplier', 'supplier_name', 'image'
        ]

    def get_total_stock(self, obj):
        branch_id = self.context.get('branch_id')
        if branch_id:
            from .models import BranchStock
            try:
                branch_stock = BranchStock.objects.get(product=obj, branch_id=branch_id)
                return branch_stock.quantity
            except BranchStock.DoesNotExist:
                return 0
        return obj.get_total_stock()

    def get_stock_status(self, obj):
        """Get stock status based on branch context or total stock"""
        from .models import (
            BranchStock, STOCK_THRESHOLD_OK, STOCK_THRESHOLD_LOW,
            STOCK_STATUS_OK, STOCK_STATUS_LOW, STOCK_STATUS_OUT
        )
        branch_id = self.context.get('branch_id')
        if branch_id:
            try:
                branch_stock = BranchStock.objects.get(product=obj, branch_id=branch_id)
                return branch_stock.stock_status
            except BranchStock.DoesNotExist:
                return STOCK_STATUS_OUT
        return obj.stock_status


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail view"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_path = serializers.CharField(source='category.full_path', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    branch_stocks = BranchStockSerializer(many=True, read_only=True)
    total_stock = serializers.SerializerMethodField()
    stock_status = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'sku', 'barcode',
            'category', 'category_name', 'category_path',
            'cost_price', 'sale_price', 'profit_margin',
            'unit', 'min_stock', 'max_stock',
            'image', 'is_active', 'is_sellable',
            'supplier', 'supplier_name',
            'branch_stocks', 'total_stock', 'stock_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_total_stock(self, obj):
        return obj.get_total_stock()


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'sku', 'barcode',
            'category', 'cost_price', 'sale_price',
            'unit', 'min_stock', 'max_stock',
            'image', 'is_active', 'is_sellable', 'supplier'
        ]
        read_only_fields = ['id']

    def validate_sale_price(self, value):
        cost_price = self.initial_data.get('cost_price')
        if cost_price and Decimal(str(value)) < Decimal(str(cost_price)):
            raise serializers.ValidationError(
                "El precio de venta no puede ser menor al precio de costo"
            )
        return value

    def validate_barcode(self, value):
        if value:
            # Check for unique barcode excluding current instance
            qs = Product.objects.filter(barcode=value, is_deleted=False)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Ya existe un producto con este código de barras"
                )
        return value


class ProductBarcodeSearchSerializer(serializers.Serializer):
    """Serializer for barcode search response"""
    product = ProductDetailSerializer()
    stock_in_branch = serializers.IntegerField()
    available_in_branch = serializers.IntegerField()


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for stock movements"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    related_branch_name = serializers.CharField(
        source='related_branch.name',
        read_only=True
    )
    movement_type_display = serializers.CharField(
        source='get_movement_type_display',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.full_name',
        read_only=True
    )

    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'branch', 'branch_name',
            'movement_type', 'movement_type_display',
            'quantity', 'previous_quantity', 'new_quantity',
            'reference', 'related_branch', 'related_branch_name',
            'notes', 'created_by', 'created_by_name',
            'created_at'
        ]
        read_only_fields = ['created_at', 'created_by']


class StockAdjustmentSerializer(serializers.Serializer):
    """Serializer for manual stock adjustments"""
    product_id = serializers.IntegerField()
    branch_id = serializers.IntegerField()
    adjustment_type = serializers.ChoiceField(
        choices=[('add', 'Agregar'), ('subtract', 'Restar'), ('set', 'Establecer')]
    )
    quantity = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=200)
    notes = serializers.CharField(required=False, allow_blank=True)


class StockTransferSerializer(serializers.Serializer):
    """Serializer for stock transfers between branches"""
    product_id = serializers.IntegerField()
    from_branch_id = serializers.IntegerField()
    to_branch_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['from_branch_id'] == data['to_branch_id']:
            raise serializers.ValidationError(
                "Las sucursales de origen y destino deben ser diferentes"
            )
        return data


class StockAlertSerializer(serializers.ModelSerializer):
    """Serializer for stock alerts"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    alert_type_display = serializers.CharField(
        source='get_alert_type_display',
        read_only=True
    )

    class Meta:
        model = StockAlert
        fields = [
            'id', 'product', 'product_name',
            'category', 'category_name',
            'branch', 'branch_name',
            'alert_type', 'alert_type_display',
            'threshold', 'is_active', 'notify_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ActiveAlertSerializer(serializers.Serializer):
    """Serializer for currently active stock alerts"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    branch_id = serializers.IntegerField()
    branch_name = serializers.CharField()
    alert_type = serializers.CharField()
    current_quantity = serializers.IntegerField()
    threshold = serializers.IntegerField()
