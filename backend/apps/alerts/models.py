"""
Alert models for system notifications and warnings.
Handles alerts generation, tracking, and user preferences.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from core.mixins import TimestampMixin


class Alert(TimestampMixin, models.Model):
    """
    System-generated alert for various events.
    Tracks stock levels, anomalies, and important notifications.
    Multi-tenant: alerts belong to a specific company.
    """
    # Multi-tenant: company association
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name='Empresa'
    )

    ALERT_TYPE_CHOICES = [
        # Company-level alerts (for company admins)
        ('low_stock', 'Stock bajo'),
        ('out_of_stock', 'Sin stock'),
        ('overstock', 'Exceso de stock'),
        ('cash_difference', 'Diferencia de caja'),
        ('high_void_rate', 'Alta tasa de anulaciones'),
        ('sales_anomaly', 'Anomalía en ventas'),
        ('shift_overtime', 'Turno extendido'),
        ('system', 'Sistema'),
        # Platform-level alerts (for superadmin) - Subscription related
        ('subscription_payment_due', 'Pago próximo'),
        ('subscription_overdue', 'Pago vencido'),
        ('subscription_trial_ending', 'Prueba por terminar'),
        ('subscription_cancelled', 'Suscripción cancelada'),
        ('subscription_suspended', 'Suscripción suspendida'),
        ('new_subscription', 'Nueva suscripción'),
        ('subscription_plan_changed', 'Cambio de plan'),
        # Platform-level alerts (for superadmin) - Business health
        ('high_churn_rate', 'Alta tasa de cancelaciones'),
        ('revenue_anomaly', 'Anomalía en ingresos'),
        ('low_platform_activity', 'Baja actividad en plataforma'),
        # Platform-level alerts (for superadmin) - Tenant health
        ('tenant_limit_approaching', 'Tenant cerca del límite'),
        ('tenant_inactive', 'Tenant inactivo'),
        ('onboarding_stalled', 'Onboarding detenido'),
        # Platform-level alerts (for superadmin) - System health
        ('high_error_rate', 'Alta tasa de errores'),
        ('system_performance', 'Rendimiento del sistema'),
    ]

    # Alert types that are platform-level (not company-specific)
    PLATFORM_ALERT_TYPES = [
        # Subscription related
        'subscription_payment_due',
        'subscription_overdue',
        'subscription_trial_ending',
        'subscription_cancelled',
        'subscription_suspended',
        'new_subscription',
        'subscription_plan_changed',
        # Business health
        'high_churn_rate',
        'revenue_anomaly',
        'low_platform_activity',
        # Tenant health
        'tenant_limit_approaching',
        'tenant_inactive',
        'onboarding_stalled',
        # System health
        'high_error_rate',
        'system_performance',
    ]

    SEVERITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]

    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('acknowledged', 'Reconocida'),
        ('resolved', 'Resuelta'),
        ('dismissed', 'Descartada'),
    ]

    # Alert info
    alert_type = models.CharField(
        max_length=30,
        choices=ALERT_TYPE_CHOICES,
        verbose_name='Tipo de alerta'
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='medium',
        verbose_name='Severidad'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    message = models.TextField(
        verbose_name='Mensaje'
    )

    # Related objects (optional, based on alert type)
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name='Sucursal'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='system_alerts',
        verbose_name='Producto'
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name='Empleado'
    )
    subscription = models.ForeignKey(
        'companies.Subscription',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name='Suscripción'
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Estado'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Leída'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de lectura'
    )
    read_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts_read',
        verbose_name='Leída por'
    )

    # Resolution
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de resolución'
    )
    resolved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts_resolved',
        verbose_name='Resuelta por'
    )
    resolution_notes = models.TextField(
        blank=True,
        verbose_name='Notas de resolución'
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadatos',
        help_text='Datos adicionales específicos del tipo de alerta'
    )

    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['company', 'alert_type', '-created_at']),
            models.Index(fields=['company', 'status', '-created_at']),
            models.Index(fields=['company', 'severity', '-created_at']),
            models.Index(fields=['company', 'is_read', '-created_at']),
            models.Index(fields=['branch', '-created_at']),
            # Platform-level alert index (subscription alerts)
            models.Index(fields=['alert_type', 'status', '-created_at']),
            models.Index(fields=['subscription', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"

    @property
    def is_platform_alert(self) -> bool:
        """Check if this alert is a platform-level alert (for superadmin)."""
        return self.alert_type in self.PLATFORM_ALERT_TYPES

    def mark_as_read(self, user):
        """Mark alert as read by a user."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.read_by = user
            self.save(update_fields=['is_read', 'read_at', 'read_by', 'updated_at'])

    def acknowledge(self, user):
        """Acknowledge the alert."""
        self.status = 'acknowledged'
        self.mark_as_read(user)

    def resolve(self, user, notes=''):
        """Resolve the alert."""
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.read_by = user
        self.save()

    def dismiss(self, user):
        """Dismiss the alert without resolution."""
        self.status = 'dismissed'
        self.mark_as_read(user)


class AlertConfiguration(TimestampMixin, models.Model):
    """
    Configuration for alert thresholds and preferences.
    Can be set globally, per branch, or per product category.
    Multi-tenant: configurations belong to a specific company.
    """
    # Multi-tenant: company association
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alert_configurations',
        verbose_name='Empresa'
    )

    SCOPE_CHOICES = [
        ('global', 'Global'),
        ('branch', 'Por sucursal'),
        ('category', 'Por categoría'),
    ]

    # Scope
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='global',
        verbose_name='Alcance'
    )
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alert_configurations',
        verbose_name='Sucursal'
    )
    category = models.ForeignKey(
        'inventory.Category',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alert_configurations',
        verbose_name='Categoría'
    )

    # Stock thresholds
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        verbose_name='Umbral stock bajo',
        help_text='Porcentaje del stock mínimo configurado en producto'
    )
    overstock_threshold = models.PositiveIntegerField(
        default=150,
        verbose_name='Umbral exceso de stock',
        help_text='Porcentaje del stock máximo configurado en producto'
    )

    # Cash register thresholds
    cash_difference_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('100.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Umbral diferencia de caja',
        help_text='Diferencia mínima para generar alerta'
    )

    # Void rate threshold
    void_rate_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Umbral tasa de anulaciones (%)',
        help_text='Porcentaje de anulaciones para generar alerta'
    )

    # Shift overtime threshold (hours)
    overtime_threshold = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal('10.0'),
        validators=[MinValueValidator(Decimal('0.0'))],
        verbose_name='Umbral horas extra',
        help_text='Horas de turno para generar alerta de turno extendido'
    )

    # Notification preferences
    email_notifications = models.BooleanField(
        default=True,
        verbose_name='Notificaciones por email'
    )
    dashboard_notifications = models.BooleanField(
        default=True,
        verbose_name='Notificaciones en dashboard'
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )

    class Meta:
        verbose_name = 'Configuración de alertas'
        verbose_name_plural = 'Configuraciones de alertas'
        unique_together = [
            ['scope', 'branch'],
            ['scope', 'category'],
        ]

    def __str__(self):
        if self.scope == 'branch' and self.branch:
            return f"Config alertas: {self.branch.name}"
        elif self.scope == 'category' and self.category:
            return f"Config alertas: {self.category.name}"
        return "Config alertas: Global"


class UserAlertPreference(TimestampMixin, models.Model):
    """
    User-specific alert preferences.
    Controls which alerts a user wants to receive.
    """
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='alert_preferences',
        verbose_name='Usuario'
    )

    # Alert type preferences
    receive_low_stock = models.BooleanField(
        default=True,
        verbose_name='Recibir alertas de stock bajo'
    )
    receive_out_of_stock = models.BooleanField(
        default=True,
        verbose_name='Recibir alertas de sin stock'
    )
    receive_cash_difference = models.BooleanField(
        default=True,
        verbose_name='Recibir alertas de diferencia de caja'
    )
    receive_void_alerts = models.BooleanField(
        default=True,
        verbose_name='Recibir alertas de anulaciones'
    )
    receive_shift_alerts = models.BooleanField(
        default=True,
        verbose_name='Recibir alertas de turnos'
    )
    receive_system_alerts = models.BooleanField(
        default=True,
        verbose_name='Recibir alertas del sistema'
    )
    # Platform-level alerts (for superadmin)
    receive_subscription_alerts = models.BooleanField(
        default=True,
        verbose_name='Recibir alertas de suscripciones'
    )

    # Severity filter
    minimum_severity = models.CharField(
        max_length=20,
        choices=Alert.SEVERITY_CHOICES,
        default='low',
        verbose_name='Severidad mínima',
        help_text='Solo recibir alertas de esta severidad o mayor'
    )

    # Email digest
    email_digest = models.BooleanField(
        default=False,
        verbose_name='Resumen por email',
        help_text='Enviar resumen diario en lugar de alertas individuales'
    )

    class Meta:
        verbose_name = 'Preferencia de alertas'
        verbose_name_plural = 'Preferencias de alertas'

    def __str__(self):
        return f"Preferencias de {self.user.email}"


class ActivityLog(TimestampMixin, models.Model):
    """
    Registro de actividades de usuarios para notificaciones a administradores.
    Captura acciones importantes realizadas por empleados y admins.
    Multi-tenant: logs pertenecen a una empresa específica.
    """
    # Multi-tenant: company association (REQUIRED)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name='Empresa'
    )

    # Tipos de acciones agrupados por módulo
    ACTION_CHOICES = [
        # Inventario
        ('product_created', 'Producto creado'),
        ('product_updated', 'Producto modificado'),
        ('product_deleted', 'Producto eliminado'),
        ('stock_adjusted', 'Ajuste de stock'),
        ('stock_transferred', 'Transferencia de stock'),
        # Ventas
        ('sale_created', 'Venta realizada'),
        ('sale_voided', 'Venta anulada'),
        ('cash_register_opened', 'Caja abierta'),
        ('cash_register_closed', 'Caja cerrada'),
        # Empleados
        ('employee_created', 'Empleado creado'),
        ('employee_updated', 'Empleado modificado'),
        ('shift_started', 'Turno iniciado'),
        ('shift_ended', 'Turno finalizado'),
        # Sucursales
        ('branch_created', 'Sucursal creada'),
        ('branch_updated', 'Sucursal modificada'),
        # Usuarios
        ('user_created', 'Usuario creado'),
        ('user_updated', 'Usuario modificado'),
        ('role_changed', 'Rol cambiado'),
        # Proveedores
        ('supplier_created', 'Proveedor creado'),
        ('supplier_updated', 'Proveedor modificado'),
        ('purchase_order_created', 'Orden de compra creada'),
    ]

    # Módulos para filtrado
    MODULE_CHOICES = [
        ('inventory', 'Inventario'),
        ('sales', 'Ventas'),
        ('employees', 'Empleados'),
        ('branches', 'Sucursales'),
        ('users', 'Usuarios'),
        ('suppliers', 'Proveedores'),
    ]

    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name='Acción'
    )

    module = models.CharField(
        max_length=20,
        choices=MODULE_CHOICES,
        verbose_name='Módulo',
        db_index=True
    )

    # Usuario que realizó la acción
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs',
        verbose_name='Usuario'
    )

    # Nombre del usuario (guardado para mantener historial si se elimina)
    user_name = models.CharField(
        max_length=300,
        verbose_name='Nombre del usuario'
    )

    # Sucursal donde ocurrió (opcional)
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name='Sucursal'
    )

    # Descripción legible de la acción
    description = models.CharField(
        max_length=500,
        verbose_name='Descripción'
    )

    # Referencia genérica al objeto afectado
    target_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Tipo de objeto',
        help_text='Nombre del modelo afectado (ej: Product, Sale)'
    )

    target_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='ID del objeto'
    )

    target_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nombre del objeto',
        help_text='Nombre descriptivo del objeto afectado'
    )

    # Metadata adicional en JSON (cambios específicos, valores anteriores, etc)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadatos',
        help_text='Datos adicionales como cambios realizados, valores anteriores/nuevos'
    )

    # Control de lectura por admins
    is_read = models.BooleanField(
        default=False,
        verbose_name='Leído',
        db_index=True
    )

    read_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='read_activity_logs',
        verbose_name='Leído por'
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de lectura'
    )

    class Meta:
        verbose_name = 'Registro de actividad'
        verbose_name_plural = 'Registros de actividad'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['company', 'module', '-created_at']),
            models.Index(fields=['company', 'is_read', '-created_at']),
            models.Index(fields=['company', 'user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user_name}: {self.description}"

    @classmethod
    def get_module_for_action(cls, action: str) -> str:
        """Devuelve el módulo correspondiente a una acción."""
        module_mapping = {
            'product_created': 'inventory',
            'product_updated': 'inventory',
            'product_deleted': 'inventory',
            'stock_adjusted': 'inventory',
            'stock_transferred': 'inventory',
            'sale_created': 'sales',
            'sale_voided': 'sales',
            'cash_register_opened': 'sales',
            'cash_register_closed': 'sales',
            'employee_created': 'employees',
            'employee_updated': 'employees',
            'shift_started': 'employees',
            'shift_ended': 'employees',
            'branch_created': 'branches',
            'branch_updated': 'branches',
            'user_created': 'users',
            'user_updated': 'users',
            'role_changed': 'users',
            'supplier_created': 'suppliers',
            'supplier_updated': 'suppliers',
            'purchase_order_created': 'suppliers',
        }
        return module_mapping.get(action, 'inventory')
