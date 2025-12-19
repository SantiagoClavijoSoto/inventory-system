import apiClient, {
  setAccessToken,
  setRefreshToken,
  clearTokens,
  getRefreshToken,
} from './client'
import type { LoginCredentials, LoginResponse, User } from '@/types'

export interface VerifyEmailResponse {
  message: string
  access: string
  refresh: string
  user: User
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login/', credentials)
    const { access, refresh } = response.data

    setAccessToken(access)
    setRefreshToken(refresh)

    return response.data
  },

  logout: async (): Promise<void> => {
    const refreshToken = getRefreshToken()
    try {
      if (refreshToken) {
        await apiClient.post('/auth/logout/', { refresh: refreshToken })
      }
    } finally {
      clearTokens()
    }
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me/')
    return response.data
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await apiClient.patch<User>('/auth/me/', data)
    return response.data
  },

  changePassword: async (data: {
    current_password: string
    new_password: string
    new_password_confirm: string
  }): Promise<void> => {
    await apiClient.post('/auth/change-password/', data)
  },

  refreshToken: async (): Promise<string> => {
    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }
    const response = await apiClient.post<{ access: string }>('/auth/refresh/', {
      refresh: refreshToken,
    })
    setAccessToken(response.data.access)
    return response.data.access
  },

  verifyEmail: async (email: string, code: string): Promise<VerifyEmailResponse> => {
    const response = await apiClient.post<VerifyEmailResponse>('/auth/verify-email/', {
      email,
      code,
    })
    const { access, refresh } = response.data

    setAccessToken(access)
    setRefreshToken(refresh)

    return response.data
  },

  resendVerification: async (email: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/resend-verification/', {
      email,
    })
    return response.data
  },
}
