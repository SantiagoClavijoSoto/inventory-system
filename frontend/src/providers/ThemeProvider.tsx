import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { useThemeStore, DEFAULT_BRANDING } from '@/store/themeStore'

interface ThemeProviderProps {
  children: React.ReactNode
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const { currentBranch, isAuthenticated } = useAuthStore()
  const { loadBranding, applyTheme, branding } = useThemeStore()

  // Load theme when branch changes
  useEffect(() => {
    if (isAuthenticated && currentBranch?.id) {
      loadBranding(currentBranch.id)
    } else if (!isAuthenticated) {
      // Reset to default theme when logged out
      applyTheme(DEFAULT_BRANDING)
    }
  }, [currentBranch?.id, isAuthenticated, loadBranding, applyTheme])

  // Apply cached theme on initial load
  useEffect(() => {
    if (branding) {
      applyTheme(branding)
    } else {
      applyTheme(DEFAULT_BRANDING)
    }
  }, [])

  return <>{children}</>
}
