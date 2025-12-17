"""
Management command to fix product prices for Colombian Peso (COP).

Usage:
    # Preview products with low prices (dry run)
    python manage.py fix_prices --preview

    # Fix all products with sale_price < 1000, multiply by 100
    python manage.py fix_prices --threshold 1000 --factor 100

    # Fix specific company's products
    python manage.py fix_prices --company-id 1 --threshold 1000 --factor 100

    # Fix all products regardless of price (use with caution!)
    python manage.py fix_prices --all --factor 100
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.inventory.models import Product


class Command(BaseCommand):
    help = 'Fix product prices by multiplying by a factor (for COP conversion)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Preview products that would be affected (dry run)',
        )
        parser.add_argument(
            '--threshold',
            type=Decimal,
            default=Decimal('1000'),
            help='Only fix products with sale_price below this value (default: 1000)',
        )
        parser.add_argument(
            '--factor',
            type=Decimal,
            default=Decimal('100'),
            help='Multiplication factor to apply (default: 100)',
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='Only fix products for a specific company ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Fix ALL products regardless of price threshold (use with caution!)',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        threshold = options['threshold']
        factor = options['factor']
        preview = options['preview']
        fix_all = options['all']
        company_id = options['company_id']
        confirm = options['confirm']

        # Build queryset
        queryset = Product.objects.filter(is_deleted=False)

        if company_id:
            queryset = queryset.filter(company_id=company_id)
            self.stdout.write(f"Filtering by company_id: {company_id}")

        if not fix_all:
            queryset = queryset.filter(sale_price__lt=threshold)
            self.stdout.write(f"Filtering products with sale_price < {threshold}")
        else:
            self.stdout.write(self.style.WARNING("Processing ALL products (--all flag)"))

        products = list(queryset.order_by('company_id', 'name'))
        count = len(products)

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No products found matching criteria. Nothing to fix."))
            return

        self.stdout.write(f"\nFound {count} products to process:\n")
        self.stdout.write("-" * 80)

        # Show preview
        current_company = None
        for product in products:
            if product.company_id != current_company:
                current_company = product.company_id
                company_name = product.company.name if product.company else "Sin empresa"
                self.stdout.write(f"\n=== Company {current_company}: {company_name} ===")

            new_cost = product.cost_price * factor
            new_sale = product.sale_price * factor

            self.stdout.write(
                f"  {product.name}:\n"
                f"    Costo: {product.cost_price:>12} -> {new_cost:>12}\n"
                f"    Venta: {product.sale_price:>12} -> {new_sale:>12}"
            )

        self.stdout.write("-" * 80)
        self.stdout.write(f"\nTotal: {count} productos serán multiplicados por {factor}\n")

        if preview:
            self.stdout.write(self.style.WARNING("\n[PREVIEW MODE] No changes were made."))
            self.stdout.write("Run without --preview to apply changes.")
            return

        # Confirm before applying
        if not confirm:
            self.stdout.write(self.style.WARNING("\n¿Deseas aplicar estos cambios?"))
            response = input("Escribe 'SI' para confirmar: ")
            if response.strip().upper() != 'SI':
                self.stdout.write(self.style.ERROR("Operación cancelada."))
                return

        # Apply changes
        self.stdout.write("\nAplicando cambios...")

        for product in products:
            product.cost_price = product.cost_price * factor
            product.sale_price = product.sale_price * factor
            product.save(update_fields=['cost_price', 'sale_price'])

        self.stdout.write(self.style.SUCCESS(f"\n✓ {count} productos actualizados correctamente."))
        self.stdout.write("\nNuevos precios:")

        # Show updated prices
        for product in Product.objects.filter(id__in=[p.id for p in products]).order_by('company_id', 'name')[:10]:
            self.stdout.write(f"  {product.name}: costo={product.cost_price}, venta={product.sale_price}")

        if count > 10:
            self.stdout.write(f"  ... y {count - 10} más")
