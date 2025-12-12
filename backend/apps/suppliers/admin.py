"""
Django Admin configuration for Suppliers app.
"""
from django.contrib import admin
from .models import Supplier, PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    """Inline admin for PurchaseOrderItem."""
    model = PurchaseOrderItem
    extra = 1
    fields = ['product', 'quantity_ordered', 'quantity_received', 'unit_price', 'subtotal']
    readonly_fields = ['subtotal']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin configuration for Supplier model."""
    list_display = [
        'code', 'name', 'contact_name', 'email', 'phone',
        'city', 'payment_terms', 'credit_limit', 'is_active'
    ]
    list_filter = ['is_active', 'city', 'country']
    search_fields = ['name', 'code', 'contact_name', 'email', 'phone', 'tax_id']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'deleted_by']

    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'code', 'contact_name', 'is_active')
        }),
        ('Contacto', {
            'fields': ('email', 'phone', 'mobile', 'website')
        }),
        ('Dirección', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Información Comercial', {
            'fields': ('tax_id', 'payment_terms', 'credit_limit')
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Admin configuration for PurchaseOrder model."""
    list_display = [
        'order_number', 'supplier', 'branch', 'status',
        'order_date', 'expected_date', 'total', 'created_by'
    ]
    list_filter = ['status', 'branch', 'order_date', 'expected_date']
    search_fields = ['order_number', 'supplier__name', 'supplier__code']
    ordering = ['-created_at']
    readonly_fields = ['order_number', 'subtotal', 'tax', 'total', 'created_at', 'updated_at']
    inlines = [PurchaseOrderItemInline]

    fieldsets = (
        ('Información de la Orden', {
            'fields': ('order_number', 'supplier', 'branch', 'status')
        }),
        ('Fechas', {
            'fields': ('order_date', 'expected_date', 'received_date')
        }),
        ('Totales', {
            'fields': ('subtotal', 'tax', 'total')
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'approved_by', 'received_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """Recalculate totals after saving items."""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        formset.save_m2m()

        # Recalculate totals
        if hasattr(form.instance, 'calculate_totals'):
            form.instance.calculate_totals()


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    """Admin configuration for PurchaseOrderItem model."""
    list_display = [
        'purchase_order', 'product', 'quantity_ordered',
        'quantity_received', 'unit_price', 'subtotal'
    ]
    list_filter = ['purchase_order__status']
    search_fields = ['product__name', 'product__sku', 'purchase_order__order_number']
    ordering = ['-created_at']
    readonly_fields = ['subtotal', 'created_at', 'updated_at']

    fieldsets = (
        ('Información del Item', {
            'fields': ('purchase_order', 'product')
        }),
        ('Cantidades', {
            'fields': ('quantity_ordered', 'quantity_received')
        }),
        ('Precios', {
            'fields': ('unit_price', 'subtotal')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
