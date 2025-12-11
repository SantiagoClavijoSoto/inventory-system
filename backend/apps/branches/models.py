"""
Branch model for multi-location support.
"""
from django.db import models
from core.mixins import AuditMixin, SoftDeleteMixin, ActiveManager


class Branch(AuditMixin, SoftDeleteMixin):
    """Branch/Location model for multi-store support."""

    name = models.CharField(max_length=100, verbose_name='Nombre')
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
        help_text='Código único de la sucursal (ej: SUC001)'
    )
    address = models.TextField(blank=True, verbose_name='Dirección')
    city = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    state = models.CharField(max_length=100, blank=True, verbose_name='Estado')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='Código Postal')
    country = models.CharField(max_length=100, default='México', verbose_name='País')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Email')

    # Manager info
    manager_name = models.CharField(max_length=150, blank=True, verbose_name='Nombre del gerente')
    manager_phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono del gerente')

    # Status
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    is_main = models.BooleanField(
        default=False,
        verbose_name='Sucursal principal',
        help_text='Indica si es la sucursal principal/matriz'
    )

    # Operational settings
    opening_time = models.TimeField(null=True, blank=True, verbose_name='Hora de apertura')
    closing_time = models.TimeField(null=True, blank=True, verbose_name='Hora de cierre')

    # Managers
    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        db_table = 'branches'
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_address(self):
        """Return formatted full address."""
        parts = [self.address, self.city, self.state, self.postal_code, self.country]
        return ', '.join(filter(None, parts))

    def save(self, *args, **kwargs):
        # Ensure only one main branch
        if self.is_main:
            Branch.objects.filter(is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)
