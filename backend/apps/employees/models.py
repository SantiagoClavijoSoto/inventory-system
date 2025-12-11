"""
Employee models for workforce management.
Handles employee profiles and shift tracking.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone

from core.mixins import TimestampMixin, SoftDeleteMixin, ActiveManager


class Employee(TimestampMixin, SoftDeleteMixin, models.Model):
    """
    Extended employee information linked to User.
    Contains employment-specific data separate from auth.
    """
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Tiempo completo'),
        ('part_time', 'Medio tiempo'),
        ('contract', 'Por contrato'),
        ('temporary', 'Temporal'),
    ]

    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('on_leave', 'De licencia'),
        ('terminated', 'Terminado'),
    ]

    # Link to User (OneToOne)
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name='Usuario'
    )

    # Employment info
    employee_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código de empleado',
        help_text='Identificador único del empleado'
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default='full_time',
        verbose_name='Tipo de empleo'
    )
    position = models.CharField(
        max_length=100,
        verbose_name='Puesto',
        help_text='Título del puesto de trabajo'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Departamento'
    )
    hire_date = models.DateField(
        verbose_name='Fecha de contratación'
    )
    termination_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de terminación'
    )

    # Primary branch assignment
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='Sucursal asignada'
    )

    # Compensation
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Salario',
        help_text='Salario mensual'
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Tarifa por hora',
        help_text='Para cálculo de horas extra'
    )

    # Contact (additional to User)
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Contacto de emergencia'
    )
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono de emergencia'
    )
    address = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )

    # Documents
    tax_id = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='RFC/CURP',
        help_text='Identificación fiscal'
    )
    social_security_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Número de seguro social'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Estado'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )

    # Managers
    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['employee_code']),
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['status', '-hire_date']),
        ]

    def __str__(self):
        return f"{self.employee_code} - {self.user.full_name}"

    @property
    def full_name(self):
        """Get employee full name from user."""
        return self.user.full_name

    @property
    def email(self):
        """Get employee email from user."""
        return self.user.email

    @property
    def is_active(self):
        """Check if employee is active."""
        return self.status == 'active' and not self.is_deleted

    @property
    def years_of_service(self):
        """Calculate years of service."""
        from datetime import date
        end_date = self.termination_date or date.today()
        delta = end_date - self.hire_date
        return delta.days // 365

    @classmethod
    def generate_employee_code(cls, branch_code: str) -> str:
        """
        Generate a unique employee code.
        Format: EMP-BRANCH-XXXX
        """
        prefix = f"EMP-{branch_code}"
        last_employee = cls.objects.filter(
            employee_code__startswith=prefix
        ).order_by('-employee_code').first()

        if last_employee:
            try:
                sequence = int(last_employee.employee_code.split('-')[-1]) + 1
            except (ValueError, IndexError):
                sequence = 1
        else:
            sequence = 1

        return f"{prefix}-{sequence:04d}"

    def get_current_shift(self):
        """Get the current open shift for this employee."""
        return self.shifts.filter(
            clock_out__isnull=True
        ).order_by('-clock_in').first()

    def is_clocked_in(self):
        """Check if employee is currently clocked in."""
        return self.get_current_shift() is not None


class Shift(TimestampMixin, models.Model):
    """
    Employee shift record for time tracking.
    Records clock-in and clock-out times.
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='shifts',
        verbose_name='Empleado'
    )
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.PROTECT,
        related_name='shifts',
        verbose_name='Sucursal',
        help_text='Sucursal donde se registró el turno'
    )

    # Time tracking
    clock_in = models.DateTimeField(
        verbose_name='Hora de entrada'
    )
    clock_out = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hora de salida'
    )

    # Break time tracking (optional)
    break_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Inicio de descanso'
    )
    break_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fin de descanso'
    )

    # Calculated fields (stored for performance)
    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Horas totales'
    )
    break_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Horas de descanso'
    )
    worked_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Horas trabajadas'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )

    # Manual adjustments
    is_manual_entry = models.BooleanField(
        default=False,
        verbose_name='Entrada manual',
        help_text='Si fue registrado manualmente por un supervisor'
    )
    adjusted_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shift_adjustments',
        verbose_name='Ajustado por'
    )

    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        ordering = ['-clock_in']
        indexes = [
            models.Index(fields=['employee', '-clock_in']),
            models.Index(fields=['branch', '-clock_in']),
            models.Index(fields=['-clock_in']),
        ]

    def __str__(self):
        date_str = self.clock_in.strftime('%Y-%m-%d')
        status = "En curso" if not self.clock_out else f"{self.worked_hours}h"
        return f"{self.employee.full_name} - {date_str} ({status})"

    @property
    def is_complete(self):
        """Check if shift is complete (has clock_out)."""
        return self.clock_out is not None

    @property
    def duration(self):
        """Get shift duration as timedelta."""
        if not self.clock_out:
            return timezone.now() - self.clock_in
        return self.clock_out - self.clock_in

    def calculate_hours(self):
        """Calculate and store worked hours."""
        if not self.clock_out:
            return None

        # Total shift duration in hours
        total_delta = self.clock_out - self.clock_in
        self.total_hours = Decimal(str(total_delta.total_seconds() / 3600)).quantize(Decimal('0.01'))

        # Break duration
        if self.break_start and self.break_end:
            break_delta = self.break_end - self.break_start
            self.break_hours = Decimal(str(break_delta.total_seconds() / 3600)).quantize(Decimal('0.01'))
        else:
            self.break_hours = Decimal('0.00')

        # Worked hours = total - breaks
        self.worked_hours = self.total_hours - self.break_hours

        return self.worked_hours

    def save(self, *args, **kwargs):
        """Calculate hours before saving if shift is complete."""
        if self.clock_out:
            self.calculate_hours()
        super().save(*args, **kwargs)

    @classmethod
    def clock_in_employee(cls, employee, branch=None):
        """
        Clock in an employee.
        Returns the new shift or raises exception if already clocked in.
        """
        if employee.is_clocked_in():
            raise ValueError(f"El empleado {employee.full_name} ya tiene un turno abierto")

        branch = branch or employee.branch

        shift = cls.objects.create(
            employee=employee,
            branch=branch,
            clock_in=timezone.now()
        )

        return shift

    @classmethod
    def clock_out_employee(cls, employee, notes=''):
        """
        Clock out an employee.
        Returns the completed shift or raises exception if not clocked in.
        """
        current_shift = employee.get_current_shift()

        if not current_shift:
            raise ValueError(f"El empleado {employee.full_name} no tiene un turno abierto")

        current_shift.clock_out = timezone.now()
        current_shift.notes = notes
        current_shift.save()

        return current_shift
