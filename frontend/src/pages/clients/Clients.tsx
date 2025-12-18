import { useState, useEffect } from 'react'
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
  Plus,
  X,
  Pencil,
} from 'lucide-react'
import toast from 'react-hot-toast'

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
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null)
  const [editCompanyId, setEditCompanyId] = useState<number | null>(null)

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
    return new Date(dateString).toLocaleDateString('es-CO', {
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
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Nueva Empresa
        </Button>
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
                                  setSelectedCompanyId(company.id)
                                  setActiveDropdown(null)
                                }}
                                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-secondary-700 hover:bg-secondary-50"
                              >
                                <Eye className="w-4 h-4" />
                                Ver detalles
                              </button>
                              <button
                                onClick={() => {
                                  setEditCompanyId(company.id)
                                  setActiveDropdown(null)
                                }}
                                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-secondary-700 hover:bg-secondary-50"
                              >
                                <Pencil className="w-4 h-4" />
                                Editar
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

      {/* Company Details Modal */}
      {selectedCompanyId && (
        <CompanyDetailsModal
          companyId={selectedCompanyId}
          onClose={() => setSelectedCompanyId(null)}
        />
      )}

      {/* Create Company Modal */}
      <CreateCompanyModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['companies'] })
          setIsCreateModalOpen(false)
        }}
      />

      {/* Edit Company Modal */}
      {editCompanyId && (
        <EditCompanyModal
          companyId={editCompanyId}
          onClose={() => setEditCompanyId(null)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['companies'] })
            setEditCompanyId(null)
          }}
        />
      )}
    </div>
  )
}

// Create Company Modal Component
function CreateCompanyModal({
  isOpen,
  onClose,
  onSuccess,
}: {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}) {
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    email: '',
    phone: '',
    legal_name: '',
    tax_id: '',
    address: '',
    plan: 'basic' as CompanyPlan,
    billing_cycle: 'monthly' as 'monthly' | 'quarterly' | 'semiannual' | 'annual',
    subscription_status: 'trial' as 'trial' | 'active' | 'past_due' | 'cancelled' | 'suspended',
    primary_color: '#3B82F6',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Auto-generate slug from name
  const handleNameChange = (name: string) => {
    const slug = name
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
    setFormData({ ...formData, name, slug })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name || !formData.email || !formData.slug) {
      toast.error('Nombre, slug y email son requeridos')
      return
    }

    setIsSubmitting(true)
    try {
      await companiesApi.create(formData)
      toast.success('Empresa creada exitosamente')
      setFormData({
        name: '',
        slug: '',
        email: '',
        phone: '',
        legal_name: '',
        tax_id: '',
        address: '',
        plan: 'basic',
        billing_cycle: 'monthly',
        subscription_status: 'trial',
        primary_color: '#3B82F6',
      })
      onSuccess()
    } catch (error: unknown) {
      const err = error as { response?: { data?: { slug?: string[]; email?: string[] } } }
      if (err.response?.data?.slug) {
        toast.error(`Slug: ${err.response.data.slug[0]}`)
      } else if (err.response?.data?.email) {
        toast.error(`Email: ${err.response.data.email[0]}`)
      } else {
        toast.error('Error al crear la empresa')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-secondary-200">
          <h2 className="text-lg font-semibold text-secondary-900">Nueva Empresa</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-secondary-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Nombre de la Empresa *
              </label>
              <Input
                value={formData.name}
                onChange={(e) => handleNameChange(e.target.value)}
                placeholder="Mi Empresa S.A.S"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Slug (URL) *
              </label>
              <Input
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                placeholder="mi-empresa"
                required
              />
              <p className="text-xs text-secondary-500 mt-1">Identificador único para URLs</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Email *
              </label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="contacto@empresa.com"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Teléfono
              </label>
              <Input
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+57 300 123 4567"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Razón Social
              </label>
              <Input
                value={formData.legal_name}
                onChange={(e) => setFormData({ ...formData, legal_name: e.target.value })}
                placeholder="Nombre legal completo"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                NIT / ID Tributario
              </label>
              <Input
                value={formData.tax_id}
                onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
                placeholder="900.123.456-7"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">
              Dirección
            </label>
            <Input
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              placeholder="Dirección de la empresa"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Plan
              </label>
              <select
                className="w-full px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={formData.plan}
                onChange={(e) => setFormData({ ...formData, plan: e.target.value as CompanyPlan })}
              >
                <option value="free">Gratuito</option>
                <option value="basic">Básico</option>
                <option value="professional">Profesional</option>
                <option value="enterprise">Empresarial</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Ciclo de Facturación
              </label>
              <select
                className="w-full px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={formData.billing_cycle}
                onChange={(e) => setFormData({ ...formData, billing_cycle: e.target.value as typeof formData.billing_cycle })}
              >
                <option value="monthly">Mensual</option>
                <option value="quarterly">Trimestral (3 meses)</option>
                <option value="semiannual">Semestral (6 meses)</option>
                <option value="annual">Anual (12 meses)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Estado Suscripción
              </label>
              <select
                className="w-full px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={formData.subscription_status}
                onChange={(e) => setFormData({ ...formData, subscription_status: e.target.value as typeof formData.subscription_status })}
              >
                <option value="trial">Prueba</option>
                <option value="active">Activa</option>
                <option value="past_due">Vencida</option>
                <option value="cancelled">Cancelada</option>
                <option value="suspended">Suspendida</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">
              Color Principal
            </label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={formData.primary_color}
                onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                className="w-10 h-10 rounded border border-secondary-300 cursor-pointer"
              />
              <Input
                value={formData.primary_color}
                onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                placeholder="#3B82F6"
                className="flex-1"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-secondary-200">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creando...' : 'Crear Empresa'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Company Details Modal Component
function CompanyDetailsModal({
  companyId,
  onClose,
}: {
  companyId: number
  onClose: () => void
}) {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['company-stats', companyId],
    queryFn: () => companiesApi.getStats(companyId),
  })

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  const formatCurrency = (amount?: number) => {
    if (!amount) return '$0'
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-secondary-200">
          <h2 className="text-lg font-semibold text-secondary-900">
            {isLoading ? 'Cargando...' : stats?.company.name}
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-secondary-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-secondary-500">
            Cargando detalles...
          </div>
        ) : stats ? (
          <div className="p-4 space-y-6">
            {/* Company Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-secondary-500 uppercase">Email</p>
                  <p className="text-sm font-medium">{stats.company.email}</p>
                </div>
                <div>
                  <p className="text-xs text-secondary-500 uppercase">Teléfono</p>
                  <p className="text-sm font-medium">{stats.company.phone || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-secondary-500 uppercase">Dirección</p>
                  <p className="text-sm font-medium">{stats.company.address || '-'}</p>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-secondary-500 uppercase">Razón Social</p>
                  <p className="text-sm font-medium">{stats.company.legal_name || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-secondary-500 uppercase">NIT</p>
                  <p className="text-sm font-medium">{stats.company.tax_id || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-secondary-500 uppercase">Creada</p>
                  <p className="text-sm font-medium">{formatDate(stats.company.created_at)}</p>
                </div>
              </div>
            </div>

            {/* Plan & Subscription */}
            <div className="border-t border-secondary-200 pt-4">
              <h3 className="text-sm font-semibold text-secondary-900 mb-3">Plan y Suscripción</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-secondary-50 rounded-lg p-3">
                  <p className="text-xs text-secondary-500 uppercase">Plan Actual</p>
                  <p className="text-lg font-semibold capitalize">{planNames[stats.company.plan]}</p>
                </div>
                <div className="bg-secondary-50 rounded-lg p-3">
                  <p className="text-xs text-secondary-500 uppercase">Estado</p>
                  <Badge variant={stats.company.is_active ? 'success' : 'danger'}>
                    {stats.company.is_active ? 'Activa' : 'Inactiva'}
                  </Badge>
                </div>
                <div className="bg-secondary-50 rounded-lg p-3">
                  <p className="text-xs text-secondary-500 uppercase">Próximo Pago</p>
                  <p className="text-sm font-medium">
                    {stats.company.subscription?.next_payment_date
                      ? formatDate(stats.company.subscription.next_payment_date)
                      : 'Sin suscripción'}
                  </p>
                </div>
              </div>
            </div>

            {/* Usage Stats */}
            <div className="border-t border-secondary-200 pt-4">
              <h3 className="text-sm font-semibold text-secondary-900 mb-3">Uso de Recursos</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Building2 className="w-4 h-4 text-blue-600" />
                    <p className="text-xs text-blue-600 uppercase">Sucursales</p>
                  </div>
                  <p className="text-xl font-semibold text-blue-900">
                    {stats.usage.branches_used} / {stats.limits.max_branches}
                  </p>
                  <div className="w-full bg-blue-200 rounded-full h-1.5 mt-2">
                    <div
                      className="bg-blue-600 h-1.5 rounded-full"
                      style={{ width: `${Math.min((stats.usage.branches_used / stats.limits.max_branches) * 100, 100)}%` }}
                    />
                  </div>
                </div>
                <div className="bg-green-50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Users className="w-4 h-4 text-green-600" />
                    <p className="text-xs text-green-600 uppercase">Usuarios</p>
                  </div>
                  <p className="text-xl font-semibold text-green-900">
                    {stats.usage.users_used} / {stats.limits.max_users}
                  </p>
                  <div className="w-full bg-green-200 rounded-full h-1.5 mt-2">
                    <div
                      className="bg-green-600 h-1.5 rounded-full"
                      style={{ width: `${Math.min((stats.usage.users_used / stats.limits.max_users) * 100, 100)}%` }}
                    />
                  </div>
                </div>
                <div className="bg-purple-50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Building className="w-4 h-4 text-purple-600" />
                    <p className="text-xs text-purple-600 uppercase">Productos</p>
                  </div>
                  <p className="text-xl font-semibold text-purple-900">
                    {stats.usage.products_used} / {stats.limits.max_products}
                  </p>
                  <div className="w-full bg-purple-200 rounded-full h-1.5 mt-2">
                    <div
                      className="bg-purple-600 h-1.5 rounded-full"
                      style={{ width: `${Math.min((stats.usage.products_used / stats.limits.max_products) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Subscription Details if exists */}
            {stats.company.subscription && (
              <div className="border-t border-secondary-200 pt-4">
                <h3 className="text-sm font-semibold text-secondary-900 mb-3">Detalles de Suscripción</h3>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-secondary-500 uppercase">Ciclo</p>
                    <p className="text-sm font-medium capitalize">
                      {stats.company.subscription.billing_cycle === 'monthly' ? 'Mensual' :
                       stats.company.subscription.billing_cycle === 'quarterly' ? 'Trimestral' :
                       stats.company.subscription.billing_cycle === 'semiannual' ? 'Semestral' : 'Anual'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-secondary-500 uppercase">Monto</p>
                    <p className="text-sm font-medium">{formatCurrency(stats.company.subscription.amount)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-secondary-500 uppercase">Estado</p>
                    <Badge variant={statusColors[stats.company.subscription.status] || 'secondary'}>
                      {stats.company.subscription.status_display || stats.company.subscription.status}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-xs text-secondary-500 uppercase">Próximo Pago</p>
                    <p className="text-sm font-medium">{formatDate(stats.company.subscription.next_payment_date)}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-8 text-center text-secondary-500">
            No se encontraron datos
          </div>
        )}

        <div className="flex justify-end gap-3 p-4 border-t border-secondary-200">
          <Button variant="outline" onClick={onClose}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  )
}

// Edit Company Modal Component
function EditCompanyModal({
  companyId,
  onClose,
  onSuccess,
}: {
  companyId: number
  onClose: () => void
  onSuccess: () => void
}) {
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    email: '',
    phone: '',
    legal_name: '',
    tax_id: '',
    address: '',
    plan: 'basic' as CompanyPlan,
    subscription_status: 'trial' as 'trial' | 'active' | 'past_due' | 'cancelled' | 'suspended',
    primary_color: '#3B82F6',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Load company data with subscription
  const { data: stats, isLoading } = useQuery({
    queryKey: ['company-stats', companyId],
    queryFn: () => companiesApi.getStats(companyId),
  })

  // Populate form when company data loads
  useEffect(() => {
    if (stats?.company) {
      setFormData({
        name: stats.company.name || '',
        slug: stats.company.slug || '',
        email: stats.company.email || '',
        phone: stats.company.phone || '',
        legal_name: stats.company.legal_name || '',
        tax_id: stats.company.tax_id || '',
        address: stats.company.address || '',
        plan: stats.company.plan || 'basic',
        subscription_status: stats.company.subscription?.status || 'trial',
        primary_color: stats.company.primary_color || '#3B82F6',
      })
    }
  }, [stats])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name || !formData.email) {
      toast.error('Nombre y email son requeridos')
      return
    }

    setIsSubmitting(true)
    try {
      await companiesApi.update(companyId, formData)
      toast.success('Empresa actualizada exitosamente')
      onSuccess()
    } catch (error: unknown) {
      const err = error as { response?: { data?: { slug?: string[]; email?: string[] } } }
      if (err.response?.data?.slug) {
        toast.error(`Slug: ${err.response.data.slug[0]}`)
      } else if (err.response?.data?.email) {
        toast.error(`Email: ${err.response.data.email[0]}`)
      } else {
        toast.error('Error al actualizar la empresa')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-secondary-200">
          <h2 className="text-lg font-semibold text-secondary-900">Editar Empresa</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-secondary-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-secondary-500">
            Cargando datos...
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Nombre de la Empresa *
                </label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Mi Empresa S.A.S"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Slug (URL) *
                </label>
                <Input
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  placeholder="mi-empresa"
                  required
                />
                <p className="text-xs text-secondary-500 mt-1">Identificador único para URLs</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Email *
                </label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="contacto@empresa.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Teléfono
                </label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+57 300 123 4567"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Razón Social
                </label>
                <Input
                  value={formData.legal_name}
                  onChange={(e) => setFormData({ ...formData, legal_name: e.target.value })}
                  placeholder="Nombre legal completo"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  NIT / ID Tributario
                </label>
                <Input
                  value={formData.tax_id}
                  onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
                  placeholder="900.123.456-7"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Dirección
              </label>
              <Input
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                placeholder="Dirección de la empresa"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Plan
                </label>
                <select
                  className="w-full px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={formData.plan}
                  onChange={(e) => setFormData({ ...formData, plan: e.target.value as CompanyPlan })}
                >
                  <option value="free">Gratuito</option>
                  <option value="basic">Básico</option>
                  <option value="professional">Profesional</option>
                  <option value="enterprise">Empresarial</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Estado Suscripción
                </label>
                <select
                  className="w-full px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={formData.subscription_status}
                  onChange={(e) => setFormData({ ...formData, subscription_status: e.target.value as typeof formData.subscription_status })}
                >
                  <option value="trial">Prueba</option>
                  <option value="active">Activa</option>
                  <option value="past_due">Vencida</option>
                  <option value="cancelled">Cancelada</option>
                  <option value="suspended">Suspendida</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Color Principal
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={formData.primary_color}
                  onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                  className="w-10 h-10 rounded border border-secondary-300 cursor-pointer"
                />
                <Input
                  value={formData.primary_color}
                  onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                  placeholder="#3B82F6"
                  className="flex-1"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-secondary-200">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Guardando...' : 'Guardar Cambios'}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
