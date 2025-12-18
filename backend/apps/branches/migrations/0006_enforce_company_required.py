"""
Migration to enforce company FK as non-nullable on Branch.
IMPORTANT: This assumes no NULL values exist. Verified before creation.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial_company_model'),
        ('branches', '0005_change_code_unique_per_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='branch',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='branches',
                to='companies.company',
                verbose_name='Empresa',
            ),
        ),
    ]
