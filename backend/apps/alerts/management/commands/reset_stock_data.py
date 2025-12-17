"""
Management command to reset stock data and fix negative quantities.

This command:
1. Fixes all negative stock quantities with random valid values
2. Resolves all existing stock alerts
3. Regenerates alerts based on new stock levels

Usage:
    python manage.py reset_stock_data
    python manage.py reset_stock_data --dry-run  # Preview changes without applying
"""
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.inventory.models import BranchStock, STOCK_THRESHOLD_OK, STOCK_THRESHOLD_LOW
from apps.alerts.models import Alert
from apps.alerts.services import AlertGeneratorService


class Command(BaseCommand):
    help = 'Reset stock data: fix negative quantities and regenerate alerts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN MODE (no changes will be saved) ===\n'))

        # Step 1: Fix negative stock quantities
        self.stdout.write('\n1. Fixing negative stock quantities...')
        negative_stocks = BranchStock.objects.filter(quantity__lt=0)
        negative_count = negative_stocks.count()

        if negative_count == 0:
            self.stdout.write(self.style.SUCCESS('   No negative stock found!'))
        else:
            self.stdout.write(f'   Found {negative_count} records with negative stock')

            # Distribution: 30% sin-stock (0-3), 30% stock-bajo (4-9), 40% stock saludable (10-30)
            stock_distributions = {
                'sin-stock': (0, 3),      # 30%
                'stock-bajo': (4, 9),     # 30%
                'stock': (10, 30),        # 40%
            }

            fixed_count = 0
            for bs in negative_stocks:
                # Randomly select distribution
                rand = random.random()
                if rand < 0.3:
                    min_val, max_val = stock_distributions['sin-stock']
                elif rand < 0.6:
                    min_val, max_val = stock_distributions['stock-bajo']
                else:
                    min_val, max_val = stock_distributions['stock']

                new_quantity = random.randint(min_val, max_val)
                old_quantity = bs.quantity

                if not dry_run:
                    bs.quantity = new_quantity
                    bs.save(update_fields=['quantity', 'updated_at'])

                self.stdout.write(
                    f'   - {bs.product.name} @ {bs.branch.name}: '
                    f'{old_quantity} -> {new_quantity}'
                )
                fixed_count += 1

            self.stdout.write(self.style.SUCCESS(f'   Fixed {fixed_count} records'))

        # Step 2: Also randomize some healthy stocks to have variety
        self.stdout.write('\n2. Adding variety to existing stock levels...')
        all_stocks = BranchStock.objects.filter(quantity__gte=0)
        varied_count = 0

        for bs in all_stocks:
            # 20% chance to change to sin-stock, 20% to stock-bajo
            rand = random.random()
            if rand < 0.15:  # 15% sin-stock
                new_quantity = random.randint(0, 3)
            elif rand < 0.35:  # 20% stock-bajo
                new_quantity = random.randint(4, 9)
            else:
                continue  # Keep current value

            old_quantity = bs.quantity
            if not dry_run:
                bs.quantity = new_quantity
                bs.save(update_fields=['quantity', 'updated_at'])

            self.stdout.write(
                f'   - {bs.product.name} @ {bs.branch.name}: '
                f'{old_quantity} -> {new_quantity}'
            )
            varied_count += 1

        self.stdout.write(self.style.SUCCESS(f'   Varied {varied_count} records'))

        # Step 3: Resolve all existing stock alerts
        self.stdout.write('\n3. Resolving existing stock alerts...')
        if not dry_run:
            now = timezone.now()
            resolved_count = Alert.objects.filter(
                alert_type__in=['low_stock', 'out_of_stock'],
                status='active'
            ).update(
                status='resolved',
                resolved_at=now,
                resolution_notes='Resuelto automáticamente: datos de stock reseteados'
            )
            self.stdout.write(self.style.SUCCESS(f'   Resolved {resolved_count} alerts'))
        else:
            pending_alerts = Alert.objects.filter(
                alert_type__in=['low_stock', 'out_of_stock'],
                status='active'
            ).count()
            self.stdout.write(f'   Would resolve {pending_alerts} alerts')

        # Step 4: Generate new alerts
        self.stdout.write('\n4. Generating new alerts...')
        if not dry_run:
            new_alerts = AlertGeneratorService.generate_stock_alerts()
            self.stdout.write(self.style.SUCCESS(f'   Created {len(new_alerts)} new alerts'))

            # Summary
            for alert in new_alerts[:10]:
                self.stdout.write(f'   - {alert.title} ({alert.branch.name})')
            if len(new_alerts) > 10:
                self.stdout.write(f'   ... and {len(new_alerts) - 10} more')
        else:
            self.stdout.write('   Would generate new alerts based on current stock')

        # Final summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('SUMMARY:')

        # Count current stock status distribution
        sin_stock = BranchStock.objects.filter(quantity__lt=STOCK_THRESHOLD_LOW).count()
        stock_bajo = BranchStock.objects.filter(
            quantity__gte=STOCK_THRESHOLD_LOW,
            quantity__lt=STOCK_THRESHOLD_OK
        ).count()
        stock_ok = BranchStock.objects.filter(quantity__gte=STOCK_THRESHOLD_OK).count()
        total = BranchStock.objects.count()

        self.stdout.write(f'\nStock Distribution ({total} total records):')
        self.stdout.write(f'  - Sin stock (0-3):    {sin_stock} ({sin_stock*100//total}%)')
        self.stdout.write(f'  - Stock bajo (4-9):   {stock_bajo} ({stock_bajo*100//total}%)')
        self.stdout.write(f'  - Stock OK (>=10):    {stock_ok} ({stock_ok*100//total}%)')

        # Alert counts
        active_low = Alert.objects.filter(alert_type='low_stock', status='active').count()
        active_out = Alert.objects.filter(alert_type='out_of_stock', status='active').count()

        self.stdout.write(f'\nActive Alerts:')
        self.stdout.write(f'  - Low stock:    {active_low}')
        self.stdout.write(f'  - Out of stock: {active_out}')
        self.stdout.write(f'  - Total:        {active_low + active_out}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN - No changes were saved ==='))
            self.stdout.write('Run without --dry-run to apply changes')
