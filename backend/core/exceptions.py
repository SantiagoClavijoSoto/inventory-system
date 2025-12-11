"""
Custom exceptions for the API.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class InsufficientStockError(APIException):
    """Raised when there's not enough stock for an operation."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Stock insuficiente para completar la operación.'
    default_code = 'insufficient_stock'


class InvalidBarcodeError(APIException):
    """Raised when a barcode is invalid or not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Código de barras no encontrado.'
    default_code = 'invalid_barcode'


class SaleAlreadyVoidedError(APIException):
    """Raised when trying to void an already voided sale."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Esta venta ya ha sido anulada.'
    default_code = 'sale_already_voided'


class ShiftNotActiveError(APIException):
    """Raised when an employee tries to perform an action without an active shift."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'No hay un turno activo. Por favor registre su entrada primero.'
    default_code = 'shift_not_active'


class ShiftAlreadyActiveError(APIException):
    """Raised when an employee tries to clock in when already clocked in."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Ya tiene un turno activo. Por favor registre su salida primero.'
    default_code = 'shift_already_active'


class BranchMismatchError(APIException):
    """Raised when an operation involves mismatched branches."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Las sucursales no coinciden para esta operación.'
    default_code = 'branch_mismatch'


class InsufficientPermissionsError(APIException):
    """Raised when user doesn't have required permissions."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'No tiene permisos suficientes para realizar esta acción.'
    default_code = 'insufficient_permissions'


class StockTransferError(APIException):
    """Raised when a stock transfer operation fails."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error al transferir stock entre sucursales.'
    default_code = 'stock_transfer_error'


class ValidationError(APIException):
    """Raised when validation fails for an operation."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error de validación.'
    default_code = 'validation_error'
