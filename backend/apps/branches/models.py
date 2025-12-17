"""
Branch model for multi-location support.
"""
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.mixins import AuditMixin, SoftDeleteMixin, ActiveManager


class Branch(AuditMixin, SoftDeleteMixin):
    """Branch/Location model for multi-store support."""

    # Multi-tenant: company association
    # NOTE: nullable=True for initial migration, should be required in production
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='branches',
        verbose_name='Empresa'
    )

    name = models.CharField(max_length=100, verbose_name='Nombre')
    code = models.CharField(
        max_length=20,
        verbose_name='Código',
        help_text='Código único de la sucursal por empresa (ej: SUC001)'
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

    # Branding / White-label
    store_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Nombre de la tienda',
        help_text='Nombre comercial que se muestra en la interfaz'
    )
    logo = models.ImageField(
        upload_to='branches/logos/',
        blank=True,
        null=True,
        verbose_name='Logo',
        help_text='Logo de la tienda (recomendado: 200x200px)'
    )
    favicon = models.ImageField(
        upload_to='branches/favicons/',
        blank=True,
        null=True,
        verbose_name='Favicon',
        help_text='Icono de la pestaña del navegador (recomendado: 32x32px)'
    )
    primary_color = models.CharField(
        max_length=7,
        default='#2563eb',
        verbose_name='Color primario',
        help_text='Color principal en formato hexadecimal (ej: #2563eb)'
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#64748b',
        verbose_name='Color secundario',
        help_text='Color secundario en formato hexadecimal'
    )
    accent_color = models.CharField(
        max_length=7,
        default='#f59e0b',
        blank=True,
        verbose_name='Color de acento',
        help_text='Color de acento para destacar elementos'
    )

    # Business configuration
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('16.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name='Tasa de impuesto (%)',
        help_text='Porcentaje de impuesto aplicado a las ventas'
    )
    currency = models.CharField(
        max_length=3,
        default='MXN',
        verbose_name='Moneda',
        help_text='Código de moneda ISO 4217 (ej: MXN, USD, EUR)'
    )
    currency_symbol = models.CharField(
        max_length=5,
        default='$',
        verbose_name='Símbolo de moneda',
        help_text='Símbolo a mostrar antes de los precios'
    )
    receipt_header = models.TextField(
        blank=True,
        verbose_name='Encabezado de recibo',
        help_text='Texto que aparece en la parte superior de los recibos'
    )
    receipt_footer = models.TextField(
        blank=True,
        verbose_name='Pie de recibo',
        help_text='Texto que aparece en la parte inferior de los recibos (ej: políticas de devolución)'
    )

    # Managers
    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        db_table = 'branches'
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'code'],
                name='unique_branch_code_per_company'
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_address(self):
        """Return formatted full address."""
        parts = [self.address, self.city, self.state, self.postal_code, self.country]
        return ', '.join(filter(None, parts))

    @property
    def display_name(self):
        """Return store_name if set, otherwise branch name."""
        return self.store_name or self.name

    @property
    def logo_url(self):
        """Return logo URL if exists."""
        if self.logo:
            return self.logo.url
        return None

    @property
    def favicon_url(self):
        """Return favicon URL if exists."""
        if self.favicon:
            return self.favicon.url
        return None

    def save(self, *args, **kwargs):
        # Ensure only one main branch per company (multi-tenant safe)
        if self.is_main and self.company_id:
            Branch.objects.filter(
                company_id=self.company_id,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)
