"""
Security-focused input validation utilities.

Provides strict type validation to prevent injection attacks
and ensure data integrity before database operations.
"""

from typing import Any, Optional, List, Dict, Type, Union
from decimal import Decimal, InvalidOperation
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
import re


class StrictTypeValidator:
    """
    Strict type validation for API inputs.

    Usage:
        validator = StrictTypeValidator(request.data)
        product_id = validator.get_int('product_id', required=True)
        quantity = validator.get_positive_int('quantity', required=True)
        price = validator.get_decimal('price', min_value=0)
    """

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.errors: Dict[str, List[str]] = {}

    def get_int(
        self,
        field: str,
        required: bool = False,
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> Optional[int]:
        """Get and validate an integer field."""
        value = self.data.get(field)

        if value is None or value == '':
            if required:
                self._add_error(field, 'Este campo es requerido.')
                return None
            return default

        try:
            int_value = int(value)
        except (TypeError, ValueError):
            self._add_error(field, f'Se esperaba un número entero, se recibió: {type(value).__name__}')
            return default

        if min_value is not None and int_value < min_value:
            self._add_error(field, f'El valor debe ser mayor o igual a {min_value}.')
        if max_value is not None and int_value > max_value:
            self._add_error(field, f'El valor debe ser menor o igual a {max_value}.')

        return int_value

    def get_positive_int(
        self,
        field: str,
        required: bool = False,
        default: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> Optional[int]:
        """Get and validate a positive integer (>= 0)."""
        return self.get_int(field, required, default, min_value=0, max_value=max_value)

    def get_decimal(
        self,
        field: str,
        required: bool = False,
        default: Optional[Decimal] = None,
        min_value: Optional[Decimal] = None,
        max_value: Optional[Decimal] = None,
        max_digits: int = 12,
        decimal_places: int = 2,
    ) -> Optional[Decimal]:
        """Get and validate a decimal field."""
        value = self.data.get(field)

        if value is None or value == '':
            if required:
                self._add_error(field, 'Este campo es requerido.')
                return None
            return default

        try:
            decimal_value = Decimal(str(value))
        except (TypeError, ValueError, InvalidOperation):
            self._add_error(field, f'Se esperaba un número decimal válido.')
            return default

        # Check precision
        sign, digits, exponent = decimal_value.as_tuple()
        total_digits = len(digits)
        decimal_count = -exponent if exponent < 0 else 0

        if total_digits > max_digits:
            self._add_error(field, f'Máximo {max_digits} dígitos permitidos.')
        if decimal_count > decimal_places:
            self._add_error(field, f'Máximo {decimal_places} decimales permitidos.')

        if min_value is not None and decimal_value < min_value:
            self._add_error(field, f'El valor debe ser mayor o igual a {min_value}.')
        if max_value is not None and decimal_value > max_value:
            self._add_error(field, f'El valor debe ser menor o igual a {max_value}.')

        return decimal_value

    def get_string(
        self,
        field: str,
        required: bool = False,
        default: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        strip: bool = True,
    ) -> Optional[str]:
        """Get and validate a string field."""
        value = self.data.get(field)

        if value is None:
            if required:
                self._add_error(field, 'Este campo es requerido.')
                return None
            return default

        if not isinstance(value, str):
            self._add_error(field, f'Se esperaba texto, se recibió: {type(value).__name__}')
            return default

        if strip:
            value = value.strip()

        if value == '':
            if required:
                self._add_error(field, 'Este campo no puede estar vacío.')
                return None
            return default

        if min_length is not None and len(value) < min_length:
            self._add_error(field, f'Mínimo {min_length} caracteres requeridos.')
        if max_length is not None and len(value) > max_length:
            self._add_error(field, f'Máximo {max_length} caracteres permitidos.')
        if pattern is not None and not re.match(pattern, value):
            self._add_error(field, 'Formato inválido.')

        return value

    def get_email(
        self,
        field: str,
        required: bool = False,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """Get and validate an email field."""
        value = self.get_string(field, required, default, max_length=254)

        if value is None:
            return default

        try:
            validate_email(value)
        except DjangoValidationError:
            self._add_error(field, 'Email inválido.')
            return default

        return value.lower()

    def get_bool(
        self,
        field: str,
        required: bool = False,
        default: Optional[bool] = None,
    ) -> Optional[bool]:
        """Get and validate a boolean field."""
        value = self.data.get(field)

        if value is None:
            if required:
                self._add_error(field, 'Este campo es requerido.')
                return None
            return default

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'si'):
                return True
            if value.lower() in ('false', '0', 'no'):
                return False

        self._add_error(field, 'Se esperaba un valor booleano.')
        return default

    def get_choice(
        self,
        field: str,
        choices: List[str],
        required: bool = False,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """Get and validate a choice field."""
        value = self.get_string(field, required, default)

        if value is None:
            return default

        if value not in choices:
            self._add_error(field, f'Valor inválido. Opciones: {", ".join(choices)}')
            return default

        return value

    def get_list_of_ints(
        self,
        field: str,
        required: bool = False,
        default: Optional[List[int]] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> Optional[List[int]]:
        """Get and validate a list of integers."""
        value = self.data.get(field)

        if value is None:
            if required:
                self._add_error(field, 'Este campo es requerido.')
                return None
            return default or []

        if not isinstance(value, list):
            self._add_error(field, 'Se esperaba una lista.')
            return default or []

        if min_length is not None and len(value) < min_length:
            self._add_error(field, f'Mínimo {min_length} elementos requeridos.')
        if max_length is not None and len(value) > max_length:
            self._add_error(field, f'Máximo {max_length} elementos permitidos.')

        result = []
        for i, item in enumerate(value):
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                self._add_error(field, f'Elemento {i} debe ser un número entero.')
                return default or []

        return result

    def _add_error(self, field: str, message: str) -> None:
        """Add an error for a field."""
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(message)

    def is_valid(self) -> bool:
        """Check if validation passed."""
        return len(self.errors) == 0

    def raise_if_invalid(self) -> None:
        """Raise ValidationError if validation failed."""
        if not self.is_valid():
            raise ValidationError(self.errors)


class SecureIDField(serializers.IntegerField):
    """
    Secure integer ID field that prevents injection attempts.

    Ensures the value is a valid positive integer and within
    reasonable bounds for database IDs.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('min_value', 1)
        kwargs.setdefault('max_value', 2147483647)  # Max INT in MySQL
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        # Reject any non-numeric strings that might be injection attempts
        if isinstance(data, str):
            if not data.isdigit():
                self.fail('invalid')
        return super().to_internal_value(data)


class SecureDecimalField(serializers.DecimalField):
    """
    Secure decimal field with strict validation.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('max_digits', 12)
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('min_value', Decimal('0'))
        kwargs.setdefault('max_value', Decimal('999999999.99'))
        super().__init__(**kwargs)


class SafeSearchField(serializers.CharField):
    """
    Safe search field that sanitizes input for LIKE queries.

    While Django ORM protects against SQL injection, this provides
    additional sanitization for search terms.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', 100)
        kwargs.setdefault('trim_whitespace', True)
        kwargs.setdefault('allow_blank', True)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        # Remove characters that could be problematic in LIKE patterns
        # (though Django ORM handles this, defense in depth)
        if value:
            value = re.sub(r'[%_\\]', '', value)
        return value
