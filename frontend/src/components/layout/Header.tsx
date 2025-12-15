import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useThemeStore } from '@/store/themeStore'
import { branchesApi } from '@/api/branches'
import { alertsApi, type Alert, type AlertUnreadCount } from '@/api/alerts'
import {
  Bell,
  ChevronDown,
  Building2,
  Check,
  Loader2,
  AlertTriangle,
  Package,
  XCircle,
  Clock,
  CheckCircle2,
} from 'lucide-react'
import type { Branch } from '@/types'

// Severity colors and icons
const severityConfig = {
  critical: { color: 'text-danger-600', bg: 'bg-danger-100', icon: XCircle },
  high: { color: 'text-danger-500', bg: 'bg-danger-50', icon: AlertTriangle },
  medium: { color: 'text-warning-500', bg: 'bg-warning-50', icon: AlertTriangle },
  low: { color: 'text-secondary-500', bg: 'bg-secondary-100', icon: Package },
}

const alertTypeIcons: Record<string, typeof Package> = {
  low_stock: Package,
  out_of_stock: XCircle,
  overstock: Package,
}

export function Header() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user, currentBranch, setCurrentBranch } = useAuthStore()
  const { loadBranding, branding } = useThemeStore()
  const [showBranchSelector, setShowBranchSelector] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const [branches, setBranches] = useState<Branch[]>([])
  const [isLoadingBranches, setIsLoadingBranches] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const notificationRef = useRef<HTMLDivElement>(null)

  // Fetch unread alert count
  const { data: unreadCount } = useQuery<AlertUnreadCount>({
    queryKey: ['alerts', 'unread-count', currentBranch?.id],
    queryFn: () => alertsApi.getUnreadCount(currentBranch?.id),
    refetchInterval: 30000, // Refetch every 30 seconds
    enabled: !!currentBranch,
  })

  // Fetch recent alerts for dropdown
  const { data: recentAlerts, isLoading: isLoadingAlerts } = useQuery<Alert[]>({
    queryKey: ['alerts', 'recent', currentBranch?.id],
    queryFn: () =>
      alertsApi.getAll({
        branch_id: currentBranch?.id,
        status: 'active',
        limit: 5,
      }),
    enabled: showNotifications && !!currentBranch,
  })

  // Mark as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: alertsApi.markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })

  // Mark all as read mutation
  const markAllAsReadMutation = useMutation({
    mutationFn: () => alertsApi.markAllAsRead(currentBranch?.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })

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

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowBranchSelector(false)
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setShowNotifications(false)
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

  const handleAlertClick = (alert: Alert) => {
    // Mark as read if not already
    if (!alert.is_read) {
      markAsReadMutation.mutate(alert.id)
    }
    setShowNotifications(false)
    // Navigate to alerts page
    navigate('/alerts')
  }

  const handleViewAll = () => {
    setShowNotifications(false)
    navigate('/alerts')
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Ahora'
    if (diffMins < 60) return `Hace ${diffMins}m`
    if (diffHours < 24) return `Hace ${diffHours}h`
    return `Hace ${diffDays}d`
  }

  // Get display name from branding or branch
  const displayBranchName = branding?.display_name || currentBranch?.name || 'Seleccionar sucursal'

  // Calculate total unread
  const totalUnread = unreadCount?.total || 0

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
        <div className="relative" ref={notificationRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 text-secondary-500 hover:text-secondary-700 hover:bg-secondary-100 rounded-lg transition-colors"
          >
            <Bell className="w-5 h-5" />
            {totalUnread > 0 && (
              <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center px-1 text-[10px] font-bold text-white bg-danger-500 rounded-full">
                {totalUnread > 99 ? '99+' : totalUnread}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-secondary-200 z-50">
              {/* Header */}
              <div className="px-4 py-3 border-b border-secondary-200 flex items-center justify-between">
                <h3 className="font-semibold text-secondary-900">Notificaciones</h3>
                {totalUnread > 0 && (
                  <button
                    onClick={() => markAllAsReadMutation.mutate()}
                    disabled={markAllAsReadMutation.isPending}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {markAllAsReadMutation.isPending ? 'Marcando...' : 'Marcar todo como leído'}
                  </button>
                )}
              </div>

              {/* Alert List */}
              <div className="max-h-96 overflow-y-auto">
                {isLoadingAlerts ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
                  </div>
                ) : !recentAlerts || recentAlerts.length === 0 ? (
                  <div className="py-8 text-center">
                    <CheckCircle2 className="w-10 h-10 mx-auto mb-2 text-success-500" />
                    <p className="text-secondary-600 font-medium">¡Todo en orden!</p>
                    <p className="text-sm text-secondary-400">No hay alertas activas</p>
                  </div>
                ) : (
                  recentAlerts.map((alert) => {
                    const config = severityConfig[alert.severity]
                    const Icon = alertTypeIcons[alert.alert_type] || AlertTriangle
                    return (
                      <button
                        key={alert.id}
                        onClick={() => handleAlertClick(alert)}
                        className={`w-full px-4 py-3 text-left border-b border-secondary-100 last:border-b-0 hover:bg-secondary-50 transition-colors ${
                          !alert.is_read ? 'bg-primary-50/50' : ''
                        }`}
                      >
                        <div className="flex gap-3">
                          <div className={`p-2 rounded-lg ${config.bg}`}>
                            <Icon className={`w-4 h-4 ${config.color}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className={`text-sm font-medium text-secondary-900 truncate ${!alert.is_read ? 'font-semibold' : ''}`}>
                                {alert.title}
                              </p>
                              {!alert.is_read && (
                                <span className="w-2 h-2 bg-primary-500 rounded-full flex-shrink-0" />
                              )}
                            </div>
                            <p className="text-xs text-secondary-500 mt-0.5 line-clamp-2">
                              {alert.message}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <Clock className="w-3 h-3 text-secondary-400" />
                              <span className="text-[10px] text-secondary-400">
                                {formatTimeAgo(alert.created_at)}
                              </span>
                              {alert.branch_name && (
                                <>
                                  <span className="text-secondary-300">•</span>
                                  <span className="text-[10px] text-secondary-400">
                                    {alert.branch_name}
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </button>
                    )
                  })
                )}
              </div>

              {/* Footer */}
              <div className="px-4 py-3 border-t border-secondary-200">
                <button
                  onClick={handleViewAll}
                  className="w-full text-center text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  Ver todas las alertas
                </button>
              </div>
            </div>
          )}
        </div>

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
