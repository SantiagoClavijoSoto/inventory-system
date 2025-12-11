"""
Admin configuration for branches app.
"""
from django.contrib import admin
from .models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'city', 'is_active', 'is_main', 'created_at']
    list_filter = ['is_active', 'is_main', 'city', 'state']
    search_fields = ['name', 'code', 'city', 'address']
    ordering = ['name']

    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'code', 'is_active', 'is_main')
        }),
        ('Dirección', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Contacto', {
            'fields': ('phone', 'email', 'manager_name', 'manager_phone')
        }),
        ('Horario', {
            'fields': ('opening_time', 'closing_time')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
