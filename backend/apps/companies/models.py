"""
Company model for multi-tenant architecture.
Each company represents an independent business using the platform.
"""
from django.db import models
from django.conf import settings

from core.mixins import TimestampMixin, SoftDeleteMixin, ActiveManager


class Company(TimestampMixin, SoftDeleteMixin):
    """
    Represents a tenant/business on the platform.
    All data is scoped to a company for multi-tenant isolation.
    """
    PLAN_CHOICES = [
        ('free', 'Gratuito'),
        ('basic', 'Básico'),
        ('professional', 'Profesional'),
        ('enterprise', 'Empresarial'),
    ]

    # Identification
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre de empresa'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Identificador único',
        help_text='Identificador URL-friendly (ej: mi-empresa)'
    )
    legal_name = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Razón social'
    )
    tax_id = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='RFC',
        help_text='Registro Federal de Contribuyentes'
    )

    # Branding (default for branches)
    logo = models.ImageField(
        upload_to='companies/logos/',
        null=True,
        blank=True,
        verbose_name='Logo'
    )
    primary_color = models.CharField(
        max_length=7,
        default='#2563eb',
        verbose_name='Color primario',
        help_text='Color hexadecimal (ej: #2563eb)'
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#64748b',
        verbose_name='Color secundario'
    )

    # Contact
    email = models.EmailField(
        verbose_name='Email corporativo'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    website = models.URLField(
        blank=True,
        verbose_name='Sitio web'
    )
    address = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )

    # Subscription/Limits
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='free',
        verbose_name='Plan'
    )
    max_branches = models.PositiveIntegerField(
        default=1,
        verbose_name='Máximo de sucursales'
    )
    max_users = models.PositiveIntegerField(
        default=5,
        verbose_name='Máximo de usuarios'
    )
    max_products = models.PositiveIntegerField(
        default=100,
        verbose_name='Máximo de productos'
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )

    # Owner (first admin who created the company)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='owned_companies',
        verbose_name='Propietario'
    )

    # Managers
    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'companies'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return self.name

    @property
    def branch_count(self):
        """Get number of branches for this company."""
        return self.branches.filter(is_deleted=False).count()

    @property
    def user_count(self):
        """Get number of users for this company."""
        return self.users.filter(is_active=True).count()

    @property
    def product_count(self):
        """Get number of products for this company."""
        return self.products.filter(is_deleted=False).count()

    def can_add_branch(self):
        """Check if company can add more branches."""
        return self.branch_count < self.max_branches

    def can_add_user(self):
        """Check if company can add more users."""
        return self.user_count < self.max_users

    def can_add_product(self):
        """Check if company can add more products."""
        return self.product_count < self.max_products

    def get_plan_limits(self):
        """Get plan limits as dictionary."""
        return {
            'max_branches': self.max_branches,
            'max_users': self.max_users,
            'max_products': self.max_products,
            'current_branches': self.branch_count,
            'current_users': self.user_count,
            'current_products': self.product_count,
        }


class Subscription(TimestampMixin):
    """
    Tracks subscription/billing information for companies.
    Separated from Company to allow subscription history and flexibility.
    """
    STATUS_CHOICES = [
        ('trial', 'Prueba'),
        ('active', 'Activa'),
        ('past_due', 'Vencida'),
        ('cancelled', 'Cancelada'),
        ('suspended', 'Suspendida'),
    ]

    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('semiannual', 'Semestral'),
        ('annual', 'Anual'),
    ]

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='Empresa'
    )
    plan = models.CharField(
        max_length=20,
        choices=Company.PLAN_CHOICES,
        default='free',
        verbose_name='Plan'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial',
        verbose_name='Estado'
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE_CHOICES,
        default='monthly',
        verbose_name='Ciclo de facturación'
    )
    start_date = models.DateField(
        verbose_name='Fecha de inicio'
    )
    next_payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Próximo pago'
    )
    trial_ends_at = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fin de prueba'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Monto'
    )
    currency = models.CharField(
        max_length=3,
        default='MXN',
        verbose_name='Moneda'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )

    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'

    def __str__(self):
        return f"{self.company.name} - {self.plan} ({self.status})"

    @property
    def is_active(self):
        """Check if subscription is in an active state."""
        return self.status in ('trial', 'active')

    @property
    def days_until_payment(self):
        """Calculate days until next payment."""
        if not self.next_payment_date:
            return None
        from datetime import date
        delta = self.next_payment_date - date.today()
        return delta.days
