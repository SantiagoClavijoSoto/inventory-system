"""
Migration to enforce company FK as non-nullable on Category and Product.
IMPORTANT: This assumes no NULL values exist. Verified before creation.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial_company_model'),
        ('inventory', '0005_fix_low_prices_cop'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='categories',
                to='companies.company',
                verbose_name='Empresa',
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='products',
                to='companies.company',
                verbose_name='Empresa',
            ),
        ),
    ]
