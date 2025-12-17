"""
Management command to distribute sales dates across the last N days.
Used to fix seed data where all sales were created on the same day.
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.sales.models import Sale


class Command(BaseCommand):
    help = 'Distribute sales dates across the last N days for better testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to distribute sales across (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        self.stdout.write(f'Distributing sales across last {days} days...')

        sales = list(Sale.objects.all().order_by('id'))
        total_sales = len(sales)

        if total_sales == 0:
            self.stdout.write(self.style.WARNING('No sales found to distribute'))
            return

        self.stdout.write(f'Found {total_sales} sales to distribute')

        now = timezone.now()

        # Create weighted distribution - more recent days get more sales
        # This creates a more realistic pattern
        weights = []
        for day_offset in range(days):
            # Weight decreases as we go further back (more sales in recent days)
            weight = (days - day_offset) ** 1.5
            weights.append(weight)

        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Assign each sale to a random day based on weights
        day_offsets = random.choices(range(days), weights=normalized_weights, k=total_sales)

        # Track distribution for reporting
        distribution = {}

        for sale, day_offset in zip(sales, day_offsets):
            # Calculate new date (keeping the time component varied)
            base_date = now - timedelta(days=day_offset)
            # Add some random hours to vary the time
            random_hours = random.randint(8, 20)  # Business hours
            random_minutes = random.randint(0, 59)
            random_seconds = random.randint(0, 59)

            new_datetime = base_date.replace(
                hour=random_hours,
                minute=random_minutes,
                second=random_seconds,
                microsecond=0
            )

            date_key = new_datetime.date().isoformat()
            distribution[date_key] = distribution.get(date_key, 0) + 1

            if not dry_run:
                # Update without triggering signals
                Sale.objects.filter(pk=sale.pk).update(created_at=new_datetime)

        # Show distribution summary
        self.stdout.write('\nSales distribution:')
        for date_str in sorted(distribution.keys()):
            count = distribution[date_str]
            bar = '█' * (count // 5) + '▌' * (1 if count % 5 >= 3 else 0)
            self.stdout.write(f'  {date_str}: {count:3d} sales {bar}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDry run - no changes made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully distributed {total_sales} sales across {days} days'))
