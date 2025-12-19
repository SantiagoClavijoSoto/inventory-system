import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  alertsApi,
  alertPreferencesApi,
  activityLogApi,
  type AlertListParams,
  type Alert,
  type AlertSeverity,
  type AlertStatus,
  type AlertType,
  type ActivityModule,
} from '@/api/alerts'
import { useIsPlatformAdmin, useIsAdmin } from '@/store/authStore'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import {
  Bell,
  BellOff,
  AlertTriangle,
  AlertCircle,
  Info,
  XCircle,
  Check,
  CheckCheck,
  Eye,
  X,
  Filter,
  RefreshCw,
  Package,
  DollarSign,
  Clock,
  Settings,
  CreditCard,
  CalendarClock,
  UserPlus,
  Ban,
  PauseCircle,
  ArrowRightLeft,
  TrendingDown,
  Activity,
  ArrowUp,
  UserX,
  AlertOctagon,
  Gauge,
  Users,
  Store,
  ShoppingCart,
  Truck,
  FileText,
} from 'lucide-react'

type TabType = 'alerts' | 'activity'

export function Alerts() {
  const queryClient = useQueryClient()
  const isPlatformAdmin = useIsPlatformAdmin()
  const isAdmin = useIsAdmin()
  const [activeTab, setActiveTab] = useState<TabType>('alerts')
  const [filters, setFilters] = useState<AlertListParams>({
    limit: 50,
  })
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
  const [showPreferences, setShowPreferences] = useState(false)
  const [selectedAlerts, setSelectedAlerts] = useState<number[]>([])

  // Queries
  const { data: alerts, isLoading, refetch } = useQuery({
    queryKey: ['alerts', filters],
    queryFn: () => alertsApi.getAll(filters),
  })

  const { data: unreadCount } = useQuery({
    queryKey: ['alerts-unread-count'],
    queryFn: () => alertsApi.getUnreadCount(),
  })

  const { data: preferences } = useQuery({
    queryKey: ['alert-preferences'],
    queryFn: () => alertPreferencesApi.get(),
  })

  // Mutations
  const markReadMutation = useMutation({
    mutationFn: (id: number) => alertsApi.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['alerts-unread-count'] })
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => alertsApi.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['alerts-unread-count'] })
    },
  })

  const acknowledgeMutation = useMutation({
    mutationFn: (id: number) => alertsApi.acknowledge(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      setSelectedAlert(null)
    },
  })

  const resolveMutation = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes?: string }) =>
      alertsApi.resolve(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['alerts-unread-count'] })
      setSelectedAlert(null)
    },
  })

  const dismissMutation = useMutation({
    mutationFn: (id: number) => alertsApi.dismiss(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['alerts-unread-count'] })
      setSelectedAlert(null)
    },
  })

  const bulkResolveMutation = useMutation({
    mutationFn: (alertIds: number[]) => alertsApi.bulkResolve(alertIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['alerts-unread-count'] })
      setSelectedAlerts([])
    },
  })

  const handleFilterChange = (key: keyof AlertListParams, value: string | boolean | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value === '' ? undefined : value,
    }))
  }

  const handleSelectAll = () => {
    if (selectedAlerts.length === alerts?.length) {
      setSelectedAlerts([])
    } else {
      setSelectedAlerts(alerts?.map((a) => a.id) || [])
    }
  }

  const handleSelectAlert = (id: number) => {
    setSelectedAlerts((prev) =>
      prev.includes(id) ? prev.filter((aid) => aid !== id) : [...prev, id]
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Alertas y Actividad</h1>
          <p className="text-secondary-500 mt-1">
            Gestiona las alertas del sistema y visualiza la actividad de usuarios
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => activeTab === 'alerts' ? refetch() : queryClient.invalidateQueries({ queryKey: ['activity-logs'] })}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualizar
          </Button>
          {activeTab === 'alerts' && (
            <Button variant="outline" size="sm" onClick={() => setShowPreferences(true)}>
              <Settings className="w-4 h-4 mr-2" />
              Preferencias
            </Button>
          )}
        </div>
      </div>

      {/* Tabs - solo mostrar si es admin */}
      {isAdmin && (
        <div className="flex border-b border-secondary-200">
          <button
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'alerts'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-secondary-500 hover:text-secondary-700'
            }`}
            onClick={() => setActiveTab('alerts')}
          >
            <Bell className="w-4 h-4 inline-block mr-2" />
            Alertas del Sistema
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'activity'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-secondary-500 hover:text-secondary-700'
            }`}
            onClick={() => setActiveTab('activity')}
          >
            <Activity className="w-4 h-4 inline-block mr-2" />
            Actividad de Usuarios
          </button>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'alerts' ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <SummaryCard
              title="Total No Leídas"
              value={unreadCount?.total || 0}
              icon={Bell}
              iconBg="bg-primary-100"
              iconColor="text-primary-600"
            />
            <SummaryCard
              title="Críticas"
              value={unreadCount?.by_severity?.critical || 0}
              icon={XCircle}
              iconBg="bg-danger-100"
              iconColor="text-danger-600"
            />
            <SummaryCard
              title="Altas"
              value={unreadCount?.by_severity?.high || 0}
              icon={AlertTriangle}
              iconBg="bg-warning-100"
              iconColor="text-warning-600"
            />
            <SummaryCard
              title="Medias"
              value={unreadCount?.by_severity?.medium || 0}
              icon={AlertCircle}
              iconBg="bg-info-100"
              iconColor="text-info-600"
            />
            <SummaryCard
              title="Bajas"
              value={unreadCount?.by_severity?.low || 0}
              icon={Info}
              iconBg="bg-secondary-100"
              iconColor="text-secondary-600"
            />
          </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-secondary-400" />
            <span className="text-sm font-medium text-secondary-700">Filtros:</span>
          </div>

          <select
            className="px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={filters.severity || ''}
            onChange={(e) => handleFilterChange('severity', e.target.value as AlertSeverity)}
          >
            <option value="">Todas las severidades</option>
            <option value="critical">Crítica</option>
            <option value="high">Alta</option>
            <option value="medium">Media</option>
            <option value="low">Baja</option>
          </select>

          <select
            className="px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={filters.status || ''}
            onChange={(e) => handleFilterChange('status', e.target.value as AlertStatus)}
          >
            <option value="">Todos los estados</option>
            <option value="active">Activas</option>
            <option value="acknowledged">Reconocidas</option>
            <option value="resolved">Resueltas</option>
            <option value="dismissed">Descartadas</option>
          </select>

          <select
            className="px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={filters.alert_type || ''}
            onChange={(e) => handleFilterChange('alert_type', e.target.value as AlertType)}
          >
            <option value="">Todos los tipos</option>
            {isPlatformAdmin ? (
              <>
                <option value="subscription_payment_due">Pago próximo</option>
                <option value="subscription_overdue">Pago vencido</option>
                <option value="subscription_trial_ending">Prueba por terminar</option>
                <option value="subscription_cancelled">Suscripción cancelada</option>
                <option value="subscription_suspended">Suscripción suspendida</option>
                <option value="new_subscription">Nueva suscripción</option>
                <option value="subscription_plan_changed">Cambio de plan</option>
              </>
            ) : (
              <>
                <option value="low_stock">Stock bajo</option>
                <option value="out_of_stock">Sin stock</option>
                <option value="overstock">Exceso de stock</option>
                <option value="cash_difference">Diferencia de caja</option>
                <option value="high_void_rate">Alta tasa de anulaciones</option>
                <option value="shift_overtime">Turno extendido</option>
                <option value="system">Sistema</option>
              </>
            )}
          </select>

          <select
            className="px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={filters.is_read?.toString() || ''}
            onChange={(e) =>
              handleFilterChange(
                'is_read',
                e.target.value === '' ? undefined : e.target.value === 'true'
              )
            }
          >
            <option value="">Todas</option>
            <option value="false">No leídas</option>
            <option value="true">Leídas</option>
          </select>

          <div className="flex-1" />

          {selectedAlerts.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => bulkResolveMutation.mutate(selectedAlerts)}
              disabled={bulkResolveMutation.isPending}
            >
              <CheckCheck className="w-4 h-4 mr-2" />
              Resolver ({selectedAlerts.length})
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending || !unreadCount?.total}
          >
            <Eye className="w-4 h-4 mr-2" />
            Marcar todas como leídas
          </Button>
        </div>
      </div>

      {/* Alerts List */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-secondary-500">Cargando alertas...</div>
        ) : !alerts || alerts.length === 0 ? (
          <div className="p-8 text-center">
            <BellOff className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
            <p className="text-secondary-500">No hay alertas que mostrar</p>
          </div>
        ) : (
          <div className="divide-y divide-secondary-200">
            {/* Select All Header */}
            <div className="px-4 py-3 bg-secondary-50 flex items-center gap-4">
              <input
                type="checkbox"
                checked={selectedAlerts.length === alerts.length && alerts.length > 0}
                onChange={handleSelectAll}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <span className="text-sm text-secondary-500">
                {selectedAlerts.length > 0
                  ? `${selectedAlerts.length} seleccionadas`
                  : 'Seleccionar todas'}
              </span>
            </div>

            {/* Alert Items */}
            {alerts.map((alert) => (
              <AlertItem
                key={alert.id}
                alert={alert}
                selected={selectedAlerts.includes(alert.id)}
                onSelect={() => handleSelectAlert(alert.id)}
                onView={() => setSelectedAlert(alert)}
                onMarkRead={() => markReadMutation.mutate(alert.id)}
              />
            ))}
          </div>
        )}
      </div>
        </>
      ) : (
        <ActivityLogTab />
      )}

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <AlertDetailModal
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onAcknowledge={() => acknowledgeMutation.mutate(selectedAlert.id)}
          onResolve={(notes) =>
            resolveMutation.mutate({ id: selectedAlert.id, notes })
          }
          onDismiss={() => dismissMutation.mutate(selectedAlert.id)}
          isLoading={
            acknowledgeMutation.isPending ||
            resolveMutation.isPending ||
            dismissMutation.isPending
          }
        />
      )}

      {/* Preferences Modal */}
      {showPreferences && preferences && (
        <PreferencesModal
          preferences={preferences}
          onClose={() => setShowPreferences(false)}
          isPlatformAdmin={isPlatformAdmin}
        />
      )}
    </div>
  )
}

// Summary Card Component
interface SummaryCardProps {
  title: string
  value: number
  icon: React.ElementType
  iconBg: string
  iconColor: string
}

function SummaryCard({ title, value, icon: Icon, iconBg, iconColor }: SummaryCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${iconBg}`}>
          <Icon className={`w-5 h-5 ${iconColor}`} />
        </div>
        <div>
          <p className="text-sm text-secondary-500">{title}</p>
          <p className="text-xl font-bold text-secondary-900">{value}</p>
        </div>
      </div>
    </div>
  )
}

// Alert Item Component
interface AlertItemProps {
  alert: Alert
  selected: boolean
  onSelect: () => void
  onView: () => void
  onMarkRead: () => void
}

function AlertItem({ alert, selected, onSelect, onView, onMarkRead }: AlertItemProps) {
  const severityConfig: Record<
    AlertSeverity,
    { bg: string; border: string; icon: React.ElementType; iconColor: string }
  > = {
    critical: {
      bg: 'bg-danger-50',
      border: 'border-l-danger-500',
      icon: XCircle,
      iconColor: 'text-danger-500',
    },
    high: {
      bg: 'bg-warning-50',
      border: 'border-l-warning-500',
      icon: AlertTriangle,
      iconColor: 'text-warning-500',
    },
    medium: {
      bg: 'bg-info-50',
      border: 'border-l-info-500',
      icon: AlertCircle,
      iconColor: 'text-info-500',
    },
    low: {
      bg: 'bg-secondary-50',
      border: 'border-l-secondary-400',
      icon: Info,
      iconColor: 'text-secondary-500',
    },
  }

  const typeIcons: Record<AlertType, React.ElementType> = {
    // Company-level alerts
    low_stock: Package,
    out_of_stock: Package,
    overstock: Package,
    cash_difference: DollarSign,
    high_void_rate: AlertTriangle,
    sales_anomaly: AlertCircle,
    shift_overtime: Clock,
    system: Bell,
    // Platform-level alerts - Subscription related
    subscription_payment_due: CalendarClock,
    subscription_overdue: CreditCard,
    subscription_trial_ending: Clock,
    subscription_cancelled: Ban,
    subscription_suspended: PauseCircle,
    new_subscription: UserPlus,
    subscription_plan_changed: ArrowRightLeft,
    // Platform-level alerts - Business health
    high_churn_rate: TrendingDown,
    revenue_anomaly: DollarSign,
    low_platform_activity: Activity,
    // Platform-level alerts - Tenant health
    tenant_limit_approaching: ArrowUp,
    tenant_inactive: UserX,
    onboarding_stalled: Clock,
    // Platform-level alerts - System health
    high_error_rate: AlertOctagon,
    system_performance: Gauge,
  }

  const config = severityConfig[alert.severity]
  const SeverityIcon = config.icon
  const TypeIcon = typeIcons[alert.alert_type] || Bell

  return (
    <div
      className={`flex items-start gap-4 px-4 py-4 border-l-4 ${config.border} ${
        !alert.is_read ? config.bg : 'bg-white'
      } hover:bg-secondary-50 transition-colors cursor-pointer`}
      onClick={onView}
    >
      <input
        type="checkbox"
        checked={selected}
        onChange={(e) => {
          e.stopPropagation()
          onSelect()
        }}
        onClick={(e) => e.stopPropagation()}
        className="mt-1 w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
      />

      <div className={`p-2 rounded-lg ${config.bg}`}>
        <SeverityIcon className={`w-5 h-5 ${config.iconColor}`} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className={`text-sm font-medium ${!alert.is_read ? 'text-secondary-900' : 'text-secondary-700'}`}>
            {alert.title}
          </h4>
          {!alert.is_read && (
            <span className="w-2 h-2 bg-primary-500 rounded-full" />
          )}
        </div>
        <p className="text-sm text-secondary-600 line-clamp-2">{alert.message}</p>
        <div className="flex items-center gap-3 mt-2">
          <div className="flex items-center gap-1 text-xs text-secondary-500">
            <TypeIcon className="w-3 h-3" />
            {alert.alert_type_display}
          </div>
          {alert.branch_name && (
            <span className="text-xs text-secondary-500">{alert.branch_name}</span>
          )}
          <span className="text-xs text-secondary-400">
            {new Date(alert.created_at).toLocaleString()}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Badge
          variant={
            alert.status === 'resolved'
              ? 'success'
              : alert.status === 'acknowledged'
              ? 'primary'
              : alert.status === 'dismissed'
              ? 'secondary'
              : 'warning'
          }
        >
          {alert.status_display}
        </Badge>
        {!alert.is_read && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onMarkRead()
            }}
            className="p-1 hover:bg-secondary-100 rounded"
            title="Marcar como leída"
          >
            <Eye className="w-4 h-4 text-secondary-400" />
          </button>
        )}
      </div>
    </div>
  )
}

// Alert Detail Modal
interface AlertDetailModalProps {
  alert: Alert
  onClose: () => void
  onAcknowledge: () => void
  onResolve: (notes?: string) => void
  onDismiss: () => void
  isLoading: boolean
}

function AlertDetailModal({
  alert,
  onClose,
  onAcknowledge,
  onResolve,
  onDismiss,
  isLoading,
}: AlertDetailModalProps) {
  const [notes, setNotes] = useState('')

  const severityBadge: Record<AlertSeverity, 'danger' | 'warning' | 'primary' | 'secondary'> = {
    critical: 'danger',
    high: 'warning',
    medium: 'primary',
    low: 'secondary',
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
        <div className="px-6 py-4 border-b border-secondary-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Badge variant={severityBadge[alert.severity]}>{alert.severity_display}</Badge>
            <span className="text-sm text-secondary-500">{alert.alert_type_display}</span>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-secondary-100 rounded-lg">
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <h3 className="text-lg font-semibold text-secondary-900">{alert.title}</h3>
          <p className="text-secondary-600">{alert.message}</p>

          {/* Meta Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            {alert.branch_name && (
              <div>
                <span className="text-secondary-500">Sucursal:</span>
                <span className="ml-2 text-secondary-900">{alert.branch_name}</span>
              </div>
            )}
            {alert.product_name && (
              <div>
                <span className="text-secondary-500">Producto:</span>
                <span className="ml-2 text-secondary-900">{alert.product_name}</span>
              </div>
            )}
            {alert.employee_name && (
              <div>
                <span className="text-secondary-500">Empleado:</span>
                <span className="ml-2 text-secondary-900">{alert.employee_name}</span>
              </div>
            )}
            {/* Subscription info for platform alerts */}
            {alert.subscription_company_name && (
              <div>
                <span className="text-secondary-500">Empresa:</span>
                <span className="ml-2 text-secondary-900">{alert.subscription_company_name}</span>
              </div>
            )}
            {alert.subscription_plan && (
              <div>
                <span className="text-secondary-500">Plan:</span>
                <span className="ml-2 text-secondary-900 capitalize">{alert.subscription_plan}</span>
              </div>
            )}
            {alert.subscription_status && (
              <div>
                <span className="text-secondary-500">Estado suscripción:</span>
                <span className="ml-2 text-secondary-900 capitalize">{alert.subscription_status}</span>
              </div>
            )}
            <div>
              <span className="text-secondary-500">Fecha:</span>
              <span className="ml-2 text-secondary-900">
                {new Date(alert.created_at).toLocaleString()}
              </span>
            </div>
            <div>
              <span className="text-secondary-500">Estado:</span>
              <span className="ml-2">
                <Badge
                  variant={
                    alert.status === 'resolved'
                      ? 'success'
                      : alert.status === 'acknowledged'
                      ? 'primary'
                      : 'warning'
                  }
                >
                  {alert.status_display}
                </Badge>
              </span>
            </div>
          </div>

          {/* Resolution notes input */}
          {alert.status === 'active' && (
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Notas de resolución (opcional)
              </label>
              <textarea
                className="w-full px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Agregar notas sobre la resolución..."
              />
            </div>
          )}

          {/* Resolution info */}
          {alert.resolved_at && (
            <div className="bg-success-50 rounded-lg p-3 text-sm">
              <p className="font-medium text-success-700">Resuelta</p>
              <p className="text-success-600">
                Por {alert.resolved_by_name} el{' '}
                {new Date(alert.resolved_at).toLocaleString()}
              </p>
              {alert.resolution_notes && (
                <p className="text-success-600 mt-1">{alert.resolution_notes}</p>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        {alert.status === 'active' && (
          <div className="px-6 py-4 border-t border-secondary-200 flex justify-end gap-3">
            <Button variant="outline" onClick={onDismiss} disabled={isLoading}>
              Descartar
            </Button>
            <Button variant="outline" onClick={onAcknowledge} disabled={isLoading}>
              <Check className="w-4 h-4 mr-2" />
              Reconocer
            </Button>
            <Button onClick={() => onResolve(notes)} disabled={isLoading}>
              <CheckCheck className="w-4 h-4 mr-2" />
              Resolver
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

// Preferences Modal
interface PreferencesModalProps {
  preferences: {
    receive_low_stock: boolean
    receive_out_of_stock: boolean
    receive_cash_difference: boolean
    receive_void_alerts: boolean
    receive_shift_alerts: boolean
    receive_system_alerts: boolean
    receive_subscription_alerts?: boolean
    minimum_severity: AlertSeverity
    email_digest: boolean
  }
  onClose: () => void
  isPlatformAdmin: boolean
}

function PreferencesModal({ preferences, onClose, isPlatformAdmin }: PreferencesModalProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="px-6 py-4 border-b border-secondary-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-secondary-900">Preferencias de Alertas</h2>
          <button onClick={onClose} className="p-2 hover:bg-secondary-100 rounded-lg">
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-secondary-900">Tipos de Alertas</h3>
            {isPlatformAdmin ? (
              <>
                <PreferenceToggle
                  label="Alertas de suscripciones"
                  checked={preferences.receive_subscription_alerts ?? true}
                />
              </>
            ) : (
              <>
                <PreferenceToggle label="Stock bajo" checked={preferences.receive_low_stock} />
                <PreferenceToggle label="Sin stock" checked={preferences.receive_out_of_stock} />
                <PreferenceToggle label="Diferencia de caja" checked={preferences.receive_cash_difference} />
                <PreferenceToggle label="Anulaciones" checked={preferences.receive_void_alerts} />
                <PreferenceToggle label="Turnos" checked={preferences.receive_shift_alerts} />
                <PreferenceToggle label="Sistema" checked={preferences.receive_system_alerts} />
              </>
            )}
          </div>

          <div className="pt-4 border-t border-secondary-200">
            <h3 className="text-sm font-medium text-secondary-900 mb-3">Severidad Mínima</h3>
            <p className="text-sm text-secondary-500 capitalize">{preferences.minimum_severity}</p>
          </div>

          <div className="pt-4 border-t border-secondary-200">
            <PreferenceToggle
              label="Recibir resumen diario por email"
              checked={preferences.email_digest}
            />
          </div>

          <p className="text-xs text-secondary-500 mt-4">
            Para modificar estas preferencias, contacta al administrador del sistema.
          </p>
        </div>

        <div className="px-6 py-4 border-t border-secondary-200">
          <Button variant="outline" onClick={onClose} className="w-full">
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  )
}

function PreferenceToggle({ label, checked }: { label: string; checked: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-secondary-700">{label}</span>
      <span
        className={`px-2 py-1 text-xs rounded ${
          checked ? 'bg-success-100 text-success-700' : 'bg-secondary-100 text-secondary-500'
        }`}
      >
        {checked ? 'Activo' : 'Inactivo'}
      </span>
    </div>
  )
}

// Activity Log Tab Component
function ActivityLogTab() {
  const queryClient = useQueryClient()
  const [moduleFilter, setModuleFilter] = useState<ActivityModule | ''>('')

  const { data: activities, isLoading } = useQuery({
    queryKey: ['activity-logs', moduleFilter],
    queryFn: () => activityLogApi.getAll({ module: moduleFilter || undefined, limit: 100 }),
  })

  const { data: unreadCount } = useQuery({
    queryKey: ['activity-logs-unread'],
    queryFn: () => activityLogApi.getUnreadCount(),
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => activityLogApi.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity-logs'] })
      queryClient.invalidateQueries({ queryKey: ['activity-logs-unread'] })
    },
  })

  const markReadMutation = useMutation({
    mutationFn: (id: number) => activityLogApi.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity-logs'] })
      queryClient.invalidateQueries({ queryKey: ['activity-logs-unread'] })
    },
  })

  const moduleIcons: Record<ActivityModule, React.ElementType> = {
    inventory: Package,
    sales: ShoppingCart,
    employees: Users,
    branches: Store,
    users: Users,
    suppliers: Truck,
  }

  const moduleColors: Record<ActivityModule, { bg: string; text: string }> = {
    inventory: { bg: 'bg-blue-100', text: 'text-blue-600' },
    sales: { bg: 'bg-green-100', text: 'text-green-600' },
    employees: { bg: 'bg-purple-100', text: 'text-purple-600' },
    branches: { bg: 'bg-orange-100', text: 'text-orange-600' },
    users: { bg: 'bg-indigo-100', text: 'text-indigo-600' },
    suppliers: { bg: 'bg-teal-100', text: 'text-teal-600' },
  }

  return (
    <>
      {/* Summary */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary-100">
              <Activity className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">Actividades sin leer</p>
              <p className="text-xl font-bold text-secondary-900">{unreadCount?.count || 0}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending || !unreadCount?.count}
          >
            <CheckCheck className="w-4 h-4 mr-2" />
            Marcar todas como leídas
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-secondary-400" />
            <span className="text-sm font-medium text-secondary-700">Filtrar por módulo:</span>
          </div>

          <select
            className="px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={moduleFilter}
            onChange={(e) => setModuleFilter(e.target.value as ActivityModule | '')}
          >
            <option value="">Todos los módulos</option>
            <option value="inventory">Inventario</option>
            <option value="sales">Ventas</option>
            <option value="employees">Empleados</option>
            <option value="branches">Sucursales</option>
            <option value="users">Usuarios</option>
            <option value="suppliers">Proveedores</option>
          </select>
        </div>
      </div>

      {/* Activity List */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-secondary-500">Cargando actividad...</div>
        ) : !activities || activities.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
            <p className="text-secondary-500">No hay actividad registrada</p>
          </div>
        ) : (
          <div className="divide-y divide-secondary-200">
            {activities.map((activity) => {
              const ModuleIcon = moduleIcons[activity.module] || FileText
              const colors = moduleColors[activity.module] || { bg: 'bg-secondary-100', text: 'text-secondary-600' }

              return (
                <div
                  key={activity.id}
                  className={`flex items-start gap-4 px-4 py-4 ${
                    !activity.is_read ? 'bg-primary-50/30' : 'bg-white'
                  } hover:bg-secondary-50 transition-colors`}
                >
                  <div className={`p-2 rounded-lg ${colors.bg}`}>
                    <ModuleIcon className={`w-5 h-5 ${colors.text}`} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-secondary-900">
                        {activity.user_name}
                      </span>
                      {!activity.is_read && (
                        <span className="w-2 h-2 bg-primary-500 rounded-full" />
                      )}
                    </div>
                    <p className="text-sm text-secondary-600">{activity.description}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <Badge variant="secondary">{activity.module_display}</Badge>
                      {activity.branch_name && (
                        <span className="text-xs text-secondary-500">
                          <Store className="w-3 h-3 inline mr-1" />
                          {activity.branch_name}
                        </span>
                      )}
                      <span className="text-xs text-secondary-400">
                        {new Date(activity.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {!activity.is_read && (
                    <button
                      onClick={() => markReadMutation.mutate(activity.id)}
                      className="p-1 hover:bg-secondary-100 rounded"
                      title="Marcar como leída"
                    >
                      <Eye className="w-4 h-4 text-secondary-400" />
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </>
  )
}
