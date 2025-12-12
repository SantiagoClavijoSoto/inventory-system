"""
Data migration to create Subscription records for existing companies.
"""
from datetime import date, timedelta
from django.db import migrations


def create_subscriptions(apps, schema_editor):
    """Create Subscription for each Company that doesn't have one."""
    Company = apps.get_model('companies', 'Company')
    Subscription = apps.get_model('companies', 'Subscription')

    for company in Company.objects.filter(is_deleted=False):
        # Check if subscription already exists
        if not Subscription.objects.filter(company=company).exists():
            # Create subscription with default values
            Subscription.objects.create(
                company=company,
                plan=company.plan,
                status='active',
                billing_cycle='monthly',
                start_date=company.created_at.date() if company.created_at else date.today(),
                next_payment_date=date.today() + timedelta(days=30),
            )


def remove_subscriptions(apps, schema_editor):
    """Remove all auto-created subscriptions (reverse migration)."""
    Subscription = apps.get_model('companies', 'Subscription')
    # Only delete subscriptions created by this migration (those with default values)
    Subscription.objects.filter(
        status='active',
        billing_cycle='monthly',
        amount=0,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('companies', '0002_add_subscription_model'),
    ]

    operations = [
        migrations.RunPython(create_subscriptions, remove_subscriptions),
    ]
