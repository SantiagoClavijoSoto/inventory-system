"""
Django admin configuration for companies app.
"""
from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin configuration for Company model."""
    list_display = [
        'name', 'slug', 'email', 'plan', 'is_active',
        'branch_count', 'user_count', 'created_at'
    ]
    list_filter = ['plan', 'is_active', 'is_deleted', 'created_at']
    search_fields = ['name', 'slug', 'email', 'legal_name', 'tax_id']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'deleted_by']
    ordering = ['name']

    fieldsets = (
        ('Identificación', {
            'fields': ('name', 'slug', 'legal_name', 'tax_id')
        }),
        ('Branding', {
            'fields': ('logo', 'primary_color', 'secondary_color')
        }),
        ('Contacto', {
            'fields': ('email', 'phone', 'website', 'address')
        }),
        ('Plan y Límites', {
            'fields': ('plan', 'max_branches', 'max_users', 'max_products')
        }),
        ('Estado', {
            'fields': ('is_active', 'owner')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'is_deleted', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',)
        }),
    )

    def branch_count(self, obj):
        return obj.branch_count
    branch_count.short_description = 'Sucursales'

    def user_count(self, obj):
        return obj.user_count
    user_count.short_description = 'Usuarios'
