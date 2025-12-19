"""
User-written report models.
Text-based reports with category, status workflow, and priority levels.
"""
from django.db import models
from django.conf import settings
from core.mixins import TimestampMixin


class UserReport(TimestampMixin, models.Model):
    """
    User-written report for issues, suggestions, or observations.
    Multi-tenant: reports belong to a specific company.
    """

    CATEGORY_CHOICES = [
        ('inventario', 'Inventario'),
        ('empleados', 'Empleados'),
        ('sucursales', 'Sucursales'),
    ]

    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En revisión'),
        ('resuelto', 'Resuelto'),
    ]

    PRIORITY_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    # Multi-tenant
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='user_reports',
        verbose_name='Empresa'
    )

    # Report content (TEXT ONLY)
    title = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    description = models.TextField(
        verbose_name='Descripción'
    )

    # Classification
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='Categoría'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='media',
        verbose_name='Prioridad'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )

    # Creator tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_created',
        verbose_name='Creado por'
    )

    # Assignment (for admin reports on 'empleados' category)
    assign_to_all = models.BooleanField(
        default=False,
        verbose_name='Asignar a todos'
    )
    assigned_employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        related_name='assigned_reports',
        verbose_name='Empleados asignados'
    )

    # Status change tracking
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de revisión'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_reviewed',
        verbose_name='Revisado por'
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de resolución'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_resolved',
        verbose_name='Resuelto por'
    )
    resolution_notes = models.TextField(
        blank=True,
        default='',
        verbose_name='Notas de resolución'
    )

    class Meta:
        verbose_name = 'Reporte de Usuario'
        verbose_name_plural = 'Reportes de Usuario'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['company', 'status', '-created_at']),
            models.Index(fields=['company', 'category', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"

    def set_in_review(self, user):
        """Move report to 'en_revision' status."""
        from django.utils import timezone
        self.status = 'en_revision'
        self.reviewed_at = timezone.now()
        self.reviewed_by = user
        self.save(update_fields=['status', 'reviewed_at', 'reviewed_by', 'updated_at'])

    def resolve(self, user, notes=''):
        """Mark report as resolved."""
        from django.utils import timezone
        self.status = 'resuelto'
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        # Also set reviewed if not already
        if not self.reviewed_at:
            self.reviewed_at = timezone.now()
            self.reviewed_by = user
        self.save()
