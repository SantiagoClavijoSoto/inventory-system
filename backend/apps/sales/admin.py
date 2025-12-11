"""
Admin configuration for Sales models.
"""
from django.contrib import admin
from .models import Sale, SaleItem, DailyCashRegister


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['subtotal', 'product_name', 'product_sku', 'cost_price']
    fields = [
        'product',
        'product_name',
        'product_sku',
        'quantity',
        'unit_price',
        'cost_price',
        'discount_amount',
        'subtotal',
    ]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        'sale_number',
        'branch',
        'cashier',
        'total',
        'payment_method',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'payment_method', 'branch', 'created_at']
    search_fields = ['sale_number', 'customer_name', 'customer_phone']
    readonly_fields = [
        'sale_number',
        'subtotal',
        'tax_amount',
        'total',
        'change_amount',
        'voided_at',
        'voided_by',
        'created_at',
        'updated_at',
    ]
    date_hierarchy = 'created_at'
    inlines = [SaleItemInline]

    fieldsets = (
        ('Información de Venta', {
            'fields': ('sale_number', 'branch', 'cashier', 'status')
        }),
        ('Totales', {
            'fields': (
                'subtotal',
                'discount_percent',
                'discount_amount',
                'tax_amount',
                'total',
            )
        }),
        ('Pago', {
            'fields': (
                'payment_method',
                'amount_tendered',
                'change_amount',
                'payment_reference',
            )
        }),
        ('Cliente', {
            'fields': ('customer_name', 'customer_phone', 'customer_email'),
            'classes': ('collapse',)
        }),
        ('Anulación', {
            'fields': ('voided_at', 'voided_by', 'void_reason'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DailyCashRegister)
class DailyCashRegisterAdmin(admin.ModelAdmin):
    list_display = [
        'branch',
        'date',
        'opening_amount',
        'closing_amount',
        'difference',
        'is_closed',
    ]
    list_filter = ['is_closed', 'branch', 'date']
    search_fields = ['branch__name']
    readonly_fields = [
        'expected_amount',
        'cash_sales_total',
        'card_sales_total',
        'transfer_sales_total',
        'difference',
        'opened_at',
        'closed_at',
        'created_at',
        'updated_at',
    ]
    date_hierarchy = 'date'

    fieldsets = (
        ('Información', {
            'fields': ('branch', 'date', 'is_closed')
        }),
        ('Apertura', {
            'fields': ('opening_amount', 'opened_by', 'opened_at')
        }),
        ('Cierre', {
            'fields': ('closing_amount', 'closed_by', 'closed_at')
        }),
        ('Totales', {
            'fields': (
                'expected_amount',
                'cash_sales_total',
                'card_sales_total',
                'transfer_sales_total',
                'difference',
            )
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
