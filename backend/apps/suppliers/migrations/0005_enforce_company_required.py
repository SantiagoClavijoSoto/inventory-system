"""
Migration to enforce company FK as non-nullable on Supplier.
IMPORTANT: This assumes no NULL values exist. Verified before creation.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial_company_model'),
        ('suppliers', '0004_change_code_unique_per_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplier',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='suppliers',
                to='companies.company',
                verbose_name='Empresa',
            ),
        ),
    ]
