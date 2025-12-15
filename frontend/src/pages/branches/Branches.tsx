import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'
import {
  branchesApi,
  type Branch,
  type BranchListParams,
  type CreateBranchRequest,
} from '@/api/branches'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Select,
  Badge,
  Modal,
  ModalFooter,
  Spinner,
} from '@/components/ui'
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Building2,
  MapPin,
  Phone,
  Mail,
  Clock,
  Users,
  Package,
  DollarSign,
  AlertTriangle,
  Star,
  Palette,
  RefreshCw,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { formatCurrency } from '@/utils/formatters'

export function Branches() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()

  // State
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [page, setPage] = useState(1)
  const [selectedBranch, setSelectedBranch] = useState<Branch | null>(null)
  const [isFormModalOpen, setIsFormModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isBrandingModalOpen, setIsBrandingModalOpen] = useState(false)

  // Build query params
  const queryParams: BranchListParams = {
    search: search || undefined,
    is_active: statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined,
    page,
    page_size: 20,
  }

  // Queries
  const { data: branchesData, isLoading } = useQuery({
    queryKey: ['branches', queryParams],
    queryFn: () => branchesApi.getAll(queryParams),
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: branchesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] })
      toast.success('Sucursal creada correctamente')
      setIsFormModalOpen(false)
    },
    onError: () => toast.error('Error al crear sucursal'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateBranchRequest> }) =>
      branchesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] })
      toast.success('Sucursal actualizada correctamente')
      setIsFormModalOpen(false)
      setSelectedBranch(null)
    },
    onError: () => toast.error('Error al actualizar sucursal'),
  })

  const deleteMutation = useMutation({
    mutationFn: branchesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] })
      toast.success('Sucursal eliminada correctamente')
      setIsDeleteModalOpen(false)
      setSelectedBranch(null)
    },
    onError: () => toast.error('Error al eliminar sucursal'),
  })

  const setMainMutation = useMutation({
    mutationFn: branchesApi.setAsMain,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] })
      toast.success('Sucursal establecida como principal')
    },
    onError: () => toast.error('Error al establecer sucursal principal'),
  })

  const handleEdit = (branch: Branch) => {
    setSelectedBranch(branch)
    setIsFormModalOpen(true)
  }

  const handleDelete = (branch: Branch) => {
    setSelectedBranch(branch)
    setIsDeleteModalOpen(true)
  }

  const handleViewDetail = (branch: Branch) => {
    setSelectedBranch(branch)
    setIsDetailModalOpen(true)
  }

  const handleBranding = (branch: Branch) => {
    setSelectedBranch(branch)
    setIsBrandingModalOpen(true)
  }

  const handleSetMain = (branch: Branch) => {
    if (!branch.is_main) {
      setMainMutation.mutate(branch.id)
    }
  }

  const isAdmin = user?.is_platform_admin || user?.role?.role_type === 'admin'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Sucursales</h1>
          <p className="text-secondary-500 mt-1">
            Gestiona las sucursales y su configuración de marca
          </p>
        </div>
        {isAdmin && (
          <Button
            onClick={() => {
              setSelectedBranch(null)
              setIsFormModalOpen(true)
            }}
          >
            <Plus className="h-4 w-4 mr-2" />
            Nueva Sucursal
          </Button>
        )}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-secondary-400" />
              <Input
                placeholder="Buscar por nombre o código..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setPage(1)
                }}
                className="pl-10"
              />
            </div>
            <Select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
              options={[
                { value: '', label: 'Todos los estados' },
                { value: 'active', label: 'Activas' },
                { value: 'inactive', label: 'Inactivas' },
              ]}
            />
            <Button
              variant="outline"
              onClick={() => queryClient.invalidateQueries({ queryKey: ['branches'] })}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Actualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Branch Cards */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : !branchesData?.results?.length ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Building2 className="h-12 w-12 mx-auto text-secondary-300 mb-4" />
            <h3 className="text-lg font-medium text-secondary-900 mb-2">No hay sucursales</h3>
            <p className="text-secondary-500 mb-4">
              {search ? 'No se encontraron sucursales con esos criterios' : 'Crea tu primera sucursal para comenzar'}
            </p>
            {isAdmin && !search && (
              <Button onClick={() => setIsFormModalOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Crear Sucursal
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {branchesData.results.map((branch) => (
            <BranchCard
              key={branch.id}
              branch={branch}
              isAdmin={isAdmin}
              onView={() => handleViewDetail(branch)}
              onEdit={() => handleEdit(branch)}
              onDelete={() => handleDelete(branch)}
              onBranding={() => handleBranding(branch)}
              onSetMain={() => handleSetMain(branch)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {branchesData && branchesData.count > 20 && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={!branchesData.previous}
            onClick={() => setPage((p) => p - 1)}
          >
            Anterior
          </Button>
          <span className="py-2 px-4 text-secondary-600">
            Página {page} de {Math.ceil(branchesData.count / 20)}
          </span>
          <Button
            variant="outline"
            disabled={!branchesData.next}
            onClick={() => setPage((p) => p + 1)}
          >
            Siguiente
          </Button>
        </div>
      )}

      {/* Form Modal */}
      <BranchFormModal
        isOpen={isFormModalOpen}
        onClose={() => {
          setIsFormModalOpen(false)
          setSelectedBranch(null)
        }}
        branch={selectedBranch}
        onSubmit={(data) => {
          if (selectedBranch) {
            updateMutation.mutate({ id: selectedBranch.id, data })
          } else {
            createMutation.mutate(data)
          }
        }}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Eliminar Sucursal"
      >
        <div className="py-4">
          <div className="flex items-center gap-3 p-4 bg-danger-50 rounded-lg mb-4">
            <AlertTriangle className="h-6 w-6 text-danger-500" />
            <div>
              <p className="font-medium text-danger-800">Esta acción no se puede deshacer</p>
              <p className="text-sm text-danger-600">
                Se eliminarán todos los datos asociados a esta sucursal
              </p>
            </div>
          </div>
          <p className="text-secondary-600">
            ¿Estás seguro de que deseas eliminar la sucursal{' '}
            <span className="font-semibold">{selectedBranch?.name}</span>?
          </p>
        </div>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)}>
            Cancelar
          </Button>
          <Button
            variant="danger"
            onClick={() => selectedBranch && deleteMutation.mutate(selectedBranch.id)}
            isLoading={deleteMutation.isPending}
          >
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>

      {/* Detail Modal */}
      {selectedBranch && (
        <BranchDetailModal
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false)
            setSelectedBranch(null)
          }}
          branch={selectedBranch}
        />
      )}

      {/* Branding Modal */}
      {selectedBranch && (
        <BrandingModal
          isOpen={isBrandingModalOpen}
          onClose={() => {
            setIsBrandingModalOpen(false)
            setSelectedBranch(null)
          }}
          branch={selectedBranch}
        />
      )}
    </div>
  )
}

// Branch Card Component
function BranchCard({
  branch,
  isAdmin,
  onView,
  onEdit,
  onDelete,
  onBranding,
  onSetMain,
}: {
  branch: Branch
  isAdmin: boolean
  onView: () => void
  onEdit: () => void
  onDelete: () => void
  onBranding: () => void
  onSetMain: () => void
}) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {branch.logo_url ? (
              <img
                src={branch.logo_url}
                alt={branch.name}
                className="h-12 w-12 rounded-lg object-cover"
              />
            ) : (
              <div
                className="h-12 w-12 rounded-lg flex items-center justify-center text-white font-bold text-lg"
                style={{ backgroundColor: branch.primary_color }}
              >
                {branch.code.substring(0, 2)}
              </div>
            )}
            <div>
              <CardTitle className="text-lg">{branch.display_name || branch.name}</CardTitle>
              <p className="text-sm text-secondary-500">{branch.code}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {branch.is_main && (
              <Badge variant="warning" className="flex items-center gap-1">
                <Star className="h-3 w-3" />
                Principal
              </Badge>
            )}
            <Badge variant={branch.is_active ? 'success' : 'secondary'}>
              {branch.is_active ? 'Activa' : 'Inactiva'}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Contact Info */}
        <div className="space-y-2 text-sm">
          {branch.full_address && (
            <div className="flex items-start gap-2 text-secondary-600">
              <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>{branch.full_address}</span>
            </div>
          )}
          {branch.phone && (
            <div className="flex items-center gap-2 text-secondary-600">
              <Phone className="h-4 w-4 flex-shrink-0" />
              <span>{branch.phone}</span>
            </div>
          )}
          {branch.email && (
            <div className="flex items-center gap-2 text-secondary-600">
              <Mail className="h-4 w-4 flex-shrink-0" />
              <span>{branch.email}</span>
            </div>
          )}
          {(branch.opening_time || branch.closing_time) && (
            <div className="flex items-center gap-2 text-secondary-600">
              <Clock className="h-4 w-4 flex-shrink-0" />
              <span>
                {branch.opening_time?.substring(0, 5)} - {branch.closing_time?.substring(0, 5)}
              </span>
            </div>
          )}
        </div>

        {/* Brand Colors Preview */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-secondary-500">Colores:</span>
          <div
            className="h-5 w-5 rounded-full border border-secondary-200"
            style={{ backgroundColor: branch.primary_color }}
            title="Primario"
          />
          <div
            className="h-5 w-5 rounded-full border border-secondary-200"
            style={{ backgroundColor: branch.secondary_color }}
            title="Secundario"
          />
          <div
            className="h-5 w-5 rounded-full border border-secondary-200"
            style={{ backgroundColor: branch.accent_color }}
            title="Acento"
          />
        </div>

        {/* Quick Stats */}
        <div className="flex items-center gap-4 pt-2 border-t border-secondary-100">
          <div className="flex items-center gap-1 text-sm text-secondary-600">
            <Users className="h-4 w-4" />
            <span>{branch.employee_count}</span>
          </div>
          <div className="text-sm text-secondary-600">
            {branch.currency_symbol} {branch.tax_rate}% IVA
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button variant="outline" size="sm" className="flex-1" onClick={onView}>
            Ver Detalles
          </Button>
          {isAdmin && (
            <>
              <Button variant="outline" size="sm" onClick={onBranding} title="Configurar marca">
                <Palette className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={onEdit} title="Editar">
                <Edit2 className="h-4 w-4" />
              </Button>
              {!branch.is_main && (
                <>
                  <Button variant="outline" size="sm" onClick={onSetMain} title="Establecer como principal">
                    <Star className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm" onClick={onDelete} title="Eliminar">
                    <Trash2 className="h-4 w-4 text-danger-500" />
                  </Button>
                </>
              )}
            </>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// Branch Form Modal
function BranchFormModal({
  isOpen,
  onClose,
  branch,
  onSubmit,
  isLoading,
}: {
  isOpen: boolean
  onClose: () => void
  branch: Branch | null
  onSubmit: (data: CreateBranchRequest) => void
  isLoading: boolean
}) {
  const [formData, setFormData] = useState<CreateBranchRequest>({
    name: '',
    code: '',
    address: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'Colombia',
    phone: '',
    email: '',
    manager_name: '',
    manager_phone: '',
    is_active: true,
    is_main: false,
    opening_time: '09:00',
    closing_time: '18:00',
    tax_rate: 19,
    currency: 'COP',
    currency_symbol: '$',
  })

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      if (branch) {
        setFormData({
          name: branch.name,
          code: branch.code,
          address: branch.address || '',
          city: branch.city || '',
          state: branch.state || '',
          postal_code: branch.postal_code || '',
          country: branch.country,
          phone: branch.phone || '',
          email: branch.email || '',
          manager_name: branch.manager_name || '',
          manager_phone: branch.manager_phone || '',
          is_active: branch.is_active,
          is_main: branch.is_main,
          opening_time: branch.opening_time?.substring(0, 5) || '09:00',
          closing_time: branch.closing_time?.substring(0, 5) || '18:00',
          tax_rate: branch.tax_rate,
          currency: branch.currency,
          currency_symbol: branch.currency_symbol,
        })
      } else {
        setFormData({
          name: '',
          code: '',
          address: '',
          city: '',
          state: '',
          postal_code: '',
          country: 'Colombia',
          phone: '',
          email: '',
          manager_name: '',
          manager_phone: '',
          is_active: true,
          is_main: false,
          opening_time: '09:00',
          closing_time: '18:00',
          tax_rate: 19,
          currency: 'COP',
          currency_symbol: '$',
        })
      }
    }
  }, [isOpen, branch])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={branch ? 'Editar Sucursal' : 'Nueva Sucursal'}
      size="lg"
    >
      <form onSubmit={handleSubmit}>
        <div className="space-y-6 py-4">
          {/* Basic Info */}
          <div>
            <h3 className="text-sm font-medium text-secondary-700 mb-3">Información Básica</h3>
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Nombre *"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
              <Input
                label="Código *"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                required
                maxLength={10}
              />
            </div>
          </div>

          {/* Address */}
          <div>
            <h3 className="text-sm font-medium text-secondary-700 mb-3">Dirección</h3>
            <div className="grid grid-cols-1 gap-4">
              <Input
                label="Dirección"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Ciudad"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                />
                <Input
                  label="Estado"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Código Postal"
                  value={formData.postal_code}
                  onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                />
                <Input
                  label="País"
                  value={formData.country}
                  onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                />
              </div>
            </div>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-sm font-medium text-secondary-700 mb-3">Contacto</h3>
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Teléfono"
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
              <Input
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
              <Input
                label="Nombre del Gerente"
                value={formData.manager_name}
                onChange={(e) => setFormData({ ...formData, manager_name: e.target.value })}
              />
              <Input
                label="Teléfono del Gerente"
                type="tel"
                value={formData.manager_phone}
                onChange={(e) => setFormData({ ...formData, manager_phone: e.target.value })}
              />
            </div>
          </div>

          {/* Schedule */}
          <div>
            <h3 className="text-sm font-medium text-secondary-700 mb-3">Horario</h3>
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Hora de Apertura"
                type="time"
                value={formData.opening_time}
                onChange={(e) => setFormData({ ...formData, opening_time: e.target.value })}
              />
              <Input
                label="Hora de Cierre"
                type="time"
                value={formData.closing_time}
                onChange={(e) => setFormData({ ...formData, closing_time: e.target.value })}
              />
            </div>
          </div>

          {/* Business Config */}
          <div>
            <h3 className="text-sm font-medium text-secondary-700 mb-3">Configuración Fiscal</h3>
            <div className="grid grid-cols-3 gap-4">
              <Input
                label="Tasa de Impuesto (%)"
                type="number"
                step="0.01"
                value={formData.tax_rate}
                onChange={(e) => setFormData({ ...formData, tax_rate: parseFloat(e.target.value) })}
              />
              <Input
                label="Moneda"
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                maxLength={3}
              />
              <Input
                label="Símbolo"
                value={formData.currency_symbol}
                onChange={(e) => setFormData({ ...formData, currency_symbol: e.target.value })}
                maxLength={3}
              />
            </div>
          </div>

          {/* Status */}
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded border-secondary-300"
              />
              <span className="text-sm text-secondary-700">Sucursal Activa</span>
            </label>
          </div>
        </div>

        <ModalFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={isLoading}>
            {branch ? 'Actualizar' : 'Crear'} Sucursal
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}

// Branch Detail Modal with Stats
function BranchDetailModal({
  isOpen,
  onClose,
  branch,
}: {
  isOpen: boolean
  onClose: () => void
  branch: Branch
}) {
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['branch-stats', branch.id],
    queryFn: () => branchesApi.getStats(branch.id),
    enabled: isOpen,
  })

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={branch.display_name || branch.name} size="lg">
      <div className="py-4 space-y-6">
        {/* Header with Logo */}
        <div className="flex items-center gap-4 pb-4 border-b">
          {branch.logo_url ? (
            <img
              src={branch.logo_url}
              alt={branch.name}
              className="h-20 w-20 rounded-lg object-cover"
            />
          ) : (
            <div
              className="h-20 w-20 rounded-lg flex items-center justify-center text-white font-bold text-2xl"
              style={{ backgroundColor: branch.primary_color }}
            >
              {branch.code.substring(0, 2)}
            </div>
          )}
          <div>
            <h2 className="text-xl font-bold text-secondary-900">{branch.name}</h2>
            <p className="text-secondary-500">{branch.code}</p>
            <div className="flex gap-2 mt-2">
              {branch.is_main && (
                <Badge variant="warning">
                  <Star className="h-3 w-3 mr-1" />
                  Principal
                </Badge>
              )}
              <Badge variant={branch.is_active ? 'success' : 'secondary'}>
                {branch.is_active ? 'Activa' : 'Inactiva'}
              </Badge>
            </div>
          </div>
        </div>

        {/* Stats */}
        {loadingStats ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : stats ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              icon={<Package className="h-5 w-5 text-primary-500" />}
              label="Productos"
              value={stats.total_products.toString()}
            />
            <StatCard
              icon={<DollarSign className="h-5 w-5 text-success-500" />}
              label="Valor en Stock"
              value={formatCurrency(stats.total_stock_value || 0)}
            />
            <StatCard
              icon={<Users className="h-5 w-5 text-secondary-500" />}
              label="Empleados Activos"
              value={stats.active_employees.toString()}
            />
            <StatCard
              icon={<AlertTriangle className="h-5 w-5 text-warning-500" />}
              label="Alertas Stock"
              value={stats.low_stock_alerts.toString()}
            />
          </div>
        ) : null}

        {/* Sales Summary */}
        {stats && (
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardContent className="pt-4">
                <h4 className="text-sm font-medium text-secondary-500 mb-2">Ventas Hoy</h4>
                <p className="text-2xl font-bold text-secondary-900">
                  {formatCurrency(stats.sales_amount_today || 0)}
                </p>
                <p className="text-sm text-secondary-500">{stats.sales_today} transacciones</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <h4 className="text-sm font-medium text-secondary-500 mb-2">Ventas Este Mes</h4>
                <p className="text-2xl font-bold text-secondary-900">
                  {formatCurrency(stats.sales_amount_this_month || 0)}
                </p>
                <p className="text-sm text-secondary-500">{stats.sales_this_month} transacciones</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Contact & Location */}
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-secondary-700 mb-3">Contacto</h4>
            <div className="space-y-2 text-sm">
              {branch.phone && (
                <div className="flex items-center gap-2 text-secondary-600">
                  <Phone className="h-4 w-4" />
                  {branch.phone}
                </div>
              )}
              {branch.email && (
                <div className="flex items-center gap-2 text-secondary-600">
                  <Mail className="h-4 w-4" />
                  {branch.email}
                </div>
              )}
              {branch.manager_name && (
                <div className="flex items-center gap-2 text-secondary-600">
                  <Users className="h-4 w-4" />
                  {branch.manager_name}
                  {branch.manager_phone && ` (${branch.manager_phone})`}
                </div>
              )}
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium text-secondary-700 mb-3">Ubicación</h4>
            <div className="space-y-2 text-sm">
              {branch.full_address && (
                <div className="flex items-start gap-2 text-secondary-600">
                  <MapPin className="h-4 w-4 mt-0.5" />
                  {branch.full_address}
                </div>
              )}
              {(branch.opening_time || branch.closing_time) && (
                <div className="flex items-center gap-2 text-secondary-600">
                  <Clock className="h-4 w-4" />
                  {branch.opening_time?.substring(0, 5)} - {branch.closing_time?.substring(0, 5)}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Brand Colors */}
        <div>
          <h4 className="text-sm font-medium text-secondary-700 mb-3">Colores de Marca</h4>
          <div className="flex gap-4">
            <ColorSwatch color={branch.primary_color} label="Primario" />
            <ColorSwatch color={branch.secondary_color} label="Secundario" />
            <ColorSwatch color={branch.accent_color} label="Acento" />
          </div>
        </div>
      </div>

      <ModalFooter>
        <Button variant="outline" onClick={onClose}>
          Cerrar
        </Button>
      </ModalFooter>
    </Modal>
  )
}

// Branding Configuration Modal
function BrandingModal({
  isOpen,
  onClose,
  branch,
}: {
  isOpen: boolean
  onClose: () => void
  branch: Branch
}) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    store_name: branch.store_name || '',
    primary_color: branch.primary_color,
    secondary_color: branch.secondary_color,
    accent_color: branch.accent_color,
    tax_rate: branch.tax_rate,
    currency: branch.currency,
    currency_symbol: branch.currency_symbol,
  })
  const [logoFile, setLogoFile] = useState<File | null>(null)
  const [logoPreview, setLogoPreview] = useState<string | null>(branch.logo_url || null)

  const updateMutation = useMutation({
    mutationFn: (data: { logo?: File | null } & typeof formData) =>
      branchesApi.updateBranding(branch.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] })
      queryClient.invalidateQueries({ queryKey: ['branch-branding'] })
      toast.success('Configuración de marca actualizada')
      onClose()
    },
    onError: () => toast.error('Error al actualizar la marca'),
  })

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setLogoFile(file)
      const reader = new FileReader()
      reader.onload = (event) => {
        setLogoPreview(event.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate({
      ...formData,
      logo: logoFile,
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Configuración de Marca" size="lg">
      <form onSubmit={handleSubmit}>
        <div className="py-4 space-y-6">
          {/* Store Name & Logo */}
          <div>
            <h3 className="text-sm font-medium text-secondary-700 mb-3">Identidad Visual</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Input
                  label="Nombre de Tienda"
                  value={formData.store_name}
                  onChange={(e) => setFormData({ ...formData, store_name: e.target.value })}
                  placeholder={branch.name}
                />
                <p className="text-xs text-secondary-500 mt-1">
                  Se mostrará en lugar del nombre de sucursal
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">Logo</label>
                <div className="flex items-center gap-4">
                  {logoPreview ? (
                    <img
                      src={logoPreview}
                      alt="Logo preview"
                      className="h-16 w-16 rounded-lg object-cover border"
                    />
                  ) : (
                    <div
                      className="h-16 w-16 rounded-lg flex items-center justify-center text-white font-bold"
                      style={{ backgroundColor: formData.primary_color }}
                    >
                      {branch.code.substring(0, 2)}
                    </div>
                  )}
                  <label className="cursor-pointer">
                    <span className="text-sm text-primary-600 hover:text-primary-700">
                      Cambiar logo
                    </span>
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleLogoChange}
                    />
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Colors */}
          <div>
            <h3 className="text-sm font-medium text-secondary-700 mb-3">Colores</h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Color Primario
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formData.primary_color}
                    onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                    className="h-10 w-16 rounded cursor-pointer"
                  />
                  <Input
                    value={formData.primary_color}
                    onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                    className="flex-1"
                    maxLength={7}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Color Secundario
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formData.secondary_color}
                    onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })}
                    className="h-10 w-16 rounded cursor-pointer"
                  />
                  <Input
                    value={formData.secondary_color}
                    onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })}
                    className="flex-1"
                    maxLength={7}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Color Acento
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formData.accent_color}
                    onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                    className="h-10 w-16 rounded cursor-pointer"
                  />
                  <Input
                    value={formData.accent_color}
                    onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                    className="flex-1"
                    maxLength={7}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Preview */}
          <div>
            <h3 className="text-sm font-medium text-secondary-700 mb-3">Vista Previa</h3>
            <div
              className="p-4 rounded-lg border"
              style={{ backgroundColor: formData.primary_color + '10' }}
            >
              <div className="flex items-center gap-3 mb-3">
                {logoPreview ? (
                  <img src={logoPreview} alt="Preview" className="h-10 w-10 rounded object-cover" />
                ) : (
                  <div
                    className="h-10 w-10 rounded flex items-center justify-center text-white font-bold"
                    style={{ backgroundColor: formData.primary_color }}
                  >
                    {branch.code.substring(0, 2)}
                  </div>
                )}
                <span className="font-semibold" style={{ color: formData.primary_color }}>
                  {formData.store_name || branch.name}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="px-4 py-2 rounded text-white text-sm"
                  style={{ backgroundColor: formData.primary_color }}
                >
                  Botón Primario
                </button>
                <button
                  type="button"
                  className="px-4 py-2 rounded text-white text-sm"
                  style={{ backgroundColor: formData.secondary_color }}
                >
                  Secundario
                </button>
                <button
                  type="button"
                  className="px-4 py-2 rounded text-white text-sm"
                  style={{ backgroundColor: formData.accent_color }}
                >
                  Acento
                </button>
              </div>
            </div>
          </div>

          {/* Business Settings */}
          <div>
            <h3 className="text-sm font-medium text-secondary-700 mb-3">Configuración Fiscal</h3>
            <div className="grid grid-cols-3 gap-4">
              <Input
                label="Tasa de Impuesto (%)"
                type="number"
                step="0.01"
                value={formData.tax_rate}
                onChange={(e) => setFormData({ ...formData, tax_rate: parseFloat(e.target.value) })}
              />
              <Input
                label="Moneda"
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                maxLength={3}
              />
              <Input
                label="Símbolo"
                value={formData.currency_symbol}
                onChange={(e) => setFormData({ ...formData, currency_symbol: e.target.value })}
                maxLength={3}
              />
            </div>
          </div>
        </div>

        <ModalFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={updateMutation.isPending}>
            Guardar Cambios
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}

// Helper Components
function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="bg-secondary-50 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-xs text-secondary-500">{label}</span>
      </div>
      <p className="text-xl font-bold text-secondary-900">{value}</p>
    </div>
  )
}

function ColorSwatch({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className="h-8 w-8 rounded-full border border-secondary-200"
        style={{ backgroundColor: color }}
      />
      <div>
        <p className="text-xs text-secondary-500">{label}</p>
        <p className="text-sm font-mono">{color}</p>
      </div>
    </div>
  )
}
