"""
Data migration to convert prices from small values to Colombian Peso (COP).
Multiplies all cost_price and sale_price values by 1000.
"""
from django.db import migrations


def multiply_prices_by_1000(apps, schema_editor):
    """Multiply all product prices by 1000 to convert to COP."""
    Product = apps.get_model('inventory', 'Product')

    for product in Product.objects.all():
        product.cost_price = product.cost_price * 1000
        product.sale_price = product.sale_price * 1000
        product.save(update_fields=['cost_price', 'sale_price'])


def divide_prices_by_1000(apps, schema_editor):
    """Reverse: divide all product prices by 1000."""
    Product = apps.get_model('inventory', 'Product')

    for product in Product.objects.all():
        product.cost_price = product.cost_price / 1000
        product.sale_price = product.sale_price / 1000
        product.save(update_fields=['cost_price', 'sale_price'])


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_add_company_fk'),
    ]

    operations = [
        migrations.RunPython(
            multiply_prices_by_1000,
            reverse_code=divide_prices_by_1000,
        ),
    ]
