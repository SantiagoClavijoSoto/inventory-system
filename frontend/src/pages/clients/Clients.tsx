import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { companiesApi, type CompanyListParams } from '@/api/companies'
import type { CompanyPlan } from '@/types'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import {
  Search,
  Building,
  Users,
  Building2,
  MoreVertical,
  Eye,
  Power,
  PowerOff,
  Calendar,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

// Plan badge variants (using valid Badge variants)
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

// Subscription status colors
const statusColors: Record<string, BadgeVariant> = {
  trial: 'primary',
  active: 'success',
  past_due: 'danger',
  cancelled: 'secondary',
  suspended: 'danger',
}

export function Clients() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<CompanyListParams>({
    page: 1,
    page_size: 20,
  })
  const [searchTerm, setSearchTerm] = useState('')
  const [activeDropdown, setActiveDropdown] = useState<number | null>(null)

  // Query
  const { data: companiesData, isLoading } = useQuery({
    queryKey: ['companies', filters],
    queryFn: () => companiesApi.getAll(filters),
  })

  // Mutations
  const activateMutation = useMutation({
    mutationFn: (id: number) => companiesApi.activate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: (id: number) => companiesApi.deactivate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
  })

  const handleSearch = () => {
    setFilters((prev) => ({ ...prev, search: searchTerm, page: 1 }))
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const handleActivate = (id: number) => {
    activateMutation.mutate(id)
    setActiveDropdown(null)
  }

  const handleDeactivate = (id: number) => {
    if (confirm('¿Estás seguro de que deseas desactivar esta empresa?')) {
      deactivateMutation.mutate(id)
    }
    setActiveDropdown(null)
  }

  const handleFilterChange = (key: keyof CompanyListParams, value: string | boolean | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }))
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const getDaysUntilPayment = (dateString?: string) => {
    if (!dateString) return null
    const date = new Date(dateString)
    const today = new Date()
    const diffTime = date.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const companies = companiesData?.results ?? []
  const totalPages = companiesData?.total_pages ?? 1

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Clientes</h1>
          <p className="text-secondary-500 mt-1">
            Gestiona las empresas que utilizan el sistema
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
              <Input
                placeholder="Buscar por nombre, email..."
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
            onChange={(e) =>
              handleFilterChange('plan', e.target.value || undefined)
            }
          >
            <option value="">Todos los planes</option>
            <option value="free">Gratuito</option>
            <option value="basic">Básico</option>
            <option value="professional">Profesional</option>
            <option value="enterprise">Empresarial</option>
          </select>

          <select
            className="px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={filters.is_active?.toString() ?? ''}
            onChange={(e) =>
              handleFilterChange(
                'is_active',
                e.target.value === '' ? undefined : e.target.value === 'true'
              )
            }
          >
            <option value="">Todos los estados</option>
            <option value="true">Activas</option>
            <option value="false">Inactivas</option>
          </select>

          <Button variant="outline" onClick={handleSearch}>
            <Search className="w-4 h-4 mr-2" />
            Buscar
          </Button>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Building className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">Total Empresas</p>
              <p className="text-xl font-semibold text-secondary-900">
                {companiesData?.count ?? 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-secondary-500">
            Cargando empresas...
          </div>
        ) : companies.length === 0 ? (
          <div className="p-8 text-center text-secondary-500">
            <Building className="w-12 h-12 mx-auto mb-4 text-secondary-300" />
            <p>No se encontraron empresas</p>
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
                    Estado Suscripción
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                    Próximo Pago
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                    Usuarios
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                    Sucursales
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-secondary-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secondary-200">
                {companies.map((company) => {
                  const daysUntil = getDaysUntilPayment(company.next_payment_date)
                  const isPaymentSoon = daysUntil !== null && daysUntil <= 7
                  const isOverdue = daysUntil !== null && daysUntil < 0

                  return (
                    <tr key={company.id} className="hover:bg-secondary-50">
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <div
                            className="w-10 h-10 rounded-lg flex items-center justify-center"
                            style={{ backgroundColor: company.primary_color + '20' }}
                          >
                            <Building
                              className="w-5 h-5"
                              style={{ color: company.primary_color }}
                            />
                          </div>
                          <div>
                            <p className="font-medium text-secondary-900">
                              {company.name}
                            </p>
                            <p className="text-sm text-secondary-500">
                              {company.email}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <Badge variant={planColors[company.plan]}>
                          {planNames[company.plan]}
                        </Badge>
                      </td>
                      <td className="px-4 py-4">
                        {company.subscription_status ? (
                          <Badge variant={statusColors[company.subscription_status]}>
                            {company.subscription_status_display}
                          </Badge>
                        ) : (
                          <span className="text-sm text-secondary-400">-</span>
                        )}
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
                            {formatDate(company.next_payment_date)}
                          </span>
                          {isOverdue && (
                            <span className="text-xs text-red-500">
                              (Vencido)
                            </span>
                          )}
                          {isPaymentSoon && !isOverdue && daysUntil !== null && (
                            <span className="text-xs text-amber-500">
                              ({daysUntil} días)
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <Users className="w-4 h-4 text-secondary-400" />
                          <span className="text-sm text-secondary-600">
                            {company.user_count}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-secondary-400" />
                          <span className="text-sm text-secondary-600">
                            {company.branch_count}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-4 text-right">
                        <div className="relative">
                          <button
                            onClick={() =>
                              setActiveDropdown(
                                activeDropdown === company.id ? null : company.id
                              )
                            }
                            className="p-1 hover:bg-secondary-100 rounded"
                          >
                            <MoreVertical className="w-5 h-5 text-secondary-400" />
                          </button>

                          {activeDropdown === company.id && (
                            <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-secondary-200 py-1 z-10">
                              <button
                                onClick={() => {
                                  // TODO: Navigate to detail view
                                  setActiveDropdown(null)
                                }}
                                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-secondary-700 hover:bg-secondary-50"
                              >
                                <Eye className="w-4 h-4" />
                                Ver detalles
                              </button>
                              {company.is_active ? (
                                <button
                                  onClick={() => handleDeactivate(company.id)}
                                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                                >
                                  <PowerOff className="w-4 h-4" />
                                  Desactivar
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleActivate(company.id)}
                                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-green-600 hover:bg-green-50"
                                >
                                  <Power className="w-4 h-4" />
                                  Activar
                                </button>
                              )}
                            </div>
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
              Mostrando {companies.length} de {companiesData?.count ?? 0} empresas
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

      {/* Click outside handler for dropdown */}
      {activeDropdown && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => setActiveDropdown(null)}
        />
      )}
    </div>
  )
}
