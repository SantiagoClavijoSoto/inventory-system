import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { useAuthStore, useIsPlatformAdmin } from '@/store/authStore'
import { alertsApi, type Alert, PLATFORM_ALERT_TYPES } from '@/api/alerts'
import { subscriptionsApi, type PlatformUsageStats } from '@/api/subscriptions'
import {
  DollarSign,
  Package,
  ShoppingCart,
  TrendingUp,
  AlertTriangle,
  XCircle,
  ChevronRight,
  Loader2,
  CheckCircle2,
  Building2,
  CreditCard,
  Clock,
  CalendarClock,
  Bell,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  TrendingDown,
  Gauge,
  UserX,
  AlertOctagon,
  ArrowUp,
} from 'lucide-react'

// Placeholder data for company admins - will be fetched from API
const companyStats = [
  {
    name: 'Ventas del Día',
    value: '$12,450',
    change: '+12%',
    changeType: 'positive' as const,
    icon: DollarSign,
  },
  {
    name: 'Productos Vendidos',
    value: '156',
    change: '+8%',
    changeType: 'positive' as const,
    icon: ShoppingCart,
  },
  {
    name: 'Productos en Stock',
    value: '2,340',
    change: '-2%',
    changeType: 'negative' as const,
    icon: Package,
  },
  {
    name: 'Ganancias del Mes',
    value: '$45,230',
    change: '+18%',
    changeType: 'positive' as const,
    icon: TrendingUp,
  },
]

// Alert type configuration for company alerts
const companyAlertConfig = {
  out_of_stock: {
    icon: XCircle,
    color: 'text-danger-600',
    bg: 'bg-danger-100',
    label: 'Sin stock',
  },
  low_stock: {
    icon: AlertTriangle,
    color: 'text-warning-600',
    bg: 'bg-warning-100',
    label: 'Stock bajo',
  },
}

// Alert type configuration for platform alerts (SuperAdmin)
const platformAlertConfig = {
  // Subscription related
  subscription_payment_due: {
    icon: CalendarClock,
    color: 'text-warning-600',
    bg: 'bg-warning-100',
    label: 'Pago próximo',
  },
  subscription_overdue: {
    icon: XCircle,
    color: 'text-danger-600',
    bg: 'bg-danger-100',
    label: 'Pago vencido',
  },
  subscription_trial_ending: {
    icon: Clock,
    color: 'text-primary-600',
    bg: 'bg-primary-100',
    label: 'Prueba por terminar',
  },
  subscription_cancelled: {
    icon: XCircle,
    color: 'text-danger-600',
    bg: 'bg-danger-100',
    label: 'Cancelada',
  },
  subscription_suspended: {
    icon: AlertTriangle,
    color: 'text-danger-600',
    bg: 'bg-danger-100',
    label: 'Suspendida',
  },
  new_subscription: {
    icon: CheckCircle2,
    color: 'text-success-600',
    bg: 'bg-success-100',
    label: 'Nueva suscripción',
  },
  subscription_plan_changed: {
    icon: CreditCard,
    color: 'text-primary-600',
    bg: 'bg-primary-100',
    label: 'Cambio de plan',
  },
  // Business health
  high_churn_rate: {
    icon: TrendingDown,
    color: 'text-danger-600',
    bg: 'bg-danger-100',
    label: 'Alta tasa de churn',
  },
  revenue_anomaly: {
    icon: DollarSign,
    color: 'text-warning-600',
    bg: 'bg-warning-100',
    label: 'Anomalía en ingresos',
  },
  low_platform_activity: {
    icon: Activity,
    color: 'text-warning-600',
    bg: 'bg-warning-100',
    label: 'Baja actividad',
  },
  // Tenant health
  tenant_limit_approaching: {
    icon: ArrowUp,
    color: 'text-warning-600',
    bg: 'bg-warning-100',
    label: 'Cerca del límite',
  },
  tenant_inactive: {
    icon: UserX,
    color: 'text-secondary-600',
    bg: 'bg-secondary-100',
    label: 'Tenant inactivo',
  },
  onboarding_stalled: {
    icon: Clock,
    color: 'text-warning-600',
    bg: 'bg-warning-100',
    label: 'Onboarding detenido',
  },
  // System health
  high_error_rate: {
    icon: AlertOctagon,
    color: 'text-danger-600',
    bg: 'bg-danger-100',
    label: 'Errores del sistema',
  },
  system_performance: {
    icon: Gauge,
    color: 'text-warning-600',
    bg: 'bg-warning-100',
    label: 'Rendimiento',
  },
}

export function Dashboard() {
  const navigate = useNavigate()
  const { user, currentBranch } = useAuthStore()
  const isPlatformAdmin = useIsPlatformAdmin()

  // Fetch subscription stats (SuperAdmin only)
  const { data: subscriptionStats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['subscriptions', 'stats'],
    queryFn: subscriptionsApi.getStats,
    enabled: isPlatformAdmin,
    refetchInterval: 60000,
  })

  // Fetch platform usage stats (SuperAdmin only)
  const { data: platformUsage, isLoading: isLoadingUsage } = useQuery<PlatformUsageStats>({
    queryKey: ['subscriptions', 'platform_usage'],
    queryFn: subscriptionsApi.getPlatformUsage,
    enabled: isPlatformAdmin,
    refetchInterval: 30000, // Refresh every 30 seconds for real-time feel
  })

  // Fetch subscription alerts (SuperAdmin only)
  const { data: subscriptionAlerts, isLoading: isLoadingSubscriptionAlerts } = useQuery<Alert[]>({
    queryKey: ['alerts', 'subscriptions'],
    queryFn: async () => {
      const alerts = await alertsApi.getAll({
        status: 'active',
        limit: 20,
      })
      // Filter only subscription alerts and sort by severity
      return alerts
        .filter(a => PLATFORM_ALERT_TYPES.includes(a.alert_type))
        .sort((a, b) => {
          const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
          const severityDiff = severityOrder[a.severity] - severityOrder[b.severity]
          if (severityDiff !== 0) return severityDiff
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        })
    },
    enabled: isPlatformAdmin,
    refetchInterval: 60000,
  })

  // Fetch stock alerts for company admins
  const { data: stockAlerts, isLoading: isLoadingAlerts } = useQuery<Alert[]>({
    queryKey: ['alerts', 'stock', currentBranch?.id],
    queryFn: async () => {
      const [lowStock, outOfStock] = await Promise.all([
        alertsApi.getAll({
          branch_id: currentBranch?.id,
          alert_type: 'low_stock',
          status: 'active',
          limit: 10,
        }),
        alertsApi.getAll({
          branch_id: currentBranch?.id,
          alert_type: 'out_of_stock',
          status: 'active',
          limit: 10,
        }),
      ])
      const combined = [...outOfStock, ...lowStock]
      return combined.sort((a, b) => {
        const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
        const severityDiff = severityOrder[a.severity] - severityOrder[b.severity]
        if (severityDiff !== 0) return severityDiff
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      })
    },
    enabled: !isPlatformAdmin && !!currentBranch,
    refetchInterval: 60000,
  })

  const handleViewAllAlerts = () => {
    navigate('/alerts')
  }

  const handleAlertClick = (alert: Alert) => {
    navigate(`/alerts?type=${alert.alert_type}`)
  }

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  // SuperAdmin Dashboard
  if (isPlatformAdmin) {
    const platformStats = [
      {
        name: 'Empresas Activas',
        value: subscriptionStats?.active_subscriptions?.toString() || '0',
        icon: Building2,
        color: 'text-success-600',
        bg: 'bg-success-100',
      },
      {
        name: 'En Período de Prueba',
        value: subscriptionStats?.trial_subscriptions?.toString() || '0',
        icon: Clock,
        color: 'text-primary-600',
        bg: 'bg-primary-100',
      },
      {
        name: 'Pagos Vencidos',
        value: subscriptionStats?.past_due_subscriptions?.toString() || '0',
        icon: AlertTriangle,
        color: subscriptionStats?.past_due_subscriptions ? 'text-danger-600' : 'text-secondary-400',
        bg: subscriptionStats?.past_due_subscriptions ? 'bg-danger-100' : 'bg-secondary-100',
      },
      {
        name: 'MRR (Ingresos Mensuales)',
        value: formatCurrency(subscriptionStats?.mrr || 0),
        icon: DollarSign,
        color: 'text-success-600',
        bg: 'bg-success-100',
      },
    ]

    return (
      <div className="space-y-6">
        {/* Welcome Header */}
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">
            Panel de Administrador
          </h1>
          <p className="text-secondary-500">
            Gestión de la plataforma •{' '}
            {new Date().toLocaleDateString('es-ES', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>

        {/* Platform Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {platformStats.map((stat) => (
            <Card key={stat.name}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-secondary-500">
                      {stat.name}
                    </p>
                    <p className="text-2xl font-bold text-secondary-900 mt-1">
                      {isLoadingStats ? (
                        <Loader2 className="w-6 h-6 animate-spin" />
                      ) : (
                        stat.value
                      )}
                    </p>
                  </div>
                  <div className={`p-3 rounded-lg ${stat.bg}`}>
                    <stat.icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Revenue Metrics - SaaS Income */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* MRR */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-secondary-500 uppercase tracking-wide">
                    MRR (Ingresos Recurrentes)
                  </p>
                  <p className="text-xl font-bold text-secondary-900 mt-1">
                    {isLoadingUsage ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      formatCurrency(platformUsage?.mrr?.total || 0)
                    )}
                  </p>
                  <p className="text-xs text-secondary-400 mt-1">
                    Suscripciones mensuales activas
                  </p>
                </div>
                <div className="p-2 rounded-lg bg-success-100">
                  <DollarSign className="w-5 h-5 text-success-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Upcoming Payments */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-secondary-500 uppercase tracking-wide">
                    Por Cobrar (7 días)
                  </p>
                  <p className="text-xl font-bold text-secondary-900 mt-1">
                    {isLoadingUsage ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      formatCurrency(platformUsage?.upcoming_payments?.amount || 0)
                    )}
                  </p>
                  <p className="text-xs text-secondary-400 mt-1">
                    {platformUsage?.upcoming_payments?.count || 0} suscripciones
                  </p>
                </div>
                <div className="p-2 rounded-lg bg-primary-100">
                  <CalendarClock className="w-5 h-5 text-primary-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* New Subscriptions */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-secondary-500 uppercase tracking-wide">
                    Nuevas Este Mes
                  </p>
                  <p className="text-xl font-bold text-secondary-900 mt-1">
                    {isLoadingUsage ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      platformUsage?.new_subscriptions?.count || 0
                    )}
                  </p>
                  {!isLoadingUsage && platformUsage?.new_subscriptions && (
                    <div className={`flex items-center gap-1 text-xs mt-1 ${
                      platformUsage.new_subscriptions.change_percent >= 0 ? 'text-success-600' : 'text-danger-600'
                    }`}>
                      {platformUsage.new_subscriptions.change_percent >= 0 ? (
                        <ArrowUpRight className="w-3 h-3" />
                      ) : (
                        <ArrowDownRight className="w-3 h-3" />
                      )}
                      {Math.abs(platformUsage.new_subscriptions.change_percent)}% vs mes anterior
                    </div>
                  )}
                </div>
                <div className="p-2 rounded-lg bg-success-100">
                  <CheckCircle2 className="w-5 h-5 text-success-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Overdue Payments */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-secondary-500 uppercase tracking-wide">
                    Pagos Vencidos
                  </p>
                  <p className={`text-xl font-bold mt-1 ${
                    (platformUsage?.overdue_payments?.count || 0) > 0 ? 'text-danger-600' : 'text-secondary-900'
                  }`}>
                    {isLoadingUsage ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      formatCurrency(platformUsage?.overdue_payments?.amount || 0)
                    )}
                  </p>
                  <p className={`text-xs mt-1 ${
                    (platformUsage?.overdue_payments?.count || 0) > 0 ? 'text-danger-500' : 'text-secondary-400'
                  }`}>
                    {platformUsage?.overdue_payments?.count || 0} suscripciones
                  </p>
                </div>
                <div className={`p-2 rounded-lg ${
                  (platformUsage?.overdue_payments?.count || 0) > 0 ? 'bg-danger-100' : 'bg-secondary-100'
                }`}>
                  <AlertTriangle className={`w-5 h-5 ${
                    (platformUsage?.overdue_payments?.count || 0) > 0 ? 'text-danger-600' : 'text-secondary-400'
                  }`} />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Alerts and Top Companies Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Subscription Alerts */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Bell className="w-5 h-5 text-primary-500" />
                  Alertas de Plataforma
                </CardTitle>
                {subscriptionAlerts && subscriptionAlerts.length > 0 && (
                  <button
                    onClick={handleViewAllAlerts}
                    className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                  >
                    Ver todas
                    <ChevronRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingSubscriptionAlerts ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
                </div>
              ) : !subscriptionAlerts || subscriptionAlerts.length === 0 ? (
                <div className="text-center py-6 text-secondary-500">
                  <CheckCircle2 className="w-10 h-10 mx-auto mb-2 text-success-500" />
                  <p className="font-medium text-secondary-700">¡Todo en orden!</p>
                  <p className="text-sm mt-1">No hay alertas pendientes</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {subscriptionAlerts.slice(0, 4).map((alert) => {
                    const config = platformAlertConfig[alert.alert_type as keyof typeof platformAlertConfig] || {
                      icon: Bell,
                      color: 'text-secondary-600',
                      bg: 'bg-secondary-100',
                      label: 'Alerta',
                    }
                    const Icon = config.icon
                    return (
                      <button
                        key={alert.id}
                        onClick={() => handleAlertClick(alert)}
                        className="w-full flex items-center gap-3 p-2 rounded-lg bg-secondary-50 hover:bg-secondary-100 transition-colors text-left"
                      >
                        <div className={`p-1.5 rounded-lg ${config.bg}`}>
                          <Icon className={`w-4 h-4 ${config.color}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-secondary-900 truncate">
                            {alert.subscription_company_name || alert.title}
                          </p>
                          <p className="text-xs text-secondary-500 truncate">
                            {config.label} • {alert.subscription_plan}
                          </p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-secondary-400" />
                      </button>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Subscribers - Highest paying customers */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <CreditCard className="w-5 h-5 text-success-500" />
                Top Suscriptores
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingUsage ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
                </div>
              ) : !platformUsage?.top_subscribers || platformUsage.top_subscribers.length === 0 ? (
                <div className="text-center py-6 text-secondary-500">
                  <Building2 className="w-10 h-10 mx-auto mb-2 text-secondary-300" />
                  <p className="text-sm">No hay suscripciones activas</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {platformUsage.top_subscribers.map((subscriber, index) => {
                    const planLabels: Record<string, string> = {
                      free: 'Gratuito',
                      basic: 'Básico',
                      professional: 'Profesional',
                      enterprise: 'Empresarial',
                    }
                    const cycleLabels: Record<string, string> = {
                      monthly: 'Mensual',
                      quarterly: 'Trimestral',
                      annual: 'Anual',
                    }
                    return (
                      <div key={subscriber.id} className="flex items-center gap-3">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          index === 0 ? 'bg-warning-100 text-warning-700' :
                          index === 1 ? 'bg-secondary-200 text-secondary-700' :
                          index === 2 ? 'bg-orange-100 text-orange-700' :
                          'bg-secondary-100 text-secondary-600'
                        }`}>
                          {index + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-secondary-900 truncate">
                            {subscriber.name}
                          </p>
                          <p className="text-xs text-secondary-500">
                            {planLabels[subscriber.plan] || subscriber.plan} • {cycleLabels[subscriber.billing_cycle] || subscriber.billing_cycle}
                          </p>
                        </div>
                        <span className="text-sm font-semibold text-success-600">
                          {formatCurrency(subscriber.amount)}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Resumen de Suscripciones</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingStats ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-2 border-b border-secondary-100">
                    <span className="text-secondary-600">Total Suscripciones</span>
                    <span className="font-semibold">{subscriptionStats?.total_subscriptions || 0}</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-secondary-100">
                    <span className="text-secondary-600">Nuevas este mes</span>
                    <span className="font-semibold text-success-600">+{subscriptionStats?.new_this_month || 0}</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-secondary-100">
                    <span className="text-secondary-600">Canceladas</span>
                    <span className="font-semibold text-danger-600">{subscriptionStats?.cancelled_subscriptions || 0}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-secondary-600">Próximos pagos (7 días)</span>
                    <span className="font-semibold text-warning-600">{subscriptionStats?.upcoming_payments || 0}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Distribución por Plan</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingStats ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
                </div>
              ) : (
                <div className="space-y-4">
                  {subscriptionStats?.by_plan?.map((item) => {
                    const planColors: Record<string, string> = {
                      free: 'bg-secondary-500',
                      basic: 'bg-primary-500',
                      professional: 'bg-success-500',
                      enterprise: 'bg-warning-500',
                    }
                    const planNames: Record<string, string> = {
                      free: 'Gratuito',
                      basic: 'Básico',
                      professional: 'Profesional',
                      enterprise: 'Empresarial',
                    }
                    const total = subscriptionStats?.total_subscriptions || 1
                    const percentage = Math.round((item.count / total) * 100)
                    return (
                      <div key={item.plan} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-secondary-600">{planNames[item.plan] || item.plan}</span>
                          <span className="font-semibold">{item.count} ({percentage}%)</span>
                        </div>
                        <div className="w-full bg-secondary-100 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${planColors[item.plan] || 'bg-primary-500'}`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    )
                  }) || (
                    <div className="text-center py-4 text-secondary-400">
                      No hay datos disponibles
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Company Admin Dashboard (original)
  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">
          ¡Bienvenido, {user?.first_name}!
        </h1>
        <p className="text-secondary-500">
          {currentBranch ? `${currentBranch.name}` : 'Selecciona una sucursal'} •{' '}
          {new Date().toLocaleDateString('es-ES', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {companyStats.map((stat) => (
          <Card key={stat.name}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-500">
                    {stat.name}
                  </p>
                  <p className="text-2xl font-bold text-secondary-900 mt-1">
                    {stat.value}
                  </p>
                  <p
                    className={`text-sm mt-1 ${
                      stat.changeType === 'positive'
                        ? 'text-success-600'
                        : 'text-danger-600'
                    }`}
                  >
                    {stat.change} vs ayer
                  </p>
                </div>
                <div
                  className={`p-3 rounded-lg ${
                    stat.changeType === 'positive'
                      ? 'bg-success-100'
                      : 'bg-danger-100'
                  }`}
                >
                  <stat.icon
                    className={`w-6 h-6 ${
                      stat.changeType === 'positive'
                        ? 'text-success-600'
                        : 'text-danger-600'
                    }`}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Alerts Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-warning-500" />
              Alertas de Stock
            </CardTitle>
            {stockAlerts && stockAlerts.length > 0 && (
              <button
                onClick={handleViewAllAlerts}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
              >
                Ver todas
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingAlerts ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
            </div>
          ) : !stockAlerts || stockAlerts.length === 0 ? (
            <div className="text-center py-8 text-secondary-500">
              <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-success-500" />
              <p className="font-medium text-secondary-700">¡Todo en orden!</p>
              <p className="text-sm mt-1">
                No hay alertas de stock en este momento
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {stockAlerts.slice(0, 5).map((alert) => {
                const config = companyAlertConfig[alert.alert_type as keyof typeof companyAlertConfig] || companyAlertConfig.low_stock
                const Icon = config.icon
                return (
                  <button
                    key={alert.id}
                    onClick={() => handleAlertClick(alert)}
                    className="w-full flex items-center gap-4 p-3 rounded-lg bg-secondary-50 hover:bg-secondary-100 transition-colors text-left"
                  >
                    <div className={`p-2 rounded-lg ${config.bg}`}>
                      <Icon className={`w-5 h-5 ${config.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-secondary-900 truncate">
                          {alert.product_name || alert.title}
                        </p>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${config.bg} ${config.color}`}>
                          {config.label}
                        </span>
                      </div>
                      <p className="text-sm text-secondary-500 truncate">
                        {alert.message}
                      </p>
                      {alert.product_sku && (
                        <p className="text-xs text-secondary-400 mt-0.5">
                          SKU: {alert.product_sku}
                          {alert.branch_name && ` • ${alert.branch_name}`}
                        </p>
                      )}
                    </div>
                    <ChevronRight className="w-5 h-5 text-secondary-400 flex-shrink-0" />
                  </button>
                )
              })}
              {stockAlerts.length > 5 && (
                <button
                  onClick={handleViewAllAlerts}
                  className="w-full text-center py-2 text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  Ver {stockAlerts.length - 5} alertas más
                </button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Charts Section - Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Ventas de los Últimos 7 Días</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-secondary-400">
              <div className="text-center">
                <TrendingUp className="w-12 h-12 mx-auto mb-3" />
                <p>Gráfica de ventas</p>
                <p className="text-sm">Se mostrará con datos reales</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top 5 Productos Más Vendidos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-secondary-400">
              <div className="text-center">
                <Package className="w-12 h-12 mx-auto mb-3" />
                <p>Lista de productos top</p>
                <p className="text-sm">Se mostrará con datos reales</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
