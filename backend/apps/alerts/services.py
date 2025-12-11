"""
Alert generation and management services.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from django.db import transaction
from django.db.models import F, Q, Count, Sum, Avg
from django.utils import timezone

from apps.inventory.models import BranchStock, Product
from apps.sales.models import Sale, DailyCashRegister
from apps.employees.models import Shift
from apps.branches.models import Branch
from .models import Alert, AlertConfiguration, UserAlertPreference


class AlertService:
    """
    Main service for alert CRUD operations.
    """

    @staticmethod
    def get_alerts(
        user,
        branch_id: Optional[int] = None,
        alert_type: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: int = 50
    ) -> List[Alert]:
        """
        Get alerts filtered by various criteria.
        """
        queryset = Alert.objects.all()

        if branch_id:
            queryset = queryset.filter(
                Q(branch_id=branch_id) | Q(branch__isnull=True)
            )

        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)

        if status:
            queryset = queryset.filter(status=status)

        if severity:
            queryset = queryset.filter(severity=severity)

        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)

        return list(queryset.select_related(
            'branch', 'product', 'employee', 'read_by', 'resolved_by'
        ).order_by('-created_at')[:limit])

    @staticmethod
    def get_unread_count(user, branch_id: Optional[int] = None) -> dict:
        """
        Get count of unread alerts by severity.
        """
        queryset = Alert.objects.filter(is_read=False, status='active')

        if branch_id:
            queryset = queryset.filter(
                Q(branch_id=branch_id) | Q(branch__isnull=True)
            )

        counts = queryset.values('severity').annotate(count=Count('id'))
        result = {
            'total': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }

        for item in counts:
            result[item['severity']] = item['count']
            result['total'] += item['count']

        return result

    @staticmethod
    @transaction.atomic
    def mark_as_read(alert_id: int, user) -> Alert:
        """Mark a single alert as read."""
        alert = Alert.objects.select_for_update().get(id=alert_id)
        alert.mark_as_read(user)
        return alert

    @staticmethod
    @transaction.atomic
    def mark_all_as_read(user, branch_id: Optional[int] = None) -> int:
        """Mark all unread alerts as read."""
        queryset = Alert.objects.filter(is_read=False)

        if branch_id:
            queryset = queryset.filter(
                Q(branch_id=branch_id) | Q(branch__isnull=True)
            )

        now = timezone.now()
        count = queryset.update(
            is_read=True,
            read_at=now,
            read_by=user,
            updated_at=now
        )
        return count

    @staticmethod
    @transaction.atomic
    def acknowledge_alert(alert_id: int, user) -> Alert:
        """Acknowledge an alert."""
        alert = Alert.objects.select_for_update().get(id=alert_id)
        alert.acknowledge(user)
        return alert

    @staticmethod
    @transaction.atomic
    def resolve_alert(alert_id: int, user, notes: str = '') -> Alert:
        """Resolve an alert."""
        alert = Alert.objects.select_for_update().get(id=alert_id)
        alert.resolve(user, notes)
        return alert

    @staticmethod
    @transaction.atomic
    def dismiss_alert(alert_id: int, user) -> Alert:
        """Dismiss an alert."""
        alert = Alert.objects.select_for_update().get(id=alert_id)
        alert.dismiss(user)
        return alert

    @staticmethod
    @transaction.atomic
    def bulk_resolve(alert_ids: List[int], user, notes: str = '') -> int:
        """Resolve multiple alerts."""
        now = timezone.now()
        count = Alert.objects.filter(id__in=alert_ids).update(
            status='resolved',
            resolved_at=now,
            resolved_by=user,
            resolution_notes=notes,
            is_read=True,
            read_at=now,
            read_by=user,
            updated_at=now
        )
        return count


class AlertGeneratorService:
    """
    Service for generating alerts based on system conditions.
    Should be called periodically via Celery task.
    """

    @classmethod
    def generate_all_alerts(cls):
        """
        Generate all types of alerts.
        Call this method from a periodic Celery task.
        """
        alerts = []
        alerts.extend(cls.generate_stock_alerts())
        alerts.extend(cls.generate_cash_difference_alerts())
        alerts.extend(cls.generate_void_rate_alerts())
        alerts.extend(cls.generate_shift_overtime_alerts())
        return alerts

    @classmethod
    def generate_stock_alerts(cls) -> List[Alert]:
        """
        Generate alerts for low stock and out of stock products.
        """
        alerts = []

        # Get active branches
        branches = Branch.objects.filter(is_active=True, is_deleted=False)

        for branch in branches:
            config = cls._get_config(branch_id=branch.id)

            # Find low stock items
            low_stock_items = BranchStock.objects.filter(
                branch=branch,
                product__is_active=True,
                product__is_deleted=False
            ).annotate(
                min_threshold=F('product__min_stock')
            ).filter(
                quantity__gt=0,
                quantity__lte=F('min_threshold')
            ).select_related('product', 'branch')

            for item in low_stock_items:
                # Check if alert already exists
                existing = Alert.objects.filter(
                    alert_type='low_stock',
                    product=item.product,
                    branch=item.branch,
                    status='active'
                ).exists()

                if not existing:
                    alert = Alert.objects.create(
                        alert_type='low_stock',
                        severity='medium',
                        title=f'Stock bajo: {item.product.name}',
                        message=(
                            f'El producto "{item.product.name}" tiene stock bajo '
                            f'en {item.branch.name}. '
                            f'Stock actual: {item.quantity}, '
                            f'Stock mínimo: {item.product.min_stock}'
                        ),
                        branch=item.branch,
                        product=item.product,
                        metadata={
                            'current_stock': item.quantity,
                            'min_stock': item.product.min_stock,
                            'product_sku': item.product.sku
                        }
                    )
                    alerts.append(alert)

            # Find out of stock items
            out_of_stock_items = BranchStock.objects.filter(
                branch=branch,
                product__is_active=True,
                product__is_deleted=False,
                quantity__lte=0
            ).select_related('product', 'branch')

            for item in out_of_stock_items:
                existing = Alert.objects.filter(
                    alert_type='out_of_stock',
                    product=item.product,
                    branch=item.branch,
                    status='active'
                ).exists()

                if not existing:
                    alert = Alert.objects.create(
                        alert_type='out_of_stock',
                        severity='high',
                        title=f'Sin stock: {item.product.name}',
                        message=(
                            f'El producto "{item.product.name}" está sin stock '
                            f'en {item.branch.name}.'
                        ),
                        branch=item.branch,
                        product=item.product,
                        metadata={
                            'product_sku': item.product.sku
                        }
                    )
                    alerts.append(alert)

        return alerts

    @classmethod
    def generate_cash_difference_alerts(cls, target_date: Optional[date] = None) -> List[Alert]:
        """
        Generate alerts for significant cash register differences.
        """
        alerts = []
        target_date = target_date or (timezone.now().date() - timedelta(days=1))

        registers = DailyCashRegister.objects.filter(
            date=target_date,
            is_closed=True
        ).select_related('branch')

        for register in registers:
            config = cls._get_config(branch_id=register.branch_id)
            threshold = config.get('cash_difference_threshold', Decimal('100.00'))

            if abs(register.difference) >= threshold:
                severity = 'critical' if abs(register.difference) >= threshold * 2 else 'high'

                existing = Alert.objects.filter(
                    alert_type='cash_difference',
                    branch=register.branch,
                    created_at__date=target_date,
                    status='active'
                ).exists()

                if not existing:
                    alert = Alert.objects.create(
                        alert_type='cash_difference',
                        severity=severity,
                        title=f'Diferencia de caja: {register.branch.name}',
                        message=(
                            f'La caja de {register.branch.name} del {target_date} '
                            f'tiene una diferencia de ${abs(register.difference):.2f}. '
                            f'Esperado: ${register.expected_amount:.2f}, '
                            f'Contado: ${register.closing_amount:.2f}'
                        ),
                        branch=register.branch,
                        metadata={
                            'date': target_date.isoformat(),
                            'expected': float(register.expected_amount),
                            'actual': float(register.closing_amount),
                            'difference': float(register.difference)
                        }
                    )
                    alerts.append(alert)

        return alerts

    @classmethod
    def generate_void_rate_alerts(cls, target_date: Optional[date] = None) -> List[Alert]:
        """
        Generate alerts for high void rates.
        """
        alerts = []
        target_date = target_date or timezone.now().date()

        branches = Branch.objects.filter(is_active=True, is_deleted=False)

        for branch in branches:
            config = cls._get_config(branch_id=branch.id)
            threshold = config.get('void_rate_threshold', Decimal('5.00'))

            # Get sales statistics
            sales = Sale.objects.filter(
                branch=branch,
                created_at__date=target_date
            )

            total_sales = sales.count()
            voided_sales = sales.filter(status='voided').count()

            if total_sales > 0:
                void_rate = (voided_sales / total_sales) * 100

                if void_rate >= float(threshold):
                    existing = Alert.objects.filter(
                        alert_type='high_void_rate',
                        branch=branch,
                        created_at__date=target_date,
                        status='active'
                    ).exists()

                    if not existing:
                        alert = Alert.objects.create(
                            alert_type='high_void_rate',
                            severity='high',
                            title=f'Alta tasa de anulaciones: {branch.name}',
                            message=(
                                f'La sucursal {branch.name} tiene una tasa de '
                                f'anulaciones del {void_rate:.1f}% hoy. '
                                f'({voided_sales} de {total_sales} ventas anuladas)'
                            ),
                            branch=branch,
                            metadata={
                                'date': target_date.isoformat(),
                                'total_sales': total_sales,
                                'voided_sales': voided_sales,
                                'void_rate': round(void_rate, 2)
                            }
                        )
                        alerts.append(alert)

        return alerts

    @classmethod
    def generate_shift_overtime_alerts(cls) -> List[Alert]:
        """
        Generate alerts for extended shifts.
        """
        alerts = []

        # Find open shifts that exceed threshold
        open_shifts = Shift.objects.filter(
            clock_out__isnull=True
        ).select_related('employee', 'branch')

        for shift in open_shifts:
            config = cls._get_config(branch_id=shift.branch_id)
            threshold_hours = config.get('overtime_threshold', Decimal('10.0'))

            duration = timezone.now() - shift.clock_in
            hours_worked = duration.total_seconds() / 3600

            if hours_worked >= float(threshold_hours):
                existing = Alert.objects.filter(
                    alert_type='shift_overtime',
                    employee=shift.employee,
                    status='active',
                    created_at__date=timezone.now().date()
                ).exists()

                if not existing:
                    alert = Alert.objects.create(
                        alert_type='shift_overtime',
                        severity='medium',
                        title=f'Turno extendido: {shift.employee.full_name}',
                        message=(
                            f'{shift.employee.full_name} lleva {hours_worked:.1f} horas '
                            f'trabajando en {shift.branch.name}. '
                            f'Hora de entrada: {shift.clock_in.strftime("%H:%M")}'
                        ),
                        branch=shift.branch,
                        employee=shift.employee,
                        metadata={
                            'shift_id': shift.id,
                            'clock_in': shift.clock_in.isoformat(),
                            'hours_worked': round(hours_worked, 2)
                        }
                    )
                    alerts.append(alert)

        return alerts

    @classmethod
    def auto_resolve_stock_alerts(cls):
        """
        Automatically resolve stock alerts when stock is replenished.
        """
        now = timezone.now()

        # Get active stock alerts
        stock_alerts = Alert.objects.filter(
            alert_type__in=['low_stock', 'out_of_stock'],
            status='active'
        ).select_related('product', 'branch')

        resolved_count = 0

        for alert in stock_alerts:
            if alert.product and alert.branch:
                try:
                    stock = BranchStock.objects.get(
                        product=alert.product,
                        branch=alert.branch
                    )

                    # Check if stock is now above minimum
                    if stock.quantity > alert.product.min_stock:
                        alert.status = 'resolved'
                        alert.resolved_at = now
                        alert.resolution_notes = 'Resuelto automáticamente: stock repuesto'
                        alert.save(update_fields=['status', 'resolved_at', 'resolution_notes', 'updated_at'])
                        resolved_count += 1

                except BranchStock.DoesNotExist:
                    pass

        return resolved_count

    @staticmethod
    def _get_config(branch_id: Optional[int] = None, category_id: Optional[int] = None) -> dict:
        """
        Get alert configuration for a specific scope.
        Falls back to global if no specific config exists.
        """
        config = None

        # Try branch-specific config
        if branch_id:
            config = AlertConfiguration.objects.filter(
                scope='branch',
                branch_id=branch_id,
                is_active=True
            ).first()

        # Try category-specific config
        if not config and category_id:
            config = AlertConfiguration.objects.filter(
                scope='category',
                category_id=category_id,
                is_active=True
            ).first()

        # Fall back to global
        if not config:
            config = AlertConfiguration.objects.filter(
                scope='global',
                is_active=True
            ).first()

        if config:
            return {
                'low_stock_threshold': config.low_stock_threshold,
                'overstock_threshold': config.overstock_threshold,
                'cash_difference_threshold': config.cash_difference_threshold,
                'void_rate_threshold': config.void_rate_threshold,
                'overtime_threshold': config.overtime_threshold,
            }

        # Default values
        return {
            'low_stock_threshold': 10,
            'overstock_threshold': 150,
            'cash_difference_threshold': Decimal('100.00'),
            'void_rate_threshold': Decimal('5.00'),
            'overtime_threshold': Decimal('10.0'),
        }


class AlertConfigurationService:
    """
    Service for managing alert configurations.
    """

    @staticmethod
    def get_configuration(
        scope: str = 'global',
        branch_id: Optional[int] = None,
        category_id: Optional[int] = None
    ) -> Optional[AlertConfiguration]:
        """Get configuration for specific scope."""
        filters = {'scope': scope, 'is_active': True}

        if scope == 'branch' and branch_id:
            filters['branch_id'] = branch_id
        elif scope == 'category' and category_id:
            filters['category_id'] = category_id

        return AlertConfiguration.objects.filter(**filters).first()

    @staticmethod
    @transaction.atomic
    def create_or_update_configuration(
        scope: str,
        branch_id: Optional[int] = None,
        category_id: Optional[int] = None,
        **kwargs
    ) -> AlertConfiguration:
        """Create or update alert configuration."""
        filters = {'scope': scope}

        if scope == 'branch':
            filters['branch_id'] = branch_id
        elif scope == 'category':
            filters['category_id'] = category_id

        config, created = AlertConfiguration.objects.update_or_create(
            defaults=kwargs,
            **filters
        )
        return config

    @staticmethod
    def get_user_preferences(user) -> UserAlertPreference:
        """Get or create user alert preferences."""
        prefs, _ = UserAlertPreference.objects.get_or_create(user=user)
        return prefs

    @staticmethod
    @transaction.atomic
    def update_user_preferences(user, **kwargs) -> UserAlertPreference:
        """Update user alert preferences."""
        prefs, _ = UserAlertPreference.objects.update_or_create(
            user=user,
            defaults=kwargs
        )
        return prefs
