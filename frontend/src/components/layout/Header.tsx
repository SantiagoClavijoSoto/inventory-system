import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '@/store/authStore'
import { useThemeStore } from '@/store/themeStore'
import { branchesApi } from '@/api/branches'
import { Bell, ChevronDown, Building2, Check, Loader2 } from 'lucide-react'
import type { Branch } from '@/types'

export function Header() {
  const { user, currentBranch, setCurrentBranch } = useAuthStore()
  const { loadBranding, branding } = useThemeStore()
  const [showBranchSelector, setShowBranchSelector] = useState(false)
  const [branches, setBranches] = useState<Branch[]>([])
  const [isLoadingBranches, setIsLoadingBranches] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch branches on mount
  useEffect(() => {
    const fetchBranches = async () => {
      setIsLoadingBranches(true)
      try {
        const response = await branchesApi.getAll({ is_active: true })
        setBranches(response.results)

        // Auto-select first branch if none selected
        if (!currentBranch && response.results.length > 0) {
          const defaultBranch = response.results.find(b => b.is_main) || response.results[0]
          handleBranchSelect(defaultBranch)
        }
      } catch (error) {
        console.error('Error fetching branches:', error)
      } finally {
        setIsLoadingBranches(false)
      }
    }
    fetchBranches()
  }, [])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowBranchSelector(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleBranchSelect = async (branch: Branch) => {
    setCurrentBranch(branch)
    setShowBranchSelector(false)
    // Load the theme for the selected branch
    await loadBranding(branch.id)
  }

  // Get display name from branding or branch
  const displayBranchName = branding?.display_name || currentBranch?.name || 'Seleccionar sucursal'

  return (
    <header className="h-16 bg-white border-b border-secondary-200 flex items-center justify-between px-6">
      {/* Page title will be set by each page */}
      <div>
        <h1 className="text-xl font-semibold text-secondary-900">
          {/* This can be populated via context or props */}
        </h1>
      </div>

      <div className="flex items-center gap-4">
        {/* Branch Selector */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowBranchSelector(!showBranchSelector)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-secondary-700 hover:bg-secondary-100 rounded-lg transition-colors"
          >
            <Building2 className="w-4 h-4 text-primary-600" />
            <span className="max-w-[200px] truncate">{displayBranchName}</span>
            <ChevronDown className={`w-4 h-4 transition-transform ${showBranchSelector ? 'rotate-180' : ''}`} />
          </button>

          {showBranchSelector && (
            <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-secondary-200 py-1 z-50 max-h-80 overflow-y-auto">
              {isLoadingBranches ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
                </div>
              ) : branches.length === 0 ? (
                <div className="px-4 py-3 text-sm text-secondary-500 text-center">
                  No hay sucursales disponibles
                </div>
              ) : (
                branches.map((branch) => (
                  <button
                    key={branch.id}
                    onClick={() => handleBranchSelect(branch)}
                    className={`w-full px-4 py-2 text-left text-sm flex items-center justify-between gap-2 transition-colors ${
                      currentBranch?.id === branch.id
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-secondary-700 hover:bg-secondary-50'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">
                        {branch.display_name || branch.name}
                      </div>
                      <div className="text-xs text-secondary-400 flex items-center gap-2">
                        <span>{branch.code}</span>
                        {branch.is_main && (
                          <span className="px-1.5 py-0.5 bg-primary-100 text-primary-600 rounded text-[10px] font-medium">
                            Principal
                          </span>
                        )}
                      </div>
                    </div>
                    {currentBranch?.id === branch.id && (
                      <Check className="w-4 h-4 text-primary-600 flex-shrink-0" />
                    )}
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* Notifications */}
        <button className="relative p-2 text-secondary-500 hover:text-secondary-700 hover:bg-secondary-100 rounded-lg transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-danger-500 rounded-full" />
        </button>

        {/* User Avatar */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
            <span className="text-sm text-primary-700 font-medium">
              {user?.first_name?.[0]}
              {user?.last_name?.[0]}
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
