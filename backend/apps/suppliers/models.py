from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from core.mixins import TimestampMixin, SoftDeleteMixin, ActiveManager


class Supplier(TimestampMixin, SoftDeleteMixin, models.Model):
    """
    Supplier/vendor information for products.
    """
    # Multi-tenant: company association
    # NOTE: nullable=True for initial migration, should be required in production
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='suppliers',
        verbose_name='Empresa'
    )

    name = models.CharField(max_length=200, verbose_name='Nombre')
    code = models.CharField(
        max_length=20,
        verbose_name='Código',
        help_text='Código único del proveedor por empresa'
    )
    contact_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Nombre de contacto'
    )
    email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    mobile = models.CharField(max_length=20, blank=True, verbose_name='Celular')

    # Address
    address = models.TextField(blank=True, verbose_name='Dirección')
    city = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    state = models.CharField(max_length=100, blank=True, verbose_name='Estado')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='Código postal')
    country = models.CharField(max_length=100, default='México', verbose_name='País')

    # Business info
    tax_id = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='RFC/NIT',
        help_text='Identificación fiscal'
    )
    website = models.URLField(blank=True, verbose_name='Sitio web')
    notes = models.TextField(blank=True, verbose_name='Notas')

    # Payment terms
    payment_terms = models.PositiveIntegerField(
        default=30,
        verbose_name='Plazo de pago (días)',
        help_text='Días de crédito'
    )
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Límite de crédito'
    )

    is_active = models.BooleanField(default=True, verbose_name='Activo')

    # Managers
    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'code'],
                name='unique_supplier_code_per_company'
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_address(self) -> str:
        """Returns formatted full address"""
        parts = filter(None, [self.address, self.city, self.state, self.postal_code, self.country])
        return ', '.join(parts)


class PurchaseOrder(TimestampMixin, models.Model):
    """
    Purchase orders to suppliers.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('ordered', 'Ordenada'),
        ('partial', 'Parcialmente recibida'),
        ('received', 'Recibida'),
        ('cancelled', 'Cancelada'),
    ]

    order_number = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Número de orden'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name='Proveedor'
    )
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name='Sucursal destino'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Estado'
    )

    # Dates
    order_date = models.DateField(null=True, blank=True, verbose_name='Fecha de orden')
    expected_date = models.DateField(null=True, blank=True, verbose_name='Fecha esperada')
    received_date = models.DateField(null=True, blank=True, verbose_name='Fecha de recepción')

    # Totals
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Subtotal'
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Impuestos'
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total'
    )

    notes = models.TextField(blank=True, verbose_name='Notas')

    # Audit
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='purchase_orders_created',
        verbose_name='Creado por'
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders_approved',
        verbose_name='Aprobado por'
    )
    received_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders_received',
        verbose_name='Recibido por'
    )

    class Meta:
        verbose_name = 'Orden de compra'
        verbose_name_plural = 'Órdenes de compra'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.supplier.name}"

    def calculate_totals(self):
        """Recalculate order totals from items"""
        from django.db.models import Sum
        totals = self.items.aggregate(
            subtotal=Sum('subtotal')
        )
        self.subtotal = totals['subtotal'] or Decimal('0.00')
        self.tax = self.subtotal * Decimal('0.19')  # 19% IVA Colombia
        self.total = self.subtotal + self.tax
        self.save()


class PurchaseOrderItem(TimestampMixin, models.Model):
    """
    Individual items in a purchase order.
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Orden de compra'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        related_name='purchase_order_items',
        verbose_name='Producto'
    )
    quantity_ordered = models.PositiveIntegerField(verbose_name='Cantidad ordenada')
    quantity_received = models.PositiveIntegerField(
        default=0,
        verbose_name='Cantidad recibida'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Precio unitario'
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Subtotal'
    )

    class Meta:
        verbose_name = 'Item de orden de compra'
        verbose_name_plural = 'Items de orden de compra'

    def __str__(self):
        return f"{self.product.name} x {self.quantity_ordered}"

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity_ordered
        super().save(*args, **kwargs)

    @property
    def is_fully_received(self) -> bool:
        return self.quantity_received >= self.quantity_ordered

    @property
    def pending_quantity(self) -> int:
        return max(0, self.quantity_ordered - self.quantity_received)
