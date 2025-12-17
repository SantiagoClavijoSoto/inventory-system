import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { useAuthStore, useIsPlatformAdmin } from '@/store/authStore'
import { alertsApi, type Alert, PLATFORM_ALERT_TYPES } from '@/api/alerts'
import { subscriptionsApi, type PlatformUsageStats } from '@/api/subscriptions'
import {
  dashboardApi,
  salesReportsApi,
  inventoryReportsApi,
  type TodaySummary,
  type TopProduct,
  type SalesByPeriod,
  type StockSummary,
} from '@/api/reports'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
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
  Trophy,
} from 'lucide-react'

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

  // Permission helpers
  const userPermissions = user?.permissions || []
  const hasPermission = (perm: string) => userPermissions.includes(perm)

  // Check specific permissions for dashboard sections
  const hasInventoryView = hasPermission('inventory:view')
  const hasSalesView = hasPermission('sales:view')
  const hasReportsView = hasPermission('reports:view')
  const hasAlertsView = hasPermission('alerts:view')

  // Derived permissions for different dashboard sections
  const canViewStockAlerts = hasInventoryView || hasAlertsView
  const canViewSalesData = hasSalesView || hasReportsView
  const canViewInventoryData = hasInventoryView || hasReportsView

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

  // Fetch stock alerts for users with inventory or alerts view permission
  const { data: stockAlerts, isLoading: isLoadingAlerts } = useQuery<Alert[]>({
    queryKey: ['alerts', 'stock', currentBranch?.id],
    queryFn: async () => {
      const [lowStock, outOfStock] = await Promise.all([
        alertsApi.getAll({
          branch_id: currentBranch?.id,
          alert_type: 'low_stock',
          status: 'active',
        }),
        alertsApi.getAll({
          branch_id: currentBranch?.id,
          alert_type: 'out_of_stock',
          status: 'active',
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
    enabled: !isPlatformAdmin && !!currentBranch && canViewStockAlerts,
    refetchInterval: 60000,
  })

  // Fetch today's sales summary (requires sales or reports view permission)
  const { data: todaySummary, isLoading: isLoadingTodaySummary } = useQuery<TodaySummary>({
    queryKey: ['dashboard', 'today', currentBranch?.id],
    queryFn: () => dashboardApi.getTodaySummary(currentBranch?.id),
    enabled: !isPlatformAdmin && !!currentBranch && canViewSalesData,
    refetchInterval: 60000,
  })

  // Fetch inventory summary (requires inventory or reports view permission)
  const { data: inventorySummary, isLoading: isLoadingInventory } = useQuery<StockSummary>({
    queryKey: ['inventory', 'summary', currentBranch?.id],
    queryFn: () => inventoryReportsApi.getSummary(currentBranch?.id),
    enabled: !isPlatformAdmin && !!currentBranch && canViewInventoryData,
    refetchInterval: 60000,
  })

  // Fetch sales by period - last 7 days (requires sales or reports view permission)
  const { data: salesByPeriod, isLoading: isLoadingSalesPeriod } = useQuery<SalesByPeriod[]>({
    queryKey: ['sales', 'by-period', currentBranch?.id],
    queryFn: () => {
      const today = new Date()
      const sevenDaysAgo = new Date(today)
      sevenDaysAgo.setDate(today.getDate() - 6)
      return salesReportsApi.getByPeriod({
        date_from: sevenDaysAgo.toISOString().split('T')[0],
        date_to: today.toISOString().split('T')[0],
        group_by: 'day',
        branch_id: currentBranch?.id,
      })
    },
    enabled: !isPlatformAdmin && !!currentBranch && canViewSalesData,
    refetchInterval: 60000,
  })

  // Fetch top 5 products (requires sales or reports view permission)
  const { data: topProducts, isLoading: isLoadingTopProducts } = useQuery<TopProduct[]>({
    queryKey: ['dashboard', 'top-products', currentBranch?.id],
    queryFn: () => dashboardApi.getTopProducts({ days: 7, limit: 5, branch_id: currentBranch?.id }),
    enabled: !isPlatformAdmin && !!currentBranch && canViewSalesData,
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
    const formatted = new Intl.NumberFormat('es-CO', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
    return `COP ${formatted}`
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

      {/* Stats Grid - shows cards based on user permissions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Ventas del Día - requires sales/reports permission */}
        {canViewSalesData && (
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-500">
                    Ventas del Día
                  </p>
                  <p className="text-2xl font-bold text-secondary-900 mt-1">
                    {isLoadingTodaySummary ? (
                      <Loader2 className="w-6 h-6 animate-spin" />
                    ) : (
                      formatCurrency(todaySummary?.total_sales || 0)
                    )}
                  </p>
                  <p className="text-sm mt-1 text-secondary-500">
                    {todaySummary?.total_transactions || 0} transacciones
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-success-100">
                  <DollarSign className="w-6 h-6 text-success-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Productos Vendidos - requires sales/reports permission */}
        {canViewSalesData && (
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-500">
                    Productos Vendidos
                  </p>
                  <p className="text-2xl font-bold text-secondary-900 mt-1">
                    {isLoadingTodaySummary ? (
                      <Loader2 className="w-6 h-6 animate-spin" />
                    ) : (
                      todaySummary?.items_sold || 0
                    )}
                  </p>
                  <p className="text-sm mt-1 text-secondary-500">
                    Ticket promedio: {formatCurrency(todaySummary?.average_ticket || 0)}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-primary-100">
                  <ShoppingCart className="w-6 h-6 text-primary-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Productos en Stock - requires inventory/reports permission */}
        {canViewInventoryData && (
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-500">
                    Productos en Stock
                  </p>
                  <p className="text-2xl font-bold text-secondary-900 mt-1">
                    {isLoadingInventory ? (
                      <Loader2 className="w-6 h-6 animate-spin" />
                    ) : (
                      (inventorySummary?.total_products || 0).toLocaleString()
                    )}
                  </p>
                  <p className={`text-sm mt-1 ${
                    (inventorySummary?.low_stock_count || 0) > 0 ? 'text-warning-600' : 'text-secondary-500'
                  }`}>
                    {inventorySummary?.low_stock_count || 0} con stock bajo
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${
                  (inventorySummary?.out_of_stock_count || 0) > 0 ? 'bg-danger-100' : 'bg-secondary-100'
                }`}>
                  <Package className={`w-6 h-6 ${
                    (inventorySummary?.out_of_stock_count || 0) > 0 ? 'text-danger-600' : 'text-secondary-600'
                  }`} />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Ganancia del Día - requires sales/reports permission */}
        {canViewSalesData && (
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-500">
                    Ganancia del Día
                  </p>
                  <p className="text-2xl font-bold text-secondary-900 mt-1">
                    {isLoadingTodaySummary ? (
                      <Loader2 className="w-6 h-6 animate-spin" />
                    ) : (
                      formatCurrency(todaySummary?.total_profit || 0)
                    )}
                  </p>
                  <p className="text-sm mt-1 text-secondary-500">
                    Efectivo: {formatCurrency(todaySummary?.cash_total || 0)}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-success-100">
                  <TrendingUp className="w-6 h-6 text-success-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Alerts Section - requires inventory or alerts permission */}
      {canViewStockAlerts && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-warning-500" />
                Alertas de Stock
                {stockAlerts && stockAlerts.length > 0 && (
                  <span className="ml-2 text-sm font-normal text-secondary-500">
                    ({stockAlerts.length} {stockAlerts.length === 1 ? 'producto' : 'productos'})
                  </span>
                )}
              </CardTitle>
              {stockAlerts && stockAlerts.length > 0 && (
                <button
                  onClick={handleViewAllAlerts}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                >
                  Ver detalles
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
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {stockAlerts.map((alert) => {
                  const config = companyAlertConfig[alert.alert_type as keyof typeof companyAlertConfig] || companyAlertConfig.low_stock
                  const Icon = config.icon
                  return (
                    <button
                      key={alert.id}
                      onClick={() => handleAlertClick(alert)}
                      className="w-full flex items-center gap-3 p-2.5 rounded-lg bg-secondary-50 hover:bg-secondary-100 transition-colors text-left"
                    >
                      <div className={`p-1.5 rounded-lg ${config.bg} flex-shrink-0`}>
                        <Icon className={`w-4 h-4 ${config.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-secondary-900 truncate">
                            {alert.product_name || alert.title}
                          </p>
                          <span className={`text-xs px-1.5 py-0.5 rounded-full ${config.bg} ${config.color} flex-shrink-0`}>
                            {config.label}
                          </span>
                        </div>
                        {alert.product_sku && (
                          <p className="text-xs text-secondary-400">
                            SKU: {alert.product_sku}
                            {alert.branch_name && ` • ${alert.branch_name}`}
                          </p>
                        )}
                      </div>
                      <ChevronRight className="w-4 h-4 text-secondary-400 flex-shrink-0" />
                    </button>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Charts Section - requires sales/reports permission */}
      {canViewSalesData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sales Chart - Last 7 Days */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary-500" />
                Ventas de los Últimos 7 Días
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingSalesPeriod ? (
                <div className="h-64 flex items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
                </div>
              ) : !salesByPeriod || salesByPeriod.length === 0 ? (
                <div className="h-64 flex items-center justify-center text-secondary-400">
                  <div className="text-center">
                    <TrendingUp className="w-12 h-12 mx-auto mb-3" />
                    <p className="font-medium text-secondary-700">Sin datos</p>
                    <p className="text-sm">No hay ventas registradas en este período</p>
                  </div>
                </div>
              ) : (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={salesByPeriod.map(item => ({
                        ...item,
                        // Format date to show day name
                        day: new Date(item.period).toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric' }),
                      }))}
                      margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="day"
                        tick={{ fill: '#6b7280', fontSize: 12 }}
                        axisLine={{ stroke: '#e5e7eb' }}
                      />
                      <YAxis
                        tick={{ fill: '#6b7280', fontSize: 12 }}
                        axisLine={{ stroke: '#e5e7eb' }}
                        tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                      />
                      <Tooltip
                        formatter={(value: number) => [formatCurrency(value), 'Ventas']}
                        labelFormatter={(label) => `Día: ${label}`}
                        contentStyle={{
                          backgroundColor: '#fff',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                        }}
                      />
                      <Bar
                        dataKey="total_sales"
                        fill="#3b82f6"
                        radius={[4, 4, 0, 0]}
                        name="Ventas"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top 5 Products */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="w-5 h-5 text-warning-500" />
                Top 5 Productos Más Vendidos
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingTopProducts ? (
                <div className="h-64 flex items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
                </div>
              ) : !topProducts || topProducts.length === 0 ? (
                <div className="h-64 flex items-center justify-center text-secondary-400">
                  <div className="text-center">
                    <Package className="w-12 h-12 mx-auto mb-3" />
                    <p className="font-medium text-secondary-700">Sin datos</p>
                    <p className="text-sm">No hay productos vendidos en este período</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {topProducts.map((product, index) => (
                    <div key={product.product_id} className="flex items-center gap-4">
                      <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                        index === 0 ? 'bg-warning-100 text-warning-700' :
                        index === 1 ? 'bg-secondary-200 text-secondary-700' :
                        index === 2 ? 'bg-orange-100 text-orange-700' :
                        'bg-secondary-100 text-secondary-600'
                      }`}>
                        {index + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-secondary-900 truncate">
                          {product.product_name}
                        </p>
                        <p className="text-xs text-secondary-500">
                          SKU: {product.product_sku}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-secondary-900">
                          {product.total_quantity} uds
                        </p>
                        <p className="text-xs text-success-600">
                          {formatCurrency(product.total_revenue)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
