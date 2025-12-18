"""
Security Audit Logging Middleware

Logs security-relevant events for compliance and incident response:
- Authentication attempts (success/failure)
- Sensitive data access
- Administrative actions
- Suspicious activity patterns
"""

import logging
import time
import json
from typing import Callable, Optional
from django.http import HttpRequest, HttpResponse
from django.conf import settings

# Dedicated security logger
audit_logger = logging.getLogger('security.audit')


class SecurityAuditMiddleware:
    """
    Middleware for logging security-relevant HTTP requests.

    Logs:
    - All authentication endpoints
    - Admin/sensitive endpoints
    - Failed requests (4xx, 5xx)
    - Requests with suspicious patterns
    """

    # Endpoints that always get logged
    AUDIT_ENDPOINTS = [
        '/api/v1/users/login/',
        '/api/v1/users/logout/',
        '/api/v1/users/register/',
        '/api/v1/users/token/refresh/',
        '/api/v1/users/change-password/',
        '/api/v1/users/reset-password/',
    ]

    # Patterns indicating admin/sensitive operations
    SENSITIVE_PATTERNS = [
        '/admin/',
        '/api/v1/companies/',
        '/api/v1/users/',
        'delete',
        'bulk',
    ]

    # HTTP methods that modify data
    WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Start timing
        start_time = time.time()

        # Process request
        response = self.get_response(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Determine if this request should be logged
        should_log = self._should_log(request, response)

        if should_log:
            self._log_request(request, response, duration_ms)

        return response

    def _should_log(self, request: HttpRequest, response: HttpResponse) -> bool:
        """Determine if request should be logged."""
        path = request.path.lower()

        # Always log authentication endpoints
        for endpoint in self.AUDIT_ENDPOINTS:
            if endpoint in path:
                return True

        # Log all write operations to sensitive endpoints
        if request.method in self.WRITE_METHODS:
            for pattern in self.SENSITIVE_PATTERNS:
                if pattern in path:
                    return True

        # Log all failures (4xx, 5xx)
        if response.status_code >= 400:
            return True

        # Log if suspicious headers present
        if self._has_suspicious_headers(request):
            return True

        return False

    def _has_suspicious_headers(self, request: HttpRequest) -> bool:
        """Check for suspicious request patterns."""
        # SQL injection patterns in headers
        suspicious_patterns = [
            "' OR ",
            "1=1",
            "UNION SELECT",
            "<script>",
            "javascript:",
        ]

        # Check common attack vectors
        for header in ['HTTP_USER_AGENT', 'HTTP_REFERER', 'QUERY_STRING']:
            value = request.META.get(header, '').upper()
            for pattern in suspicious_patterns:
                if pattern.upper() in value:
                    return True

        return False

    def _log_request(
        self,
        request: HttpRequest,
        response: HttpResponse,
        duration_ms: float
    ) -> None:
        """Log the security event."""
        # Get user info
        user_id = None
        user_email = None
        company_id = None

        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            user_email = getattr(request.user, 'email', None)
            company_id = getattr(request.user, 'company_id', None)

        # Build log entry
        log_entry = {
            'event_type': self._get_event_type(request, response),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'request': {
                'method': request.method,
                'path': request.path,
                'query_string': request.META.get('QUERY_STRING', '')[:500],
                'content_type': request.content_type,
            },
            'response': {
                'status_code': response.status_code,
                'duration_ms': round(duration_ms, 2),
            },
            'user': {
                'id': user_id,
                'email': user_email,
                'company_id': company_id,
            },
            'client': {
                'ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            },
        }

        # Log at appropriate level
        if response.status_code >= 500:
            audit_logger.error(json.dumps(log_entry))
        elif response.status_code >= 400:
            audit_logger.warning(json.dumps(log_entry))
        else:
            audit_logger.info(json.dumps(log_entry))

    def _get_event_type(self, request: HttpRequest, response: HttpResponse) -> str:
        """Categorize the security event."""
        path = request.path.lower()

        if 'login' in path:
            return 'AUTH_LOGIN_SUCCESS' if response.status_code < 400 else 'AUTH_LOGIN_FAILED'
        elif 'logout' in path:
            return 'AUTH_LOGOUT'
        elif 'password' in path:
            return 'AUTH_PASSWORD_CHANGE'
        elif 'register' in path:
            return 'AUTH_REGISTER'
        elif response.status_code == 401:
            return 'AUTH_UNAUTHORIZED'
        elif response.status_code == 403:
            return 'AUTH_FORBIDDEN'
        elif response.status_code >= 500:
            return 'ERROR_SERVER'
        elif request.method == 'DELETE':
            return 'DATA_DELETE'
        elif request.method in ('POST', 'PUT', 'PATCH'):
            return 'DATA_MODIFY'
        else:
            return 'ACCESS'

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get the real client IP, considering proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class FailedLoginTracker:
    """
    Track failed login attempts for rate limiting and alerting.

    This is a simple in-memory implementation.
    For production, use Redis or database storage.
    """

    # In-memory storage (use Redis in production)
    _failed_attempts: dict = {}

    # Thresholds
    LOCKOUT_THRESHOLD = 5
    LOCKOUT_DURATION_SECONDS = 900  # 15 minutes
    ALERT_THRESHOLD = 10  # Alert after this many failures

    @classmethod
    def record_failure(cls, ip: str, email: Optional[str] = None) -> dict:
        """Record a failed login attempt."""
        key = f"{ip}:{email or 'unknown'}"
        current_time = time.time()

        if key not in cls._failed_attempts:
            cls._failed_attempts[key] = {
                'count': 0,
                'first_attempt': current_time,
                'last_attempt': current_time,
            }

        cls._failed_attempts[key]['count'] += 1
        cls._failed_attempts[key]['last_attempt'] = current_time

        attempt_data = cls._failed_attempts[key]

        # Log alert if threshold exceeded
        if attempt_data['count'] >= cls.ALERT_THRESHOLD:
            audit_logger.critical(json.dumps({
                'event_type': 'SECURITY_ALERT',
                'alert': 'BRUTE_FORCE_DETECTED',
                'ip': ip,
                'email': email,
                'attempts': attempt_data['count'],
                'duration_seconds': current_time - attempt_data['first_attempt'],
            }))

        return {
            'is_locked': attempt_data['count'] >= cls.LOCKOUT_THRESHOLD,
            'attempts': attempt_data['count'],
            'remaining_lockout': cls._get_remaining_lockout(key),
        }

    @classmethod
    def _get_remaining_lockout(cls, key: str) -> int:
        """Get remaining lockout time in seconds."""
        if key not in cls._failed_attempts:
            return 0

        data = cls._failed_attempts[key]
        if data['count'] < cls.LOCKOUT_THRESHOLD:
            return 0

        elapsed = time.time() - data['last_attempt']
        remaining = cls.LOCKOUT_DURATION_SECONDS - elapsed
        return max(0, int(remaining))

    @classmethod
    def is_locked(cls, ip: str, email: Optional[str] = None) -> bool:
        """Check if IP/email combination is locked."""
        key = f"{ip}:{email or 'unknown'}"
        return cls._get_remaining_lockout(key) > 0

    @classmethod
    def clear(cls, ip: str, email: Optional[str] = None) -> None:
        """Clear failed attempts after successful login."""
        key = f"{ip}:{email or 'unknown'}"
        cls._failed_attempts.pop(key, None)
