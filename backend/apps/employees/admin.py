"""
Admin configuration for Employee models.
"""
from django.contrib import admin
from .models import Employee, Shift


class ShiftInline(admin.TabularInline):
    model = Shift
    extra = 0
    readonly_fields = ['total_hours', 'break_hours', 'worked_hours']
    fields = [
        'branch',
        'clock_in',
        'clock_out',
        'break_start',
        'break_end',
        'total_hours',
        'worked_hours',
        'is_manual_entry',
    ]
    ordering = ['-clock_in']
    max_num = 10


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_code',
        'full_name',
        'branch',
        'position',
        'employment_type',
        'status',
        'hire_date',
    ]
    list_filter = ['status', 'employment_type', 'branch', 'department']
    search_fields = [
        'employee_code',
        'user__first_name',
        'user__last_name',
        'user__email',
        'position',
    ]
    readonly_fields = [
        'employee_code',
        'full_name',
        'email',
        'years_of_service',
        'created_at',
        'updated_at',
    ]
    date_hierarchy = 'hire_date'
    inlines = [ShiftInline]

    fieldsets = (
        ('Información del Empleado', {
            'fields': (
                'user',
                'employee_code',
                'full_name',
                'email',
            )
        }),
        ('Empleo', {
            'fields': (
                'branch',
                'position',
                'department',
                'employment_type',
                'status',
            )
        }),
        ('Fechas', {
            'fields': (
                'hire_date',
                'termination_date',
                'years_of_service',
            )
        }),
        ('Compensación', {
            'fields': ('salary', 'hourly_rate'),
            'classes': ('collapse',)
        }),
        ('Contacto de Emergencia', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'address'),
            'classes': ('collapse',)
        }),
        ('Documentos', {
            'fields': ('tax_id', 'social_security_number'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'branch')


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = [
        'employee',
        'branch',
        'clock_in',
        'clock_out',
        'worked_hours',
        'is_complete',
        'is_manual_entry',
    ]
    list_filter = ['branch', 'is_manual_entry', 'clock_in']
    search_fields = [
        'employee__employee_code',
        'employee__user__first_name',
        'employee__user__last_name',
    ]
    readonly_fields = [
        'total_hours',
        'break_hours',
        'worked_hours',
        'created_at',
        'updated_at',
    ]
    date_hierarchy = 'clock_in'
    raw_id_fields = ['employee', 'adjusted_by']

    fieldsets = (
        ('Turno', {
            'fields': (
                'employee',
                'branch',
            )
        }),
        ('Tiempos', {
            'fields': (
                'clock_in',
                'clock_out',
                'break_start',
                'break_end',
            )
        }),
        ('Horas Calculadas', {
            'fields': (
                'total_hours',
                'break_hours',
                'worked_hours',
            )
        }),
        ('Ajustes', {
            'fields': (
                'is_manual_entry',
                'adjusted_by',
                'notes',
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'employee',
            'employee__user',
            'branch',
            'adjusted_by',
        )
