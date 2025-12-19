"""
Celery tasks for user-related async operations.
"""
import logging
from django.conf import settings
from celery import shared_task

logger = logging.getLogger(__name__)


def trigger_verification_email(user_id: int):
    """
    Trigger sending of verification email - sync or async based on settings.

    In development (SEND_EMAILS_SYNC=True), sends immediately.
    In production, queues via Celery.
    """
    if getattr(settings, 'SEND_EMAILS_SYNC', False):
        logger.info(f"Sending verification email synchronously for user {user_id}")
        return send_verification_email(user_id)
    else:
        logger.info(f"Queuing verification email async for user {user_id}")
        return send_verification_email.delay(user_id)


def trigger_password_notification(user_id: int):
    """
    Trigger password change notification - sync or async based on settings.
    """
    if getattr(settings, 'SEND_EMAILS_SYNC', False):
        logger.info(f"Sending password notification synchronously for user {user_id}")
        return send_password_changed_notification(user_id)
    else:
        logger.info(f"Queuing password notification async for user {user_id}")
        return send_password_changed_notification.delay(user_id)


@shared_task(name='users.send_verification_email')
def send_verification_email(user_id: int):
    """
    Send verification email to a user asynchronously.

    Args:
        user_id: The ID of the user to send verification to.
    """
    from apps.users.models import User
    from apps.users.services import EmailService

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for verification email")
        return {'task': 'send_verification_email', 'status': 'error', 'reason': 'user_not_found'}

    if user.email_verified:
        logger.info(f"User {user_id} is already verified, skipping email")
        return {'task': 'send_verification_email', 'status': 'skipped', 'reason': 'already_verified'}

    try:
        verification = EmailService.send_verification_code(user)
        return {
            'task': 'send_verification_email',
            'status': 'success',
            'user_id': user_id,
            'code_expires_at': verification.expires_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to send verification email to user {user_id}: {e}")
        return {'task': 'send_verification_email', 'status': 'error', 'reason': str(e)}


@shared_task(name='users.send_password_changed_notification')
def send_password_changed_notification(user_id: int):
    """
    Send notification that password was changed.

    Args:
        user_id: The ID of the user whose password changed.
    """
    from apps.users.models import User
    from apps.users.services import EmailService

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for password notification")
        return {'task': 'send_password_changed_notification', 'status': 'error', 'reason': 'user_not_found'}

    try:
        EmailService.send_password_reset_notification(user)
        return {'task': 'send_password_changed_notification', 'status': 'success', 'user_id': user_id}
    except Exception as e:
        logger.error(f"Failed to send password notification to user {user_id}: {e}")
        return {'task': 'send_password_changed_notification', 'status': 'error', 'reason': str(e)}
