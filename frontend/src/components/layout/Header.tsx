import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import { Bell, ChevronDown, Building2 } from 'lucide-react'

export function Header() {
  const { user, currentBranch, setCurrentBranch } = useAuthStore()
  const [showBranchSelector, setShowBranchSelector] = useState(false)

  // Mock branches for now - will be fetched from API later
  const branches = [
    { id: 1, name: 'Sucursal Principal', code: 'SUC001' },
    { id: 2, name: 'Sucursal Norte', code: 'SUC002' },
    { id: 3, name: 'Sucursal Sur', code: 'SUC003' },
  ]

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
        <div className="relative">
          <button
            onClick={() => setShowBranchSelector(!showBranchSelector)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-secondary-700 hover:bg-secondary-100 rounded-lg transition-colors"
          >
            <Building2 className="w-4 h-4" />
            <span>{currentBranch?.name || 'Seleccionar sucursal'}</span>
            <ChevronDown className="w-4 h-4" />
          </button>

          {showBranchSelector && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-secondary-200 py-1 z-50">
              {branches.map((branch) => (
                <button
                  key={branch.id}
                  onClick={() => {
                    setCurrentBranch(branch as any)
                    setShowBranchSelector(false)
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-secondary-700 hover:bg-secondary-50"
                >
                  <span className="font-medium">{branch.name}</span>
                  <span className="text-secondary-400 ml-2">({branch.code})</span>
                </button>
              ))}
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
