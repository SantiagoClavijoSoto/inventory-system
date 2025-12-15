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
        Multi-tenant: only returns alerts for user's company.
        SuperAdmin: only returns platform-level alerts (subscriptions).
        """
        queryset = Alert.objects.all()

        # Determine if user is platform admin (superuser without company)
        is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_platform_admin', False)

        if is_platform_admin:
            # SuperAdmin: only show platform-level alerts (subscriptions)
            queryset = queryset.filter(alert_type__in=Alert.PLATFORM_ALERT_TYPES)
        elif hasattr(user, 'company_id') and user.company_id:
            # Company admin/user: only show company alerts (exclude platform alerts)
            queryset = queryset.filter(
                company_id=user.company_id
            ).exclude(alert_type__in=Alert.PLATFORM_ALERT_TYPES)

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
            'branch', 'product', 'employee', 'read_by', 'resolved_by', 'subscription'
        ).order_by('-created_at')[:limit])

    @staticmethod
    def get_unread_count(user, branch_id: Optional[int] = None) -> dict:
        """
        Get count of unread alerts by severity.
        Multi-tenant: only counts alerts for user's company.
        SuperAdmin: only counts platform-level alerts (subscriptions).
        """
        queryset = Alert.objects.filter(is_read=False, status='active')

        # Determine if user is platform admin (superuser without company)
        is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_platform_admin', False)

        if is_platform_admin:
            # SuperAdmin: only count platform-level alerts
            queryset = queryset.filter(alert_type__in=Alert.PLATFORM_ALERT_TYPES)
        elif hasattr(user, 'company_id') and user.company_id:
            # Company admin/user: only count company alerts
            queryset = queryset.filter(
                company_id=user.company_id
            ).exclude(alert_type__in=Alert.PLATFORM_ALERT_TYPES)

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
        """
        Mark a single alert as read.
        Multi-tenant: verifies alert belongs to user's company.
        SuperAdmin: can access platform-level alerts.
        """
        queryset = Alert.objects.select_for_update()

        # Determine if user is platform admin
        is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_platform_admin', False)

        if is_platform_admin:
            # SuperAdmin: can access platform-level alerts
            queryset = queryset.filter(alert_type__in=Alert.PLATFORM_ALERT_TYPES)
        elif hasattr(user, 'company_id') and user.company_id:
            # Multi-tenant filter: only allow access to user's company alerts
            queryset = queryset.filter(company_id=user.company_id)

        alert = queryset.get(id=alert_id)
        alert.mark_as_read(user)
        return alert

    @staticmethod
    @transaction.atomic
    def mark_all_as_read(user, branch_id: Optional[int] = None) -> int:
        """
        Mark all unread alerts as read.
        Multi-tenant: only marks alerts for user's company.
        SuperAdmin: marks platform-level alerts.
        """
        queryset = Alert.objects.filter(is_read=False)

        # Determine if user is platform admin
        is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_platform_admin', False)

        if is_platform_admin:
            # SuperAdmin: only mark platform-level alerts
            queryset = queryset.filter(alert_type__in=Alert.PLATFORM_ALERT_TYPES)
        elif hasattr(user, 'company_id') and user.company_id:
            # Multi-tenant filter: only mark alerts for user's company
            queryset = queryset.filter(company_id=user.company_id)

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
        """
        Acknowledge an alert.
        Multi-tenant: verifies alert belongs to user's company.
        SuperAdmin: can access platform-level alerts.
        """
        queryset = Alert.objects.select_for_update()

        # Determine if user is platform admin
        is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_platform_admin', False)

        if is_platform_admin:
            # SuperAdmin: can access platform-level alerts
            queryset = queryset.filter(alert_type__in=Alert.PLATFORM_ALERT_TYPES)
        elif hasattr(user, 'company_id') and user.company_id:
            # Multi-tenant filter: only allow access to user's company alerts
            queryset = queryset.filter(company_id=user.company_id)

        alert = queryset.get(id=alert_id)
        alert.acknowledge(user)
        return alert

    @staticmethod
    @transaction.atomic
    def resolve_alert(alert_id: int, user, notes: str = '') -> Alert:
        """
        Resolve an alert.
        Multi-tenant: verifies alert belongs to user's company.
        SuperAdmin: can access platform-level alerts.
        """
        queryset = Alert.objects.select_for_update()

        # Determine if user is platform admin
        is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_platform_admin', False)

        if is_platform_admin:
            # SuperAdmin: can access platform-level alerts
            queryset = queryset.filter(alert_type__in=Alert.PLATFORM_ALERT_TYPES)
        elif hasattr(user, 'company_id') and user.company_id:
            # Multi-tenant filter: only allow access to user's company alerts
            queryset = queryset.filter(company_id=user.company_id)

        alert = queryset.get(id=alert_id)
        alert.resolve(user, notes)
        return alert

    @staticmethod
    @transaction.atomic
    def dismiss_alert(alert_id: int, user) -> Alert:
        """
        Dismiss an alert.
        Multi-tenant: verifies alert belongs to user's company.
        SuperAdmin: can access platform-level alerts.
        """
        queryset = Alert.objects.select_for_update()

        # Determine if user is platform admin
        is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_platform_admin', False)

        if is_platform_admin:
            # SuperAdmin: can access platform-level alerts
            queryset = queryset.filter(alert_type__in=Alert.PLATFORM_ALERT_TYPES)
        elif hasattr(user, 'company_id') and user.company_id:
            # Multi-tenant filter: only allow access to user's company alerts
            queryset = queryset.filter(company_id=user.company_id)

        alert = queryset.get(id=alert_id)
        alert.dismiss(user)
        return alert

    @staticmethod
    @transaction.atomic
    def bulk_resolve(alert_ids: List[int], user, notes: str = '') -> int:
        """
        Resolve multiple alerts.
        Multi-tenant: only resolves alerts for user's company.
        SuperAdmin: can resolve platform-level alerts.
        """
        queryset = Alert.objects.filter(id__in=alert_ids)

        # Determine if user is platform admin
        is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_platform_admin', False)

        if is_platform_admin:
            # SuperAdmin: can resolve platform-level alerts
            queryset = queryset.filter(alert_type__in=Alert.PLATFORM_ALERT_TYPES)
        elif hasattr(user, 'company_id') and user.company_id:
            # Multi-tenant filter: only resolve alerts for user's company
            queryset = queryset.filter(company_id=user.company_id)

        now = timezone.now()
        count = queryset.update(
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

    # Fixed threshold for low stock alerts (5 products)
    LOW_STOCK_THRESHOLD = 5

    @classmethod
    def generate_stock_alerts(cls) -> List[Alert]:
        """
        Generate alerts for low stock and out of stock products.
        - Low stock: when quantity is between 1-5 products
        - Out of stock: when quantity is 0 or less
        """
        alerts = []

        # Get active branches
        branches = Branch.objects.filter(is_active=True, is_deleted=False)

        for branch in branches:
            # Find low stock items (quantity between 1 and LOW_STOCK_THRESHOLD)
            low_stock_items = BranchStock.objects.filter(
                branch=branch,
                product__is_active=True,
                product__is_deleted=False,
                quantity__gt=0,
                quantity__lte=cls.LOW_STOCK_THRESHOLD
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
                        company=branch.company,  # Multi-tenant: assign company from branch
                        alert_type='low_stock',
                        severity='medium',
                        title=f'Stock bajo: {item.product.name}',
                        message=(
                            f'El producto "{item.product.name}" tiene stock bajo '
                            f'en {item.branch.name}. '
                            f'Stock actual: {item.quantity} unidades. '
                            f'Se requiere reabastecer pronto.'
                        ),
                        branch=item.branch,
                        product=item.product,
                        metadata={
                            'current_stock': item.quantity,
                            'low_stock_threshold': cls.LOW_STOCK_THRESHOLD,
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
                        company=branch.company,  # Multi-tenant: assign company from branch
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
                        company=register.branch.company,  # Multi-tenant: assign company from branch
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
                            company=branch.company,  # Multi-tenant: assign company from branch
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
                        company=shift.branch.company,  # Multi-tenant: assign company from branch
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
        - Resolves 'low_stock' when quantity > LOW_STOCK_THRESHOLD (5)
        - Resolves 'out_of_stock' when quantity > 0
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

                    # Check if stock is now above threshold
                    # For low_stock: resolve when quantity > 5
                    # For out_of_stock: resolve when quantity > 5 (has stock again)
                    if stock.quantity > cls.LOW_STOCK_THRESHOLD:
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


class SubscriptionAlertGeneratorService:
    """
    Service for generating subscription-related alerts.
    These are platform-level alerts for the SuperAdmin.
    Should be called periodically via Celery task.
    """

    @classmethod
    def generate_all_subscription_alerts(cls) -> List[Alert]:
        """
        Generate all subscription-related alerts.
        Call this method from a periodic Celery task.
        """
        alerts = []
        alerts.extend(cls.generate_payment_due_alerts())
        alerts.extend(cls.generate_overdue_alerts())
        alerts.extend(cls.generate_trial_ending_alerts())
        return alerts

    @classmethod
    def generate_payment_due_alerts(cls, days_ahead: int = 7) -> List[Alert]:
        """
        Generate alerts for subscriptions with payments due within X days.
        """
        from apps.companies.models import Subscription

        alerts = []
        today = timezone.now().date()
        due_date_threshold = today + timedelta(days=days_ahead)

        # Find active subscriptions with payment due soon
        subscriptions = Subscription.objects.filter(
            status='active',
            next_payment_date__isnull=False,
            next_payment_date__gte=today,
            next_payment_date__lte=due_date_threshold
        ).select_related('company')

        for subscription in subscriptions:
            days_until = (subscription.next_payment_date - today).days

            # Check if alert already exists for this subscription
            existing = Alert.objects.filter(
                alert_type='subscription_payment_due',
                subscription=subscription,
                status='active'
            ).exists()

            if not existing:
                # Determine severity based on days remaining
                if days_until <= 2:
                    severity = 'high'
                elif days_until <= 5:
                    severity = 'medium'
                else:
                    severity = 'low'

                alert = Alert.objects.create(
                    company=None,  # Platform alert - no company association
                    alert_type='subscription_payment_due',
                    severity=severity,
                    title=f'Pago próximo: {subscription.company.name}',
                    message=(
                        f'La suscripción de "{subscription.company.name}" vence en {days_until} días. '
                        f'Fecha de pago: {subscription.next_payment_date.strftime("%d/%m/%Y")}. '
                        f'Plan: {subscription.get_plan_display()}. '
                        f'Monto: ${subscription.amount:,.0f} {subscription.currency}'
                    ),
                    subscription=subscription,
                    metadata={
                        'company_id': subscription.company.id,
                        'company_name': subscription.company.name,
                        'company_email': subscription.company.email,
                        'plan': subscription.plan,
                        'amount': float(subscription.amount),
                        'currency': subscription.currency,
                        'next_payment_date': subscription.next_payment_date.isoformat(),
                        'days_until_payment': days_until
                    }
                )
                alerts.append(alert)

        return alerts

    @classmethod
    def generate_overdue_alerts(cls) -> List[Alert]:
        """
        Generate alerts for subscriptions with overdue payments.
        """
        from apps.companies.models import Subscription

        alerts = []
        today = timezone.now().date()

        # Find subscriptions past due (both active with past date and past_due status)
        overdue_subscriptions = Subscription.objects.filter(
            Q(status='active', next_payment_date__lt=today) |
            Q(status='past_due')
        ).select_related('company')

        for subscription in overdue_subscriptions:
            days_overdue = 0
            if subscription.next_payment_date:
                days_overdue = (today - subscription.next_payment_date).days

            # Check if alert already exists
            existing = Alert.objects.filter(
                alert_type='subscription_overdue',
                subscription=subscription,
                status='active'
            ).exists()

            if not existing:
                # Higher severity for longer overdue
                if days_overdue >= 30:
                    severity = 'critical'
                elif days_overdue >= 14:
                    severity = 'high'
                else:
                    severity = 'medium'

                alert = Alert.objects.create(
                    company=None,  # Platform alert
                    alert_type='subscription_overdue',
                    severity=severity,
                    title=f'Pago vencido: {subscription.company.name}',
                    message=(
                        f'La suscripción de "{subscription.company.name}" tiene '
                        f'{days_overdue} días de atraso en el pago. '
                        f'Plan: {subscription.get_plan_display()}. '
                        f'Monto pendiente: ${subscription.amount:,.0f} {subscription.currency}'
                    ),
                    subscription=subscription,
                    metadata={
                        'company_id': subscription.company.id,
                        'company_name': subscription.company.name,
                        'company_email': subscription.company.email,
                        'plan': subscription.plan,
                        'amount': float(subscription.amount),
                        'currency': subscription.currency,
                        'next_payment_date': subscription.next_payment_date.isoformat() if subscription.next_payment_date else None,
                        'days_overdue': days_overdue,
                        'status': subscription.status
                    }
                )
                alerts.append(alert)

        return alerts

    @classmethod
    def generate_trial_ending_alerts(cls, days_ahead: int = 3) -> List[Alert]:
        """
        Generate alerts for trial subscriptions ending soon.
        """
        from apps.companies.models import Subscription

        alerts = []
        today = timezone.now().date()
        end_date_threshold = today + timedelta(days=days_ahead)

        # Find trial subscriptions ending soon
        trial_subscriptions = Subscription.objects.filter(
            status='trial',
            trial_ends_at__isnull=False,
            trial_ends_at__date__gte=today,
            trial_ends_at__date__lte=end_date_threshold
        ).select_related('company')

        for subscription in trial_subscriptions:
            trial_end_date = subscription.trial_ends_at.date()
            days_remaining = (trial_end_date - today).days

            # Check if alert already exists
            existing = Alert.objects.filter(
                alert_type='subscription_trial_ending',
                subscription=subscription,
                status='active'
            ).exists()

            if not existing:
                severity = 'high' if days_remaining <= 1 else 'medium'

                alert = Alert.objects.create(
                    company=None,  # Platform alert
                    alert_type='subscription_trial_ending',
                    severity=severity,
                    title=f'Prueba por terminar: {subscription.company.name}',
                    message=(
                        f'El período de prueba de "{subscription.company.name}" termina '
                        f'en {days_remaining} día(s). '
                        f'Fecha fin: {trial_end_date.strftime("%d/%m/%Y")}. '
                        f'Contactar para conversión a plan de pago.'
                    ),
                    subscription=subscription,
                    metadata={
                        'company_id': subscription.company.id,
                        'company_name': subscription.company.name,
                        'company_email': subscription.company.email,
                        'trial_ends_at': subscription.trial_ends_at.isoformat(),
                        'days_remaining': days_remaining
                    }
                )
                alerts.append(alert)

        return alerts

    @classmethod
    def auto_resolve_payment_alerts(cls) -> int:
        """
        Automatically resolve payment due alerts when payment is received.
        Called after a subscription payment is processed.
        """
        from apps.companies.models import Subscription

        now = timezone.now()
        today = now.date()
        resolved_count = 0

        # Get active payment due/overdue alerts
        payment_alerts = Alert.objects.filter(
            alert_type__in=['subscription_payment_due', 'subscription_overdue'],
            status='active'
        ).select_related('subscription')

        for alert in payment_alerts:
            if alert.subscription:
                subscription = alert.subscription
                # If payment date is now in the future, payment was made
                if subscription.next_payment_date and subscription.next_payment_date > today:
                    alert.status = 'resolved'
                    alert.resolved_at = now
                    alert.resolution_notes = 'Resuelto automáticamente: pago recibido'
                    alert.save(update_fields=['status', 'resolved_at', 'resolution_notes', 'updated_at'])
                    resolved_count += 1

        return resolved_count

    @classmethod
    def create_subscription_event_alert(
        cls,
        subscription,
        event_type: str,
        additional_info: str = ''
    ) -> Alert:
        """
        Create an alert for a subscription event (manual trigger).
        Used when subscription status changes, plan changes, etc.
        """
        event_configs = {
            'new_subscription': {
                'alert_type': 'new_subscription',
                'severity': 'low',
                'title': f'Nueva suscripción: {subscription.company.name}',
                'message': (
                    f'Nueva suscripción creada para "{subscription.company.name}". '
                    f'Plan: {subscription.get_plan_display()}. '
                    f'{additional_info}'
                )
            },
            'subscription_cancelled': {
                'alert_type': 'subscription_cancelled',
                'severity': 'high',
                'title': f'Suscripción cancelada: {subscription.company.name}',
                'message': (
                    f'La empresa "{subscription.company.name}" ha cancelado su suscripción. '
                    f'Plan anterior: {subscription.get_plan_display()}. '
                    f'{additional_info}'
                )
            },
            'subscription_suspended': {
                'alert_type': 'subscription_suspended',
                'severity': 'critical',
                'title': f'Suscripción suspendida: {subscription.company.name}',
                'message': (
                    f'La suscripción de "{subscription.company.name}" ha sido suspendida. '
                    f'Motivo: {additional_info or "Pago no recibido"}'
                )
            },
            'plan_changed': {
                'alert_type': 'subscription_plan_changed',
                'severity': 'low',
                'title': f'Cambio de plan: {subscription.company.name}',
                'message': (
                    f'"{subscription.company.name}" cambió su plan a {subscription.get_plan_display()}. '
                    f'{additional_info}'
                )
            }
        }

        config = event_configs.get(event_type)
        if not config:
            raise ValueError(f"Unknown event type: {event_type}")

        return Alert.objects.create(
            company=None,  # Platform alert
            alert_type=config['alert_type'],
            severity=config['severity'],
            title=config['title'],
            message=config['message'],
            subscription=subscription,
            metadata={
                'company_id': subscription.company.id,
                'company_name': subscription.company.name,
                'company_email': subscription.company.email,
                'plan': subscription.plan,
                'status': subscription.status,
                'event_type': event_type
            }
        )
