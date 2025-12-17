"""
Data migration to fix product prices that are too low for Colombian Peso (COP).

This migration:
1. Identifies products with suspiciously low prices (sale_price < 1000)
2. Multiplies those prices by 100 to convert to proper COP values

Example: A product showing COP 500 will become COP 50,000

This is safe to run multiple times - it only affects products with prices < 1000.
"""
from decimal import Decimal
from django.db import migrations


# Threshold: prices below this are considered incorrect
PRICE_THRESHOLD = Decimal('1000.00')
MULTIPLICATION_FACTOR = Decimal('100')


def fix_low_prices(apps, schema_editor):
    """
    Fix products with prices that are too low for COP.
    Only affects products where sale_price < 1000.
    """
    Product = apps.get_model('inventory', 'Product')

    # Get all products with low prices
    low_price_products = Product.objects.filter(sale_price__lt=PRICE_THRESHOLD)
    count = low_price_products.count()

    if count == 0:
        print("No products with low prices found. Nothing to fix.")
        return

    print(f"Found {count} products with sale_price < {PRICE_THRESHOLD}")
    print("Multiplying prices by 100...")

    for product in low_price_products:
        old_cost = product.cost_price
        old_sale = product.sale_price

        product.cost_price = product.cost_price * MULTIPLICATION_FACTOR
        product.sale_price = product.sale_price * MULTIPLICATION_FACTOR
        product.save(update_fields=['cost_price', 'sale_price'])

        print(f"  {product.name}: cost {old_cost} -> {product.cost_price}, sale {old_sale} -> {product.sale_price}")

    print(f"Fixed {count} products.")


def reverse_fix(apps, schema_editor):
    """
    Reverse: divide prices by 100 for products that were fixed.
    NOTE: This reverses ALL products with sale_price >= 100000, which may not be accurate.
    Use with caution.
    """
    Product = apps.get_model('inventory', 'Product')

    # Products that would have been fixed now have prices >= 100000
    high_price_products = Product.objects.filter(sale_price__gte=PRICE_THRESHOLD * MULTIPLICATION_FACTOR)

    for product in high_price_products:
        product.cost_price = product.cost_price / MULTIPLICATION_FACTOR
        product.sale_price = product.sale_price / MULTIPLICATION_FACTOR
        product.save(update_fields=['cost_price', 'sale_price'])


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_convert_prices_to_cop'),
    ]

    operations = [
        migrations.RunPython(
            fix_low_prices,
            reverse_code=reverse_fix,
        ),
    ]
