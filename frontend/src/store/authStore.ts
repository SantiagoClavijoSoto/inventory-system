import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { User, Branch } from '@/types'
import { authApi } from '@/api/auth'
import { getAccessToken, clearTokens } from '@/api/client'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  currentBranch: Branch | null

  // Actions
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  setUser: (user: User | null) => void
  setCurrentBranch: (branch: Branch | null) => void
  hasPermission: (permission: string) => boolean
  hasModulePermission: (module: string) => boolean
  canAccessBranch: (branchId: number) => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      currentBranch: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          const response = await authApi.login({ email, password })
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: async () => {
        set({ isLoading: true })
        try {
          await authApi.logout()
        } finally {
          clearTokens()
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            currentBranch: null,
          })
        }
      },

      checkAuth: async () => {
        const token = getAccessToken()
        if (!token) {
          set({ isAuthenticated: false, isLoading: false, user: null })
          return
        }

        try {
          const user = await authApi.getMe()
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch {
          clearTokens()
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },

      setUser: (user) => set({ user }),

      setCurrentBranch: (branch) => set({ currentBranch: branch }),

      hasPermission: (permission: string) => {
        const { user } = get()
        if (!user) return false
        if (user.role?.role_type === 'admin') return true
        return user.permissions?.includes(permission) ?? false
      },

      hasModulePermission: (module: string) => {
        const { user } = get()
        if (!user) return false
        if (user.role?.role_type === 'admin') return true
        return user.permissions?.some((p) => p.startsWith(`${module}:`)) ?? false
      },

      canAccessBranch: (branchId: number) => {
        const { user } = get()
        if (!user) return false
        if (user.role?.role_type === 'admin') return true
        return user.allowed_branches?.includes(branchId) ?? false
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentBranch: state.currentBranch,
      }),
    }
  )
)

// Hook for checking permissions
export const usePermission = (permission: string): boolean => {
  return useAuthStore((state) => state.hasPermission(permission))
}

// Hook for checking module access
export const useModulePermission = (module: string): boolean => {
  return useAuthStore((state) => state.hasModulePermission(module))
}
