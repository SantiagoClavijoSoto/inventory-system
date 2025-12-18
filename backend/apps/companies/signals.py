"""
Signals for companies app.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Company, Subscription


# Plan pricing (monthly base)
PLAN_PRICING = {
    'free': Decimal('0'),
    'basic': Decimal('99000'),
    'professional': Decimal('199000'),
    'enterprise': Decimal('399000'),
}

# Billing cycle months mapping
BILLING_CYCLE_MONTHS = {
    'monthly': 1,
    'quarterly': 3,
    'semiannual': 6,
    'annual': 12,
}


def calculate_subscription_amount(plan: str, billing_cycle: str) -> Decimal:
    """Calculate total amount based on plan and billing cycle."""
    monthly_price = PLAN_PRICING.get(plan, Decimal('0'))
    months = BILLING_CYCLE_MONTHS.get(billing_cycle, 1)
    return monthly_price * months


def calculate_next_payment_date(start_date: date, billing_cycle: str) -> date:
    """Calculate next payment date based on billing cycle."""
    months = BILLING_CYCLE_MONTHS.get(billing_cycle, 1)
    # Add months to start date
    year = start_date.year + (start_date.month + months - 1) // 12
    month = (start_date.month + months - 1) % 12 + 1
    day = min(start_date.day, 28)  # Safe day for all months
    return date(year, month, day)


@receiver(post_save, sender=Company)
def create_subscription_for_company(sender, instance, created, **kwargs):
    """
    Automatically create a subscription when a company is created.
    New companies start with a 14-day trial period (unless status is set differently).
    Uses billing_cycle and subscription_status from attributes if set by serializer.
    """
    if created:
        # Check if subscription already exists (shouldn't, but be safe)
        if not hasattr(instance, 'subscription') or instance.subscription is None:
            today = date.today()
            trial_days = 14

            # Get values from serializer attributes or use defaults
            billing_cycle = getattr(instance, '_billing_cycle', 'monthly')
            subscription_status = getattr(instance, '_subscription_status', 'trial')

            # Calculate trial end and first payment date
            trial_end = today + timedelta(days=trial_days) if subscription_status == 'trial' else None
            # Next payment is calculated from today (or trial end if trial) based on cycle
            start_for_payment = trial_end if subscription_status == 'trial' else today
            next_payment = calculate_next_payment_date(start_for_payment, billing_cycle)

            Subscription.objects.create(
                company=instance,
                plan=instance.plan,
                status=subscription_status,
                billing_cycle=billing_cycle,
                start_date=today,
                trial_ends_at=trial_end,
                next_payment_date=next_payment,
                amount=calculate_subscription_amount(instance.plan, billing_cycle),
                currency='COP',
            )
