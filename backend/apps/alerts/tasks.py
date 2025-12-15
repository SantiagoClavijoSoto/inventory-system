"""
Celery tasks for alert generation and management.
"""
from celery import shared_task

from .services import AlertGeneratorService


@shared_task(name='alerts.generate_stock_alerts')
def generate_stock_alerts():
    """
    Generate stock alerts (low stock and out of stock).
    Should be called periodically, e.g., every 15 minutes.
    """
    alerts = AlertGeneratorService.generate_stock_alerts()
    return {
        'task': 'generate_stock_alerts',
        'alerts_created': len(alerts)
    }


@shared_task(name='alerts.generate_all_alerts')
def generate_all_alerts():
    """
    Generate all types of alerts.
    Should be called periodically, e.g., every hour.
    """
    alerts = AlertGeneratorService.generate_all_alerts()
    return {
        'task': 'generate_all_alerts',
        'alerts_created': len(alerts)
    }


@shared_task(name='alerts.auto_resolve_stock_alerts')
def auto_resolve_stock_alerts():
    """
    Auto-resolve stock alerts when stock is replenished.
    Should be called periodically, e.g., every 30 minutes.
    """
    resolved_count = AlertGeneratorService.auto_resolve_stock_alerts()
    return {
        'task': 'auto_resolve_stock_alerts',
        'alerts_resolved': resolved_count
    }
