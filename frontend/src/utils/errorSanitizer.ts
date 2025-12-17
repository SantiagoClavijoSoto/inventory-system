/**
 * Error message sanitization utility.
 * Prevents exposure of sensitive backend details to users.
 */

// Known safe error patterns that can be shown to users
const SAFE_ERROR_PATTERNS = [
  /^(no|ya|el|la|los|las|este|esta|error|stock|cantidad|usuario|contraseña|email|sucursal|producto|proveedor|orden|permiso)/i,
  /insuficiente/i,
  /no encontrad/i,
  /no existe/i,
  /ya existe/i,
  /duplicad/i,
  /inválid/i,
  /requerid/i,
  /debe ser/i,
  /no puede/i,
  /no tienes/i,
  /credenciales/i,
  /contraseña incorrecta/i,
  /sesión/i,
]

// Patterns that indicate sensitive/internal errors that should NOT be shown
const UNSAFE_PATTERNS = [
  /traceback/i,
  /exception/i,
  /stack trace/i,
  /line \d+/i,
  /file ".*"/i,
  /\.py/i,
  /django\./i,
  /sql/i,
  /query/i,
  /database/i,
  /connection/i,
  /internal server/i,
  /TypeError/i,
  /ValueError/i,
  /KeyError/i,
  /AttributeError/i,
  /ImportError/i,
  /ModuleNotFoundError/i,
]

// Default messages by error type
const DEFAULT_MESSAGES: Record<string, string> = {
  create: 'Error al crear el registro',
  update: 'Error al actualizar el registro',
  delete: 'Error al eliminar el registro',
  fetch: 'Error al cargar los datos',
  auth: 'Error de autenticación',
  permission: 'No tienes permisos para realizar esta acción',
  notFound: 'Recurso no encontrado',
  server: 'Error del servidor. Por favor intenta más tarde.',
  network: 'Error de conexión. Verifica tu conexión a internet.',
  default: 'Ha ocurrido un error. Por favor intenta de nuevo.',
}

/**
 * Check if an error message is safe to display to users
 */
function isSafeMessage(message: string): boolean {
  // Check for unsafe patterns first
  if (UNSAFE_PATTERNS.some(pattern => pattern.test(message))) {
    return false
  }

  // Check if it matches known safe patterns
  return SAFE_ERROR_PATTERNS.some(pattern => pattern.test(message))
}

/**
 * Sanitize an error message for display to users.
 * Returns safe business-level error messages, hiding technical details.
 */
export function sanitizeErrorMessage(
  rawMessage: string | undefined | null,
  context?: 'create' | 'update' | 'delete' | 'fetch' | 'auth' | 'default'
): string {
  // No message provided
  if (!rawMessage || typeof rawMessage !== 'string') {
    return DEFAULT_MESSAGES[context || 'default']
  }

  // Trim and check length (very long messages are suspicious)
  const trimmed = rawMessage.trim()
  if (trimmed.length > 200) {
    console.warn('Error message too long, using default:', trimmed.substring(0, 100))
    return DEFAULT_MESSAGES[context || 'default']
  }

  // Check if message is safe to display
  if (isSafeMessage(trimmed)) {
    return trimmed
  }

  // Log the unsafe message for debugging (only in development)
  if (import.meta.env.DEV) {
    console.warn('Sanitized unsafe error message:', rawMessage)
  }

  return DEFAULT_MESSAGES[context || 'default']
}

/**
 * Extract and sanitize error message from API response
 */
export function extractErrorMessage(
  error: unknown,
  context?: 'create' | 'update' | 'delete' | 'fetch' | 'auth' | 'default'
): string {
  // Handle axios error structure
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as { response?: { data?: { error?: string; detail?: string; message?: string } } }
    const data = axiosError.response?.data
    const rawMessage = data?.error || data?.detail || data?.message
    return sanitizeErrorMessage(rawMessage, context)
  }

  // Handle string error
  if (typeof error === 'string') {
    return sanitizeErrorMessage(error, context)
  }

  // Handle Error object
  if (error instanceof Error) {
    return sanitizeErrorMessage(error.message, context)
  }

  return DEFAULT_MESSAGES[context || 'default']
}

export default sanitizeErrorMessage
