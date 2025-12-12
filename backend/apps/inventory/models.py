from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from core.mixins import TimestampMixin, SoftDeleteMixin, ActiveManager


class Category(TimestampMixin, SoftDeleteMixin, models.Model):
    """
    Product categories with hierarchical structure (parent-child).
    Allows organizing products into nested categories.
    """
    # Multi-tenant: company association
    # NOTE: nullable=True for initial migration, should be required in production
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='categories',
        verbose_name='Empresa'
    )

    name = models.CharField(max_length=100, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Categoría padre'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    # Managers
    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def full_path(self) -> str:
        """Returns the full category path (e.g., 'Electronics > Phones > Smartphones')"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)

    def get_descendants(self):
        """Returns all descendant categories (non-deleted only)"""
        # Use filter on related manager since children is a RelatedManager
        active_children = self.children.filter(is_deleted=False)
        descendants = list(active_children)
        for child in active_children:
            descendants.extend(child.get_descendants())
        return descendants


class Product(TimestampMixin, SoftDeleteMixin, models.Model):
    """
    Product catalog with barcode support and pricing.
    """
    UNIT_CHOICES = [
        ('unit', 'Unidad'),
        ('kg', 'Kilogramo'),
        ('g', 'Gramo'),
        ('l', 'Litro'),
        ('ml', 'Mililitro'),
        ('m', 'Metro'),
        ('box', 'Caja'),
        ('pack', 'Paquete'),
    ]

    # Multi-tenant: company association
    # NOTE: nullable=True for initial migration, should be required in production
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Empresa'
    )

    # Basic info
    name = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='SKU',
        help_text='Código interno único del producto'
    )
    barcode = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Código de barras',
        help_text='EAN-13, UPC o código interno'
    )

    # Classification
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='Categoría'
    )

    # Pricing
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio de costo'
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Precio de venta'
    )

    # Inventory settings
    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default='unit',
        verbose_name='Unidad de medida'
    )
    min_stock = models.PositiveIntegerField(
        default=10,
        verbose_name='Stock mínimo',
        help_text='Nivel de alerta para stock bajo'
    )
    max_stock = models.PositiveIntegerField(
        default=100,
        verbose_name='Stock máximo',
        help_text='Nivel máximo sugerido de stock'
    )

    # Media
    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True,
        verbose_name='Imagen'
    )

    # Status
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    is_sellable = models.BooleanField(
        default=True,
        verbose_name='Disponible para venta'
    )

    # Supplier reference
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Proveedor principal'
    )

    # Managers
    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def profit_margin(self) -> Decimal:
        """Calculate profit margin percentage"""
        if self.cost_price > 0:
            return ((self.sale_price - self.cost_price) / self.cost_price) * 100
        return Decimal('0')

    def get_stock_for_branch(self, branch_id: int) -> int:
        """Get current stock quantity for a specific branch"""
        try:
            branch_stock = self.branch_stocks.get(branch_id=branch_id)
            return branch_stock.quantity
        except BranchStock.DoesNotExist:
            return 0

    def get_total_stock(self) -> int:
        """Get total stock across all branches"""
        return self.branch_stocks.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0


class BranchStock(TimestampMixin, models.Model):
    """
    Stock levels per product per branch.
    Tracks inventory quantity at each location.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='branch_stocks',
        verbose_name='Producto'
    )
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        related_name='product_stocks',
        verbose_name='Sucursal'
    )
    quantity = models.IntegerField(
        default=0,
        verbose_name='Cantidad',
        help_text='Stock actual disponible'
    )
    reserved_quantity = models.IntegerField(
        default=0,
        verbose_name='Cantidad reservada',
        help_text='Cantidad reservada para órdenes pendientes'
    )

    class Meta:
        verbose_name = 'Stock de sucursal'
        verbose_name_plural = 'Stock de sucursales'
        unique_together = ['product', 'branch']
        indexes = [
            models.Index(fields=['product', 'branch']),
        ]

    def __str__(self):
        return f"{self.product.name} @ {self.branch.name}: {self.quantity}"

    @property
    def available_quantity(self) -> int:
        """Quantity available for sale (total - reserved)"""
        return max(0, self.quantity - self.reserved_quantity)

    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below minimum level"""
        return self.quantity <= self.product.min_stock

    @property
    def is_out_of_stock(self) -> bool:
        """Check if product is out of stock"""
        return self.available_quantity <= 0


class StockMovement(TimestampMixin, models.Model):
    """
    Records all stock movements for audit trail.
    Tracks entries, exits, transfers, and adjustments.
    """
    MOVEMENT_TYPES = [
        ('purchase', 'Compra'),
        ('sale', 'Venta'),
        ('transfer_in', 'Transferencia entrada'),
        ('transfer_out', 'Transferencia salida'),
        ('adjustment_in', 'Ajuste entrada'),
        ('adjustment_out', 'Ajuste salida'),
        ('return_customer', 'Devolución cliente'),
        ('return_supplier', 'Devolución proveedor'),
        ('damage', 'Daño/Pérdida'),
        ('initial', 'Inventario inicial'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name='Producto'
    )
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name='Sucursal'
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
        verbose_name='Tipo de movimiento'
    )
    quantity = models.IntegerField(
        verbose_name='Cantidad',
        help_text='Positivo para entradas, negativo para salidas'
    )
    previous_quantity = models.IntegerField(
        verbose_name='Cantidad anterior'
    )
    new_quantity = models.IntegerField(
        verbose_name='Cantidad nueva'
    )

    # Reference to related transaction
    reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Referencia',
        help_text='Número de factura, orden, etc.'
    )

    # Transfer specific fields
    related_branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_movements',
        verbose_name='Sucursal relacionada',
        help_text='Para transferencias: sucursal origen/destino'
    )

    # Audit
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name='Creado por'
    )

    class Meta:
        verbose_name = 'Movimiento de stock'
        verbose_name_plural = 'Movimientos de stock'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'branch', '-created_at']),
            models.Index(fields=['movement_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()}: {self.product.name} ({self.quantity})"


class StockAlert(TimestampMixin, models.Model):
    """
    Configuration for stock alerts per product or category.
    Allows customizing alert thresholds.
    """
    ALERT_TYPES = [
        ('low_stock', 'Stock bajo'),
        ('out_of_stock', 'Sin stock'),
        ('overstock', 'Exceso de stock'),
        ('expiring', 'Por vencer'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name='Producto'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name='Categoría'
    )
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='stock_alerts',
        verbose_name='Sucursal'
    )
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPES,
        verbose_name='Tipo de alerta'
    )
    threshold = models.PositiveIntegerField(
        verbose_name='Umbral',
        help_text='Cantidad que activa la alerta'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    notify_email = models.BooleanField(
        default=True,
        verbose_name='Notificar por email'
    )

    class Meta:
        verbose_name = 'Alerta de stock'
        verbose_name_plural = 'Alertas de stock'

    def __str__(self):
        target = self.product.name if self.product else self.category.name
        return f"{self.get_alert_type_display()}: {target}"
