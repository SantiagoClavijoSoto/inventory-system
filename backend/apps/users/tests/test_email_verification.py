"""
Tests for email verification flow.
"""
import pytest
from datetime import timedelta
from unittest.mock import patch
from django.utils import timezone
from rest_framework import status

from apps.users.models import User, EmailVerificationCode


@pytest.fixture
def unverified_user(db):
    """Create a user with email_verified=False."""
    user = User.objects.create_user(
        email='unverified@test.com',
        password='testpass123',
        first_name='Unverified',
        last_name='User',
        email_verified=False,
        is_active=True
    )
    return user


@pytest.fixture
def verification_code(db, unverified_user):
    """Create a verification code for the unverified user."""
    return EmailVerificationCode.create_for_user(unverified_user)


class TestEmailVerificationCode:
    """Tests for EmailVerificationCode model."""

    def test_generate_code_is_6_digits(self, db):
        """Test that generated code is 6 digits."""
        code = EmailVerificationCode.generate_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_create_for_user_invalidates_previous_codes(self, db, unverified_user):
        """Test that creating a new code invalidates previous ones."""
        # Create first code
        code1 = EmailVerificationCode.create_for_user(unverified_user)
        assert not code1.is_used

        # Create second code
        code2 = EmailVerificationCode.create_for_user(unverified_user)

        # Refresh first code from DB
        code1.refresh_from_db()
        assert code1.is_used  # Previous code is now used
        assert not code2.is_used

    def test_is_expired_property(self, db, unverified_user):
        """Test is_expired property."""
        code = EmailVerificationCode.create_for_user(unverified_user)
        assert not code.is_expired

        # Manually set expires_at to past
        code.expires_at = timezone.now() - timedelta(hours=1)
        code.save()
        assert code.is_expired

    def test_is_valid_property(self, db, verification_code):
        """Test is_valid property for valid code."""
        assert verification_code.is_valid

    def test_is_valid_false_when_used(self, db, verification_code):
        """Test is_valid is False when code is used."""
        verification_code.mark_as_used()
        assert not verification_code.is_valid

    def test_is_valid_false_when_expired(self, db, verification_code):
        """Test is_valid is False when code is expired."""
        verification_code.expires_at = timezone.now() - timedelta(hours=1)
        verification_code.save()
        assert not verification_code.is_valid

    def test_is_valid_false_when_max_attempts(self, db, verification_code):
        """Test is_valid is False when max attempts reached."""
        verification_code.attempts = EmailVerificationCode.MAX_ATTEMPTS
        verification_code.save()
        assert not verification_code.is_valid

    def test_increment_attempts(self, db, verification_code):
        """Test increment_attempts method."""
        initial = verification_code.attempts
        verification_code.increment_attempts()
        verification_code.refresh_from_db()
        assert verification_code.attempts == initial + 1

    def test_mark_as_used(self, db, verification_code):
        """Test mark_as_used method."""
        assert not verification_code.is_used
        verification_code.mark_as_used()
        verification_code.refresh_from_db()
        assert verification_code.is_used


class TestVerifyEmailEndpoint:
    """Tests for verify-email API endpoint."""

    def test_verify_email_success(self, api_client, unverified_user, verification_code):
        """Test successful email verification."""
        response = api_client.post('/api/v1/auth/verify-email/', {
            'email': unverified_user.email,
            'code': verification_code.code
        })

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data

        # Check user is now verified
        unverified_user.refresh_from_db()
        assert unverified_user.email_verified

        # Check code is marked as used
        verification_code.refresh_from_db()
        assert verification_code.is_used

    def test_verify_email_wrong_code(self, api_client, unverified_user, verification_code):
        """Test verification with wrong code."""
        response = api_client.post('/api/v1/auth/verify-email/', {
            'email': unverified_user.email,
            'code': '000000'  # Wrong code
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

        # Check attempts incremented
        verification_code.refresh_from_db()
        assert verification_code.attempts == 1

    def test_verify_email_expired_code(self, api_client, unverified_user, verification_code):
        """Test verification with expired code."""
        verification_code.expires_at = timezone.now() - timedelta(hours=2)
        verification_code.save()

        response = api_client.post('/api/v1/auth/verify-email/', {
            'email': unverified_user.email,
            'code': verification_code.code
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'expirado' in response.data['error'].lower()

    def test_verify_email_max_attempts(self, api_client, unverified_user, verification_code):
        """Test verification when max attempts reached."""
        verification_code.attempts = EmailVerificationCode.MAX_ATTEMPTS
        verification_code.save()

        response = api_client.post('/api/v1/auth/verify-email/', {
            'email': unverified_user.email,
            'code': verification_code.code
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'intentos' in response.data['error'].lower()

    def test_verify_email_already_verified(self, api_client, unverified_user, verification_code):
        """Test verification when user already verified."""
        unverified_user.email_verified = True
        unverified_user.save()

        response = api_client.post('/api/v1/auth/verify-email/', {
            'email': unverified_user.email,
            'code': verification_code.code
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'verificado' in response.data['error'].lower()

    def test_verify_email_user_not_found(self, db, api_client):
        """Test verification with non-existent email."""
        response = api_client.post('/api/v1/auth/verify-email/', {
            'email': 'nonexistent@test.com',
            'code': '123456'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_email_invalid_code_format(self, api_client, unverified_user):
        """Test verification with invalid code format."""
        response = api_client.post('/api/v1/auth/verify-email/', {
            'email': unverified_user.email,
            'code': 'abc'  # Not 6 digits
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestResendVerificationEndpoint:
    """Tests for resend-verification API endpoint."""

    @patch('apps.users.views.trigger_verification_email')
    def test_resend_verification_success(self, mock_trigger, api_client, unverified_user):
        """Test successful resend verification."""
        mock_trigger.return_value = None

        response = api_client.post('/api/v1/auth/resend-verification/', {
            'email': unverified_user.email
        })

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data

    def test_resend_verification_already_verified(self, api_client, unverified_user):
        """Test resend for already verified user."""
        unverified_user.email_verified = True
        unverified_user.save()

        response = api_client.post('/api/v1/auth/resend-verification/', {
            'email': unverified_user.email
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_resend_verification_user_not_found(self, db, api_client):
        """Test resend for non-existent user (should not reveal)."""
        response = api_client.post('/api/v1/auth/resend-verification/', {
            'email': 'nonexistent@test.com'
        })

        # Should return 200 to not reveal if user exists
        assert response.status_code == status.HTTP_200_OK


class TestLoginWithUnverifiedEmail:
    """Tests for login endpoint with unverified email."""

    def test_login_unverified_user_returns_error(self, api_client, unverified_user):
        """Test that login fails for unverified user with specific error."""
        response = api_client.post('/api/v1/auth/login/', {
            'email': unverified_user.email,
            'password': 'testpass123'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Check for email_not_verified indicator (DRF wraps in ErrorDetail)
        assert 'email_not_verified' in response.data

    def test_login_verified_user_succeeds(self, api_client, unverified_user):
        """Test that login succeeds for verified user."""
        unverified_user.email_verified = True
        unverified_user.save()

        response = api_client.post('/api/v1/auth/login/', {
            'email': unverified_user.email,
            'password': 'testpass123'
        })

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
