"""
Email service for user verification and notifications.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from apps.users.models import User, EmailVerificationCode

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails to users."""

    DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@inventory.local')

    @classmethod
    def send_verification_code(cls, user: User) -> EmailVerificationCode:
        """
        Generate and send a verification code to a new user.

        Args:
            user: The user to send the verification code to.

        Returns:
            The created EmailVerificationCode instance.
        """
        # Create new verification code (invalidates previous ones)
        verification = EmailVerificationCode.create_for_user(user)

        # Prepare email content
        subject = 'Verifica tu cuenta - Código de acceso'

        context = {
            'user_name': user.first_name,
            'code': verification.code,
            'expiration_hours': EmailVerificationCode.EXPIRATION_HOURS,
            'company_name': user.company.name if user.company else 'Sistema de Inventario',
        }

        # Simple HTML template
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9fafb; }}
                .code {{ font-size: 32px; font-weight: bold; text-align: center;
                         background-color: #e5e7eb; padding: 20px; margin: 20px 0;
                         letter-spacing: 8px; border-radius: 8px; }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{context['company_name']}</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{context['user_name']}</strong>,</p>
                    <p>Se ha creado una cuenta para ti. Para activar tu acceso, usa el siguiente código de verificación:</p>
                    <div class="code">{context['code']}</div>
                    <p><strong>Este código expira en {context['expiration_hours']} hora(s).</strong></p>
                    <p>Si no solicitaste esta cuenta, puedes ignorar este mensaje.</p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text version
        plain_message = f"""
Hola {context['user_name']},

Se ha creado una cuenta para ti en {context['company_name']}.

Tu código de verificación es: {context['code']}

Este código expira en {context['expiration_hours']} hora(s).

Si no solicitaste esta cuenta, puedes ignorar este mensaje.
        """

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=cls.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")
            # Don't raise - the code was created, user can request resend

        return verification

    @classmethod
    def send_password_reset_notification(cls, user: User) -> None:
        """
        Send notification that password was changed.

        Args:
            user: The user whose password was changed.
        """
        subject = 'Tu contraseña ha sido actualizada'

        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .content {{ padding: 30px; background-color: #f9fafb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <p>Hola <strong>{user.first_name}</strong>,</p>
                    <p>Tu contraseña ha sido actualizada exitosamente.</p>
                    <p>Si no realizaste este cambio, contacta inmediatamente al administrador.</p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_message = f"""
Hola {user.first_name},

Tu contraseña ha sido actualizada exitosamente.

Si no realizaste este cambio, contacta inmediatamente al administrador.
        """

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=cls.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,  # Non-critical notification
            )
            logger.info(f"Password change notification sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password change notification to {user.email}: {e}")
