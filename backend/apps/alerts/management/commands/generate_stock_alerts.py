"""
Management command to generate stock alerts.

This command scans all BranchStock records and creates alerts for:
- Out of stock products (quantity < 4, i.e., 0-3)
- Low stock products (quantity between 4-9)

Stock Status Thresholds:
- stock: >= 10 (healthy, no alert)
- stock-bajo: 4-9 (low_stock alert)
- sin-stock: <= 3 (out_of_stock alert)

Usage:
    python manage.py generate_stock_alerts
    python manage.py generate_stock_alerts --company=moda-elegante
    python manage.py generate_stock_alerts --reset  # Clear existing alerts first
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.alerts.services import AlertGeneratorService
from apps.alerts.models import Alert
from apps.companies.models import Company


class Command(BaseCommand):
    help = 'Generate stock alerts for all products with low or out of stock'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Generate alerts only for a specific company (by slug)',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Resolve all existing stock alerts before generating new ones',
        )

    def handle(self, *args, **options):
        company_slug = options.get('company')
        reset = options.get('reset', False)

        if company_slug:
            try:
                company = Company.objects.get(slug=company_slug)
                self.stdout.write(f'Generating alerts for company: {company.name}')
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Company not found: {company_slug}'))
                return
        else:
            self.stdout.write('Generating stock alerts for all companies...')

        # Reset existing stock alerts if requested
        if reset:
            self.stdout.write('\nResetting existing stock alerts...')
            now = timezone.now()
            resolved_count = Alert.objects.filter(
                alert_type__in=['low_stock', 'out_of_stock'],
                status='active'
            ).update(
                status='resolved',
                resolved_at=now,
                resolution_notes='Resuelto automáticamente: regeneración de alertas con nuevos umbrales'
            )
            self.stdout.write(self.style.SUCCESS(f'Resolved {resolved_count} existing alerts'))

        # Generate stock alerts
        alerts = AlertGeneratorService.generate_stock_alerts()

        if alerts:
            self.stdout.write(self.style.SUCCESS(f'\nCreated {len(alerts)} new alerts:'))
            for alert in alerts:
                self.stdout.write(f'  - {alert.title} ({alert.branch.name})')
        else:
            self.stdout.write(self.style.WARNING('\nNo new alerts created.'))

        # Report existing alerts
        existing_low = Alert.objects.filter(alert_type='low_stock', status='active').count()
        existing_out = Alert.objects.filter(alert_type='out_of_stock', status='active').count()

        self.stdout.write(f'\nActive stock alerts:')
        self.stdout.write(f'  - Low stock (4-9 units): {existing_low}')
        self.stdout.write(f'  - Out of stock (0-3 units): {existing_out}')
        self.stdout.write(f'  - Total: {existing_low + existing_out}')
