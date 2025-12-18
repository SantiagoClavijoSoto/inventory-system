"""
Add performance indexes for common queries.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add indexes for Supplier and PurchaseOrder models."""

    dependencies = [
        ('suppliers', '0005_enforce_company_required'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='supplier',
            index=models.Index(
                fields=['company', 'name'],
                name='supplier_company_name_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='purchaseorder',
            index=models.Index(
                fields=['supplier', 'status'],
                name='po_supplier_status_idx'
            ),
        ),
    ]
