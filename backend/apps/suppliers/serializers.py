"""
Serializers for Supplier module.
"""
from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone

from .models import Supplier, PurchaseOrder, PurchaseOrderItem
from apps.inventory.models import Product
from apps.branches.models import Branch


class SupplierBranchSerializer(serializers.ModelSerializer):
    """Nested serializer for Branch in PurchaseOrder."""
    class Meta:
        model = Branch
        fields = ['id', 'name', 'code']


class SupplierProductSerializer(serializers.ModelSerializer):
    """Nested serializer for Product in PurchaseOrderItem."""
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'barcode']


class SupplierListSerializer(serializers.ModelSerializer):
    """Serializer for supplier list view."""
    full_address = serializers.CharField(read_only=True)
    purchase_orders_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'code', 'contact_name', 'email', 'phone',
            'city', 'is_active', 'payment_terms', 'credit_limit',
            'full_address', 'purchase_orders_count'
        ]

    def get_purchase_orders_count(self, obj):
        return obj.purchase_orders.count()


class SupplierDetailSerializer(serializers.ModelSerializer):
    """Serializer for supplier detail view with all fields."""
    full_address = serializers.CharField(read_only=True)
    purchase_orders_count = serializers.SerializerMethodField()
    total_purchases = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'code', 'contact_name', 'email', 'phone', 'mobile',
            'address', 'city', 'state', 'postal_code', 'country',
            'tax_id', 'website', 'notes',
            'payment_terms', 'credit_limit', 'is_active',
            'full_address', 'purchase_orders_count', 'total_purchases',
            'created_at', 'updated_at'
        ]

    def get_purchase_orders_count(self, obj):
        return obj.purchase_orders.count()

    def get_total_purchases(self, obj):
        from django.db.models import Sum
        total = obj.purchase_orders.filter(
            status='received'
        ).aggregate(total=Sum('total'))['total']
        return total or Decimal('0.00')


class CreateSupplierSerializer(serializers.ModelSerializer):
    """Serializer for creating a new supplier."""
    class Meta:
        model = Supplier
        fields = [
            'name', 'code', 'contact_name', 'email', 'phone', 'mobile',
            'address', 'city', 'state', 'postal_code', 'country',
            'tax_id', 'website', 'notes', 'payment_terms', 'credit_limit', 'is_active'
        ]

    def validate_code(self, value):
        """Ensure code is uppercase."""
        return value.upper()

    def validate_email(self, value):
        """Validate email is unique among active suppliers."""
        if value and Supplier.active.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un proveedor activo con este email")
        return value


class UpdateSupplierSerializer(serializers.ModelSerializer):
    """Serializer for updating supplier data."""
    class Meta:
        model = Supplier
        fields = [
            'name', 'contact_name', 'email', 'phone', 'mobile',
            'address', 'city', 'state', 'postal_code', 'country',
            'tax_id', 'website', 'notes', 'payment_terms', 'credit_limit', 'is_active'
        ]

    def validate_email(self, value):
        """Validate email is unique among active suppliers."""
        if value:
            queryset = Supplier.active.filter(email=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("Ya existe un proveedor activo con este email")
        return value


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for PurchaseOrderItem."""
    product = SupplierProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    is_fully_received = serializers.BooleanField(read_only=True)
    pending_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'product', 'product_id', 'quantity_ordered', 'quantity_received',
            'unit_price', 'subtotal', 'is_fully_received', 'pending_quantity'
        ]
        read_only_fields = ['id', 'subtotal']

    def validate_product_id(self, value):
        """Validate product exists and is active."""
        if not Product.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Producto no encontrado o inactivo")
        return value

    def validate_quantity_ordered(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a cero")
        return value

    def validate_unit_price(self, value):
        """Validate price is positive."""
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a cero")
        return value


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    """Serializer for purchase order list view."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier', 'supplier_name', 'branch', 'branch_name',
            'status', 'order_date', 'expected_date', 'total', 'items_count', 'created_at'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for purchase order detail view."""
    supplier = SupplierListSerializer(read_only=True)
    branch = SupplierBranchSerializer(read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    received_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier', 'branch', 'status',
            'order_date', 'expected_date', 'received_date',
            'subtotal', 'tax', 'total', 'notes',
            'created_by', 'created_by_name',
            'approved_by', 'approved_by_name',
            'received_by', 'received_by_name',
            'items', 'created_at', 'updated_at'
        ]

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None

    def get_received_by_name(self, obj):
        return obj.received_by.get_full_name() if obj.received_by else None


class CreatePurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for creating a new purchase order."""
    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'branch', 'order_date', 'expected_date', 'notes', 'items']

    def validate_items(self, value):
        """Validate that at least one item is provided."""
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un producto")
        return value

    def validate(self, attrs):
        """Validate supplier and branch are active."""
        if not attrs['supplier'].is_active:
            raise serializers.ValidationError({"supplier": "El proveedor no está activo"})

        if not attrs['branch'].is_active:
            raise serializers.ValidationError({"branch": "La sucursal no está activa"})

        return attrs

    def create(self, validated_data):
        """Create purchase order with items."""
        items_data = validated_data.pop('items')

        # Generate order number
        from django.db.models import Max
        last_order = PurchaseOrder.objects.all().aggregate(Max('id'))
        next_id = (last_order['id__max'] or 0) + 1
        order_number = f"PO-{next_id:06d}"

        # Create purchase order (created_by is set by perform_create in view)
        purchase_order = PurchaseOrder.objects.create(
            order_number=order_number,
            **validated_data
        )

        # Create items
        for item_data in items_data:
            product_id = item_data.pop('product_id')
            product = Product.objects.get(id=product_id)

            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                product=product,
                **item_data
            )

        # Calculate totals
        purchase_order.calculate_totals()

        return purchase_order


class UpdatePurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for updating purchase order."""
    class Meta:
        model = PurchaseOrder
        fields = ['order_date', 'expected_date', 'notes']


class ReceiveItemSerializer(serializers.Serializer):
    """Serializer for receiving items in a purchase order."""
    item_id = serializers.IntegerField()
    quantity_received = serializers.IntegerField(min_value=1)

    def validate_quantity_received(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a cero")
        return value
