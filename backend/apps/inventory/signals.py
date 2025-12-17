"""
Signals for the inventory module.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Product, BranchStock
from apps.branches.models import Branch


@receiver(post_save, sender=Product)
def create_branch_stock_for_new_product(sender, instance, created, **kwargs):
    """
    Automatically create BranchStock records for all active branches
    in the same company when a new product is created.
    """
    if created and instance.company_id:
        # Get all active branches for this company
        branches = Branch.objects.filter(
            company_id=instance.company_id,
            is_active=True,
            is_deleted=False
        )

        # Create BranchStock for each branch
        for branch in branches:
            BranchStock.objects.get_or_create(
                product=instance,
                branch=branch,
                defaults={'quantity': 0}
            )


@receiver(post_save, sender=BranchStock)
def generate_stock_alert_on_change(sender, instance, **kwargs):
    """
    Generate stock alerts in real-time when BranchStock quantity changes.
    This ensures alerts are created immediately without waiting for Celery tasks.
    """
    # Import here to avoid circular imports
    from apps.alerts.services import AlertGeneratorService

    # Generate or resolve alert based on current stock level
    AlertGeneratorService.generate_stock_alert_for_item(instance)
