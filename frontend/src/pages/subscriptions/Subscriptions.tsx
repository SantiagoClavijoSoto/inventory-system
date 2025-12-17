import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { subscriptionsApi, type SubscriptionListParams } from '@/api/subscriptions'
import type { CompanyPlan, SubscriptionStatus } from '@/types'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import {
  Search,
  CreditCard,
  Building,
  Calendar,
  TrendingUp,
  AlertCircle,
  Clock,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

// Badge variants
type BadgeVariant = 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'secondary'

const planColors: Record<CompanyPlan, BadgeVariant> = {
  free: 'secondary',
  basic: 'primary',
  professional: 'success',
  enterprise: 'warning',
}

const planNames: Record<CompanyPlan, string> = {
  free: 'Gratuito',
  basic: 'Básico',
  professional: 'Profesional',
  enterprise: 'Empresarial',
}

const statusColors: Record<SubscriptionStatus, BadgeVariant> = {
  trial: 'primary',
  active: 'success',
  past_due: 'danger',
  cancelled: 'secondary',
  suspended: 'danger',
}

const statusNames: Record<SubscriptionStatus, string> = {
  trial: 'Prueba',
  active: 'Activa',
  past_due: 'Vencida',
  cancelled: 'Cancelada',
  suspended: 'Suspendida',
}

export function Subscriptions() {
  const [filters, setFilters] = useState<SubscriptionListParams>({
    page: 1,
    page_size: 20,
  })
  const [searchTerm, setSearchTerm] = useState('')

  // Query subscriptions
  const { data: subscriptionsData, isLoading } = useQuery({
    queryKey: ['subscriptions', filters],
    queryFn: () => subscriptionsApi.getAll(filters),
  })

  // Query stats
  const { data: stats } = useQuery({
    queryKey: ['subscriptions-stats'],
    queryFn: () => subscriptionsApi.getStats(),
  })

  const handleSearch = () => {
    setFilters((prev) => ({ ...prev, search: searchTerm, page: 1 }))
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const handleFilterChange = (key: keyof SubscriptionListParams, value: string | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }))
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatCurrency = (amount: number, currency: string = 'COP') => {
    const formatted = new Intl.NumberFormat('es-CO', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
    return `${currency} ${formatted}`
  }

  const getDaysUntilPayment = (dateString?: string) => {
    if (!dateString) return null
    const date = new Date(dateString)
    const today = new Date()
    const diffTime = date.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const subscriptions = subscriptionsData?.results ?? []
  const totalPages = subscriptionsData?.total_pages ?? 1

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Suscripciones</h1>
          <p className="text-secondary-500 mt-1">
            Gestiona las suscripciones y facturación de las empresas
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CreditCard className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">Suscripciones Activas</p>
              <p className="text-xl font-semibold text-secondary-900">
                {stats?.active_subscriptions ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">En Prueba</p>
              <p className="text-xl font-semibold text-secondary-900">
                {stats?.trial_subscriptions ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">Vencidas</p>
              <p className="text-xl font-semibold text-secondary-900">
                {stats?.past_due_subscriptions ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">MRR</p>
              <p className="text-xl font-semibold text-secondary-900">
                {formatCurrency(stats?.mrr ?? 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-secondary-500">Nuevas este mes</span>
            <span className="text-lg font-semibold text-primary-600">
              +{stats?.new_this_month ?? 0}
            </span>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-secondary-500">Pagos próximos (7 días)</span>
            <span className="text-lg font-semibold text-amber-600">
              {stats?.upcoming_payments ?? 0}
            </span>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-secondary-500">Total Suscripciones</span>
            <span className="text-lg font-semibold text-secondary-900">
              {stats?.total_subscriptions ?? 0}
            </span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
              <Input
                placeholder="Buscar por empresa..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={handleKeyPress}
                className="pl-10"
              />
            </div>
          </div>

          <select
            className="px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={filters.plan ?? ''}
            onChange={(e) => handleFilterChange('plan', e.target.value || undefined)}
          >
            <option value="">Todos los planes</option>
            <option value="free">Gratuito</option>
            <option value="basic">Básico</option>
            <option value="professional">Profesional</option>
            <option value="enterprise">Empresarial</option>
          </select>

          <select
            className="px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={filters.status ?? ''}
            onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
          >
            <option value="">Todos los estados</option>
            <option value="trial">Prueba</option>
            <option value="active">Activa</option>
            <option value="past_due">Vencida</option>
            <option value="cancelled">Cancelada</option>
            <option value="suspended">Suspendida</option>
          </select>

          <Button variant="outline" onClick={handleSearch}>
            <Search className="w-4 h-4 mr-2" />
            Buscar
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-secondary-500">
            Cargando suscripciones...
          </div>
        ) : subscriptions.length === 0 ? (
          <div className="p-8 text-center text-secondary-500">
            <CreditCard className="w-12 h-12 mx-auto mb-4 text-secondary-300" />
            <p>No se encontraron suscripciones</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-secondary-50 border-b border-secondary-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                    Empresa
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                    Plan
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                    Ciclo
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                    Monto
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                    Próximo Pago
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secondary-200">
                {subscriptions.map((subscription) => {
                  const daysUntil = getDaysUntilPayment(subscription.next_payment_date)
                  const isPaymentSoon = daysUntil !== null && daysUntil <= 7 && daysUntil >= 0
                  const isOverdue = daysUntil !== null && daysUntil < 0

                  return (
                    <tr key={subscription.id} className="hover:bg-secondary-50">
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-primary-100 rounded-lg">
                            <Building className="w-4 h-4 text-primary-600" />
                          </div>
                          <div>
                            <p className="font-medium text-secondary-900">
                              {subscription.company_name}
                            </p>
                            <p className="text-sm text-secondary-500">
                              {subscription.company_email}
                            </p>
                          </div>
                          {!subscription.company_is_active && (
                            <Badge variant="secondary" className="text-xs">
                              Inactiva
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <Badge variant={planColors[subscription.plan]}>
                          {planNames[subscription.plan]}
                        </Badge>
                      </td>
                      <td className="px-4 py-4">
                        <Badge variant={statusColors[subscription.status]}>
                          {statusNames[subscription.status]}
                        </Badge>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm text-secondary-600">
                          {subscription.billing_cycle_display}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm font-medium text-secondary-900">
                          {formatCurrency(subscription.amount, subscription.currency)}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-secondary-400" />
                          <span
                            className={`text-sm ${
                              isOverdue
                                ? 'text-red-600 font-medium'
                                : isPaymentSoon
                                ? 'text-amber-600 font-medium'
                                : 'text-secondary-600'
                            }`}
                          >
                            {formatDate(subscription.next_payment_date)}
                          </span>
                          {isOverdue && (
                            <span className="text-xs text-red-500 bg-red-50 px-1.5 py-0.5 rounded">
                              Vencido
                            </span>
                          )}
                          {isPaymentSoon && !isOverdue && daysUntil !== null && (
                            <span className="text-xs text-amber-500 bg-amber-50 px-1.5 py-0.5 rounded">
                              {daysUntil} días
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-secondary-200 flex items-center justify-between">
            <p className="text-sm text-secondary-500">
              Mostrando {subscriptions.length} de {subscriptionsData?.count ?? 0} suscripciones
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={filters.page === 1}
                onClick={() =>
                  setFilters((prev) => ({ ...prev, page: (prev.page ?? 1) - 1 }))
                }
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-sm text-secondary-600">
                Página {filters.page} de {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={filters.page === totalPages}
                onClick={() =>
                  setFilters((prev) => ({ ...prev, page: (prev.page ?? 1) + 1 }))
                }
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
