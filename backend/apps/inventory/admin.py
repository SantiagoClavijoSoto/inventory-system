from django.contrib import admin
from .models import Category, Product, BranchStock, StockMovement, StockAlert


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'sku', 'name', 'category', 'sale_price',
        'is_active', 'is_sellable', 'created_at'
    ]
    list_filter = ['is_active', 'is_sellable', 'category', 'unit']
    search_fields = ['name', 'sku', 'barcode', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BranchStock)
class BranchStockAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'branch', 'quantity',
        'reserved_quantity', 'available_quantity', 'updated_at'
    ]
    list_filter = ['branch']
    search_fields = ['product__name', 'product__sku']
    ordering = ['product__name']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'branch', 'movement_type',
        'quantity', 'created_by', 'created_at'
    ]
    list_filter = ['movement_type', 'branch', 'created_at']
    search_fields = ['product__name', 'product__sku', 'reference']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'category', 'branch',
        'alert_type', 'threshold', 'is_active'
    ]
    list_filter = ['alert_type', 'is_active', 'branch']
    search_fields = ['product__name', 'category__name']
