"""
Sales models for Point of Sale (POS) system.
Handles sale transactions and individual sale items.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from core.mixins import TimestampMixin


class Sale(TimestampMixin, models.Model):
    """
    Represents a complete sale transaction.
    Contains header info and links to individual items.
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Efectivo'),
        ('card', 'Tarjeta'),
        ('transfer', 'Transferencia'),
        ('mixed', 'Mixto'),
    ]

    STATUS_CHOICES = [
        ('completed', 'Completada'),
        ('voided', 'Anulada'),
        ('refunded', 'Reembolsada'),
    ]

    # Transaction info
    sale_number = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Número de venta',
        help_text='Identificador único de la transacción'
    )
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name='Sucursal'
    )
    cashier = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='sales_as_cashier',
        verbose_name='Cajero'
    )

    # Totals
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Subtotal'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Descuento'
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='% Descuento'
    )
    tax_amount = models.DecimalField(
        max_digits=10,
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

    # Payment
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        verbose_name='Método de pago'
    )
    amount_tendered = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto recibido',
        help_text='Cantidad entregada por el cliente'
    )
    change_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Cambio',
        help_text='Cambio devuelto al cliente'
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Referencia de pago',
        help_text='Número de tarjeta (últimos 4), referencia de transferencia, etc.'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        verbose_name='Estado'
    )

    # Void info
    voided_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de anulación'
    )
    voided_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_voided',
        verbose_name='Anulado por'
    )
    void_reason = models.TextField(
        blank=True,
        verbose_name='Razón de anulación'
    )

    # Customer info (optional)
    customer_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nombre del cliente'
    )
    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono del cliente'
    )
    customer_email = models.EmailField(
        blank=True,
        verbose_name='Email del cliente'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sale_number']),
            models.Index(fields=['branch', '-created_at']),
            models.Index(fields=['cashier', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Venta #{self.sale_number} - ${self.total}"

    @property
    def items_count(self) -> int:
        """Total number of items in the sale"""
        return self.items.count()

    @property
    def total_quantity(self) -> int:
        """Total quantity of products sold"""
        return sum(item.quantity for item in self.items.all())

    @property
    def profit(self) -> Decimal:
        """Calculate profit from this sale"""
        return sum(item.profit for item in self.items.all())

    @property
    def is_voided(self) -> bool:
        """Check if sale is voided"""
        return self.status == 'voided'

    def calculate_totals(self):
        """
        Recalculate sale totals from items.
        Call this after modifying items.
        """
        from django.db.models import Sum

        items_total = self.items.aggregate(
            subtotal=Sum('subtotal')
        )['subtotal'] or Decimal('0.00')

        self.subtotal = items_total

        # Apply discount
        if self.discount_percent > 0:
            self.discount_amount = self.subtotal * (self.discount_percent / 100)

        # Calculate tax (16% IVA by default - configurable)
        taxable_amount = self.subtotal - self.discount_amount
        self.tax_amount = taxable_amount * Decimal('0.16')

        # Final total
        self.total = taxable_amount + self.tax_amount

        # Calculate change
        if self.amount_tendered > 0:
            self.change_amount = max(Decimal('0.00'), self.amount_tendered - self.total)

    @classmethod
    def generate_sale_number(cls, branch_code: str) -> str:
        """
        Generate a unique sale number.
        Format: BRANCH-YYYYMMDD-XXXX
        """
        from django.utils import timezone
        from django.db.models import Max

        today = timezone.now().date()
        prefix = f"{branch_code}-{today.strftime('%Y%m%d')}"

        # Get the last sale number for today at this branch
        last_sale = cls.objects.filter(
            sale_number__startswith=prefix
        ).aggregate(Max('sale_number'))['sale_number__max']

        if last_sale:
            # Extract sequence number and increment
            try:
                sequence = int(last_sale.split('-')[-1]) + 1
            except (ValueError, IndexError):
                sequence = 1
        else:
            sequence = 1

        return f"{prefix}-{sequence:04d}"


class SaleItem(TimestampMixin, models.Model):
    """
    Individual line item in a sale.
    Records product, quantity, price at time of sale.
    """
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Venta'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        related_name='sale_items',
        verbose_name='Producto'
    )

    # Quantity and pricing (captured at time of sale)
    quantity = models.PositiveIntegerField(
        verbose_name='Cantidad',
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio unitario',
        help_text='Precio de venta al momento de la transacción'
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio de costo',
        help_text='Costo al momento de la transacción (para cálculo de ganancia)'
    )

    # Item-level discount
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Descuento'
    )

    # Calculated subtotal
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Subtotal'
    )

    # Snapshot of product info at time of sale
    product_name = models.CharField(
        max_length=200,
        verbose_name='Nombre del producto',
        help_text='Nombre capturado al momento de la venta'
    )
    product_sku = models.CharField(
        max_length=50,
        verbose_name='SKU',
        help_text='SKU capturado al momento de la venta'
    )

    class Meta:
        verbose_name = 'Item de venta'
        verbose_name_plural = 'Items de venta'
        ordering = ['id']

    def __str__(self):
        return f"{self.product_name} x {self.quantity} = ${self.subtotal}"

    @property
    def profit(self) -> Decimal:
        """Calculate profit for this item"""
        return (self.unit_price - self.cost_price) * self.quantity - self.discount_amount

    @property
    def profit_margin(self) -> Decimal:
        """Calculate profit margin percentage for this item"""
        if self.cost_price > 0:
            return ((self.unit_price - self.cost_price) / self.cost_price) * 100
        return Decimal('0')

    def save(self, *args, **kwargs):
        """Calculate subtotal before saving"""
        self.subtotal = (self.unit_price * self.quantity) - self.discount_amount
        super().save(*args, **kwargs)


class DailyCashRegister(TimestampMixin, models.Model):
    """
    Daily cash register record for a branch.
    Tracks opening/closing balance and transactions.
    """
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.PROTECT,
        related_name='cash_registers',
        verbose_name='Sucursal'
    )
    date = models.DateField(
        verbose_name='Fecha'
    )

    # Opening
    opening_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto de apertura'
    )
    opened_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='registers_opened',
        verbose_name='Abierto por'
    )
    opened_at = models.DateTimeField(
        verbose_name='Hora de apertura'
    )

    # Closing
    closing_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Monto de cierre'
    )
    closed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registers_closed',
        verbose_name='Cerrado por'
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hora de cierre'
    )

    # Calculated totals
    expected_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto esperado',
        help_text='Apertura + ventas en efectivo'
    )
    cash_sales_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total ventas en efectivo'
    )
    card_sales_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total ventas con tarjeta'
    )
    transfer_sales_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total transferencias'
    )

    # Difference
    difference = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Diferencia',
        help_text='Diferencia entre monto esperado y cierre'
    )

    # Status
    is_closed = models.BooleanField(
        default=False,
        verbose_name='Cerrada'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )

    class Meta:
        verbose_name = 'Caja diaria'
        verbose_name_plural = 'Cajas diarias'
        unique_together = ['branch', 'date']
        ordering = ['-date']

    def __str__(self):
        status = "Cerrada" if self.is_closed else "Abierta"
        return f"Caja {self.branch.name} - {self.date} ({status})"

    def calculate_totals(self):
        """Recalculate totals from sales"""
        from django.db.models import Sum

        # Get all completed sales for this branch on this date
        sales = Sale.objects.filter(
            branch=self.branch,
            created_at__date=self.date,
            status='completed'
        )

        self.cash_sales_total = sales.filter(
            payment_method='cash'
        ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')

        self.card_sales_total = sales.filter(
            payment_method='card'
        ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')

        self.transfer_sales_total = sales.filter(
            payment_method='transfer'
        ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')

        self.expected_amount = self.opening_amount + self.cash_sales_total

        if self.closing_amount is not None:
            self.difference = self.closing_amount - self.expected_amount
