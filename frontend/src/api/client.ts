import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import toast from 'react-hot-toast'
import { sanitizeErrorMessage } from '../utils/errorSanitizer'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token management - Uses sessionStorage for better security than localStorage
// sessionStorage is cleared when the browser tab closes, reducing XSS attack window
let accessToken: string | null = null

export const setAccessToken = (token: string | null) => {
  accessToken = token
  if (token) {
    sessionStorage.setItem('access_token', token)
  } else {
    sessionStorage.removeItem('access_token')
  }
}

export const getAccessToken = (): string | null => {
  if (!accessToken) {
    accessToken = sessionStorage.getItem('access_token')
  }
  return accessToken
}

export const setRefreshToken = (token: string | null) => {
  if (token) {
    sessionStorage.setItem('refresh_token', token)
  } else {
    sessionStorage.removeItem('refresh_token')
  }
}

export const getRefreshToken = (): string | null => {
  return sessionStorage.getItem('refresh_token')
}

export const clearTokens = () => {
  accessToken = null
  sessionStorage.removeItem('access_token')
  sessionStorage.removeItem('refresh_token')
}

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Public endpoints that should NOT trigger automatic 401 handling/redirect
const PUBLIC_AUTH_ENDPOINTS = [
  '/auth/login/',
  '/auth/verify-email/',
  '/auth/resend-verification/',
  '/auth/refresh/',
]

// Response interceptor - Handle errors and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Check if this is a public endpoint that shouldn't trigger auth redirect
    const isPublicEndpoint = PUBLIC_AUTH_ENDPOINTS.some(
      endpoint => originalRequest.url?.includes(endpoint)
    )

    // Handle 401 - Try to refresh token (skip for public endpoints)
    if (error.response?.status === 401 && !originalRequest._retry && !isPublicEndpoint) {
      originalRequest._retry = true

      const refreshToken = getRefreshToken()
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/auth/refresh/`, {
            refresh: refreshToken,
          })
          const newAccessToken = response.data.access
          setAccessToken(newAccessToken)

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          }
          return apiClient(originalRequest)
        } catch (refreshError) {
          // Refresh failed - clear tokens and redirect to login
          clearTokens()
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        // No refresh token - redirect to login
        clearTokens()
        window.location.href = '/login'
      }
    }

    // Handle other errors with sanitized messages
    if (error.response?.status === 400) {
      const errorData = error.response.data as { error?: string; detail?: string; message?: string }
      const rawMessage = errorData?.error || errorData?.detail || errorData?.message
      if (rawMessage) {
        toast.error(sanitizeErrorMessage(rawMessage))
      }
    } else if (error.response?.status === 403) {
      toast.error('No tienes permisos para realizar esta acción')
    } else if (error.response?.status === 404) {
      toast.error('Recurso no encontrado')
    } else if (error.response?.status === 500) {
      toast.error('Error del servidor. Por favor intenta más tarde.')
    } else if (!error.response) {
      toast.error('Error de conexión. Verifica tu conexión a internet.')
    }

    return Promise.reject(error)
  }
)

export { apiClient }
export default apiClient
