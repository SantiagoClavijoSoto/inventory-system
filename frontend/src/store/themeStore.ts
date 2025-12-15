import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { BranchBranding } from '@/types'
import { branchesApi } from '@/api/branches'

interface ThemeState {
  branding: BranchBranding | null
  isLoading: boolean
  error: string | null

  // Actions
  loadBranding: (branchId: number) => Promise<void>
  setBranding: (branding: BranchBranding | null) => void
  clearBranding: () => void
  applyTheme: (branding: BranchBranding) => void
}

// Default theme colors (blue theme)
const DEFAULT_BRANDING: BranchBranding = {
  id: 0,
  display_name: 'Sistema de Inventario',
  primary_color: '#2563eb',
  secondary_color: '#64748b',
  accent_color: '#f59e0b',
  tax_rate: 19,
  currency: 'COP',
  currency_symbol: '$',
}

// Generate color shades from a hex color
function hexToHsl(hex: string): { h: number; s: number; l: number } {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!result) return { h: 217, s: 91, l: 60 } // Default blue

  const r = parseInt(result[1], 16) / 255
  const g = parseInt(result[2], 16) / 255
  const b = parseInt(result[3], 16) / 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h = 0
  let s = 0
  const l = (max + min) / 2

  if (max !== min) {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case r:
        h = ((g - b) / d + (g < b ? 6 : 0)) / 6
        break
      case g:
        h = ((b - r) / d + 2) / 6
        break
      case b:
        h = ((r - g) / d + 4) / 6
        break
    }
  }

  return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) }
}

function generateColorShades(hex: string): Record<string, string> {
  const { h, s } = hexToHsl(hex)
  return {
    50: `hsl(${h}, ${Math.min(s + 10, 100)}%, 97%)`,
    100: `hsl(${h}, ${Math.min(s + 5, 100)}%, 93%)`,
    200: `hsl(${h}, ${s}%, 85%)`,
    300: `hsl(${h}, ${s}%, 75%)`,
    400: `hsl(${h}, ${s}%, 60%)`,
    500: `hsl(${h}, ${s}%, 50%)`,
    600: `hsl(${h}, ${s}%, 45%)`,
    700: `hsl(${h}, ${s}%, 38%)`,
    800: `hsl(${h}, ${s}%, 30%)`,
    900: `hsl(${h}, ${s}%, 23%)`,
    950: `hsl(${h}, ${s}%, 15%)`,
  }
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      branding: null,
      isLoading: false,
      error: null,

      loadBranding: async (branchId: number) => {
        set({ isLoading: true, error: null })
        try {
          const branding = await branchesApi.getBranding(branchId)
          set({ branding, isLoading: false })
          get().applyTheme(branding)
        } catch (error) {
          console.error('Failed to load branding:', error)
          set({ error: 'Error cargando tema', isLoading: false })
          // Apply default theme on error
          get().applyTheme(DEFAULT_BRANDING)
        }
      },

      setBranding: (branding) => {
        set({ branding })
        if (branding) {
          get().applyTheme(branding)
        }
      },

      clearBranding: () => {
        set({ branding: null, error: null })
        get().applyTheme(DEFAULT_BRANDING)
      },

      applyTheme: (branding: BranchBranding) => {
        const root = document.documentElement

        // Generate and apply primary color shades
        const primaryShades = generateColorShades(branding.primary_color)
        Object.entries(primaryShades).forEach(([shade, color]) => {
          root.style.setProperty(`--color-primary-${shade}`, color)
        })

        // Generate and apply secondary color shades
        const secondaryShades = generateColorShades(branding.secondary_color)
        Object.entries(secondaryShades).forEach(([shade, color]) => {
          root.style.setProperty(`--color-secondary-${shade}`, color)
        })

        // Apply accent color if present
        if (branding.accent_color) {
          const accentShades = generateColorShades(branding.accent_color)
          Object.entries(accentShades).forEach(([shade, color]) => {
            root.style.setProperty(`--color-accent-${shade}`, color)
          })
        }

        // Update favicon if available
        if (branding.favicon_url) {
          const favicon = document.querySelector<HTMLLinkElement>('link[rel="icon"]')
          if (favicon) {
            favicon.href = branding.favicon_url
          }
        }

        // Update document title
        if (branding.display_name) {
          document.title = `${branding.display_name} - Sistema de Inventario`
        }
      },
    }),
    {
      name: 'theme-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        branding: state.branding,
      }),
    }
  )
)

// Export default branding for use elsewhere
export { DEFAULT_BRANDING }
