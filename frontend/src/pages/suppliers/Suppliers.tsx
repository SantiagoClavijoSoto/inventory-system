import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { suppliersApi, type SupplierListParams } from '@/api/suppliers'
import type { Supplier, CreateSupplierRequest } from '@/types'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { formatCurrency } from '@/utils/formatters'
import {
  Plus,
  Search,
  Building2,
  Phone,
  Mail,
  MapPin,
  MoreVertical,
  Edit,
  Trash2,
  Eye,
  Package,
  DollarSign,
  X,
} from 'lucide-react'

export function Suppliers() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<SupplierListParams>({
    page: 1,
    page_size: 20,
  })
  const [searchTerm, setSearchTerm] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null)
  const [activeDropdown, setActiveDropdown] = useState<number | null>(null)

  // Queries
  const { data: suppliersData, isLoading } = useQuery({
    queryKey: ['suppliers', filters],
    queryFn: () => suppliersApi.getAll(filters),
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: CreateSupplierRequest) => suppliersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      setIsModalOpen(false)
      setSelectedSupplier(null)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateSupplierRequest> }) =>
      suppliersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      setIsModalOpen(false)
      setSelectedSupplier(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => suppliersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
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

  const handleEdit = (supplier: Supplier) => {
    setSelectedSupplier(supplier)
    setIsModalOpen(true)
    setActiveDropdown(null)
  }

  const handleViewDetail = (supplier: Supplier) => {
    setSelectedSupplier(supplier)
    setIsDetailModalOpen(true)
    setActiveDropdown(null)
  }

  const handleDelete = (id: number) => {
    if (confirm('¿Estás seguro de que deseas eliminar este proveedor?')) {
      deleteMutation.mutate(id)
    }
    setActiveDropdown(null)
  }

  const handleFilterChange = (key: keyof SupplierListParams, value: string | boolean | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Proveedores</h1>
          <p className="text-secondary-500 mt-1">
            Gestiona tus proveedores y órdenes de compra
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Nuevo Proveedor
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
              <Input
                placeholder="Buscar por nombre, código, contacto..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={handleKeyPress}
                className="pl-10"
              />
            </div>
          </div>

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
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>

          <Input
            placeholder="Filtrar por ciudad"
            value={filters.city || ''}
            onChange={(e) => handleFilterChange('city', e.target.value || undefined)}
            className="w-40"
          />

          <Button variant="outline" onClick={handleSearch}>
            <Search className="w-4 h-4 mr-2" />
            Buscar
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Building2 className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">Total Proveedores</p>
              <p className="text-xl font-bold text-secondary-900">
                {suppliersData?.count || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-success-100 rounded-lg">
              <Building2 className="w-5 h-5 text-success-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">Activos</p>
              <p className="text-xl font-bold text-secondary-900">
                {suppliersData?.results?.filter((s) => s.is_active).length || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-warning-100 rounded-lg">
              <Package className="w-5 h-5 text-warning-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">Órdenes Totales</p>
              <p className="text-xl font-bold text-secondary-900">
                {suppliersData?.results?.reduce((sum, s) => sum + (s.purchase_orders_count || 0), 0) || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-info-100 rounded-lg">
              <DollarSign className="w-5 h-5 text-info-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">Compras Totales</p>
              <p className="text-xl font-bold text-secondary-900">
                {formatCurrency(suppliersData?.results?.reduce((sum, s) => sum + (s.total_purchases || 0), 0) || 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Suppliers Table */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-secondary-50 border-b border-secondary-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Proveedor
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Contacto
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Ubicación
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Términos
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Órdenes
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-secondary-200">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-secondary-500">
                    Cargando proveedores...
                  </td>
                </tr>
              ) : suppliersData?.results?.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-secondary-500">
                    No se encontraron proveedores
                  </td>
                </tr>
              ) : (
                suppliersData?.results?.map((supplier) => (
                  <tr key={supplier.id} className="hover:bg-secondary-50">
                    <td className="px-4 py-4">
                      <div>
                        <div className="font-medium text-secondary-900">{supplier.name}</div>
                        <div className="text-sm text-secondary-500">{supplier.code}</div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="space-y-1">
                        {supplier.contact_name && (
                          <div className="text-sm text-secondary-900">{supplier.contact_name}</div>
                        )}
                        {supplier.email && (
                          <div className="flex items-center gap-1 text-sm text-secondary-500">
                            <Mail className="w-3 h-3" />
                            {supplier.email}
                          </div>
                        )}
                        {supplier.phone && (
                          <div className="flex items-center gap-1 text-sm text-secondary-500">
                            <Phone className="w-3 h-3" />
                            {supplier.phone}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      {supplier.city || supplier.state ? (
                        <div className="flex items-center gap-1 text-sm text-secondary-600">
                          <MapPin className="w-3 h-3" />
                          {[supplier.city, supplier.state].filter(Boolean).join(', ')}
                        </div>
                      ) : (
                        <span className="text-sm text-secondary-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      <div className="text-sm">
                        <div className="text-secondary-900">{supplier.payment_terms} días</div>
                        <div className="text-secondary-500">
                          Límite: {formatCurrency(supplier.credit_limit)}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="text-sm">
                        <div className="font-medium text-secondary-900">
                          {supplier.purchase_orders_count || 0} órdenes
                        </div>
                        <div className="text-secondary-500">
                          {formatCurrency(supplier.total_purchases || 0)}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant={supplier.is_active ? 'success' : 'secondary'}>
                        {supplier.is_active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <div className="relative">
                        <button
                          onClick={() => setActiveDropdown(activeDropdown === supplier.id ? null : supplier.id)}
                          className="p-2 hover:bg-secondary-100 rounded-lg"
                        >
                          <MoreVertical className="w-4 h-4 text-secondary-500" />
                        </button>
                        {activeDropdown === supplier.id && (
                          <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-secondary-200 py-1 z-10">
                            <button
                              onClick={() => handleViewDetail(supplier)}
                              className="w-full px-4 py-2 text-left text-sm text-secondary-700 hover:bg-secondary-50 flex items-center gap-2"
                            >
                              <Eye className="w-4 h-4" />
                              Ver Detalle
                            </button>
                            <button
                              onClick={() => handleEdit(supplier)}
                              className="w-full px-4 py-2 text-left text-sm text-secondary-700 hover:bg-secondary-50 flex items-center gap-2"
                            >
                              <Edit className="w-4 h-4" />
                              Editar
                            </button>
                            <button
                              onClick={() => handleDelete(supplier.id)}
                              className="w-full px-4 py-2 text-left text-sm text-danger-600 hover:bg-danger-50 flex items-center gap-2"
                            >
                              <Trash2 className="w-4 h-4" />
                              Eliminar
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {suppliersData && suppliersData.total_pages > 1 && (
          <div className="px-4 py-3 border-t border-secondary-200 flex items-center justify-between">
            <div className="text-sm text-secondary-500">
              Mostrando página {suppliersData.current_page} de {suppliersData.total_pages}
              {' '}({suppliersData.count} proveedores)
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={!suppliersData.previous}
                onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) - 1 }))}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!suppliersData.next}
                onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))}
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Supplier Form Modal */}
      {isModalOpen && (
        <SupplierFormModal
          supplier={selectedSupplier}
          onClose={() => {
            setIsModalOpen(false)
            setSelectedSupplier(null)
          }}
          onSubmit={(data) => {
            if (selectedSupplier) {
              updateMutation.mutate({ id: selectedSupplier.id, data })
            } else {
              createMutation.mutate(data)
            }
          }}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      )}

      {/* Supplier Detail Modal */}
      {isDetailModalOpen && selectedSupplier && (
        <SupplierDetailModal
          supplier={selectedSupplier}
          onClose={() => {
            setIsDetailModalOpen(false)
            setSelectedSupplier(null)
          }}
        />
      )}
    </div>
  )
}

// Supplier Form Modal Component
interface SupplierFormModalProps {
  supplier: Supplier | null
  onClose: () => void
  onSubmit: (data: CreateSupplierRequest) => void
  isLoading: boolean
}

function SupplierFormModal({ supplier, onClose, onSubmit, isLoading }: SupplierFormModalProps) {
  const [formData, setFormData] = useState<CreateSupplierRequest>({
    name: supplier?.name || '',
    code: supplier?.code || '',
    contact_name: supplier?.contact_name || '',
    email: supplier?.email || '',
    phone: supplier?.phone || '',
    mobile: supplier?.mobile || '',
    address: supplier?.address || '',
    city: supplier?.city || '',
    state: supplier?.state || '',
    postal_code: supplier?.postal_code || '',
    country: supplier?.country || 'México',
    tax_id: supplier?.tax_id || '',
    website: supplier?.website || '',
    notes: supplier?.notes || '',
    payment_terms: supplier?.payment_terms ?? 30,
    credit_limit: supplier?.credit_limit ?? 0,
    is_active: supplier?.is_active ?? true,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleChange = (field: keyof CreateSupplierRequest, value: string | number | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-secondary-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-secondary-900">
            {supplier ? 'Editar Proveedor' : 'Nuevo Proveedor'}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-secondary-100 rounded-lg">
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-sm font-medium text-secondary-900 mb-3">Información Básica</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Nombre *
                  </label>
                  <Input
                    value={formData.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    required
                    placeholder="Nombre del proveedor"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Código *
                  </label>
                  <Input
                    value={formData.code}
                    onChange={(e) => handleChange('code', e.target.value.toUpperCase())}
                    required
                    placeholder="PROV001"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    RFC / Tax ID
                  </label>
                  <Input
                    value={formData.tax_id || ''}
                    onChange={(e) => handleChange('tax_id', e.target.value)}
                    placeholder="RFC del proveedor"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Sitio Web
                  </label>
                  <Input
                    value={formData.website || ''}
                    onChange={(e) => handleChange('website', e.target.value)}
                    placeholder="https://..."
                  />
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div>
              <h3 className="text-sm font-medium text-secondary-900 mb-3">Información de Contacto</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Nombre de Contacto
                  </label>
                  <Input
                    value={formData.contact_name || ''}
                    onChange={(e) => handleChange('contact_name', e.target.value)}
                    placeholder="Nombre del contacto"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Email
                  </label>
                  <Input
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) => handleChange('email', e.target.value)}
                    placeholder="email@proveedor.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Teléfono
                  </label>
                  <Input
                    value={formData.phone || ''}
                    onChange={(e) => handleChange('phone', e.target.value)}
                    placeholder="(55) 1234-5678"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Celular
                  </label>
                  <Input
                    value={formData.mobile || ''}
                    onChange={(e) => handleChange('mobile', e.target.value)}
                    placeholder="(55) 1234-5678"
                  />
                </div>
              </div>
            </div>

            {/* Address */}
            <div>
              <h3 className="text-sm font-medium text-secondary-900 mb-3">Dirección</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Dirección
                  </label>
                  <Input
                    value={formData.address || ''}
                    onChange={(e) => handleChange('address', e.target.value)}
                    placeholder="Calle, número, colonia"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Ciudad
                  </label>
                  <Input
                    value={formData.city || ''}
                    onChange={(e) => handleChange('city', e.target.value)}
                    placeholder="Ciudad"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Estado
                  </label>
                  <Input
                    value={formData.state || ''}
                    onChange={(e) => handleChange('state', e.target.value)}
                    placeholder="Estado"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Código Postal
                  </label>
                  <Input
                    value={formData.postal_code || ''}
                    onChange={(e) => handleChange('postal_code', e.target.value)}
                    placeholder="00000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    País
                  </label>
                  <Input
                    value={formData.country || ''}
                    onChange={(e) => handleChange('country', e.target.value)}
                    placeholder="México"
                  />
                </div>
              </div>
            </div>

            {/* Payment Terms */}
            <div>
              <h3 className="text-sm font-medium text-secondary-900 mb-3">Términos de Pago</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Días de Crédito
                  </label>
                  <Input
                    type="number"
                    value={formData.payment_terms ?? ''}
                    onChange={(e) => handleChange('payment_terms', parseInt(e.target.value) || 0)}
                    placeholder="30"
                    min={0}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Límite de Crédito
                  </label>
                  <Input
                    type="number"
                    value={formData.credit_limit ?? ''}
                    onChange={(e) => handleChange('credit_limit', parseFloat(e.target.value) || 0)}
                    placeholder="0.00"
                    min={0}
                    step="0.01"
                  />
                </div>
              </div>
            </div>

            {/* Notes */}
            <div>
              <h3 className="text-sm font-medium text-secondary-900 mb-3">Notas</h3>
              <textarea
                className="w-full px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                rows={3}
                value={formData.notes || ''}
                onChange={(e) => handleChange('notes', e.target.value)}
                placeholder="Notas adicionales sobre el proveedor..."
              />
            </div>

            {/* Status */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => handleChange('is_active', e.target.checked)}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <label htmlFor="is_active" className="text-sm text-secondary-700">
                Proveedor activo
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-secondary-200">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Guardando...' : supplier ? 'Actualizar' : 'Crear Proveedor'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Supplier Detail Modal Component
interface SupplierDetailModalProps {
  supplier: Supplier
  onClose: () => void
}

function SupplierDetailModal({ supplier, onClose }: SupplierDetailModalProps) {
  const { data: stats } = useQuery({
    queryKey: ['supplier-stats', supplier.id],
    queryFn: () => suppliersApi.getStats(supplier.id),
  })

  const { data: purchaseOrders } = useQuery({
    queryKey: ['supplier-orders', supplier.id],
    queryFn: () => suppliersApi.getPurchaseOrders(supplier.id),
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-secondary-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-secondary-900">{supplier.name}</h2>
            <p className="text-sm text-secondary-500">{supplier.code}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-secondary-100 rounded-lg">
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-secondary-50 rounded-lg p-4">
              <p className="text-sm text-secondary-500">Total Órdenes</p>
              <p className="text-xl font-bold text-secondary-900">{stats?.total_orders || 0}</p>
            </div>
            <div className="bg-secondary-50 rounded-lg p-4">
              <p className="text-sm text-secondary-500">Monto Total</p>
              <p className="text-xl font-bold text-secondary-900">
                {formatCurrency(stats?.total_amount || 0)}
              </p>
            </div>
            <div className="bg-warning-50 rounded-lg p-4">
              <p className="text-sm text-warning-700">Pendientes</p>
              <p className="text-xl font-bold text-warning-900">{stats?.pending_orders || 0}</p>
            </div>
            <div className="bg-success-50 rounded-lg p-4">
              <p className="text-sm text-success-700">Recibidas</p>
              <p className="text-xl font-bold text-success-900">{stats?.received_orders || 0}</p>
            </div>
          </div>

          {/* Contact Info */}
          <div className="grid grid-cols-2 gap-6 mb-6">
            <div>
              <h3 className="text-sm font-medium text-secondary-900 mb-3">Información de Contacto</h3>
              <div className="space-y-2">
                {supplier.contact_name && (
                  <p className="text-sm text-secondary-600">
                    <span className="font-medium">Contacto:</span> {supplier.contact_name}
                  </p>
                )}
                {supplier.email && (
                  <p className="text-sm text-secondary-600 flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    {supplier.email}
                  </p>
                )}
                {supplier.phone && (
                  <p className="text-sm text-secondary-600 flex items-center gap-2">
                    <Phone className="w-4 h-4" />
                    {supplier.phone}
                  </p>
                )}
                {supplier.website && (
                  <p className="text-sm text-secondary-600">
                    <span className="font-medium">Web:</span> {supplier.website}
                  </p>
                )}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-secondary-900 mb-3">Dirección</h3>
              <p className="text-sm text-secondary-600">
                {supplier.full_address || 'No especificada'}
              </p>
              <div className="mt-4">
                <h3 className="text-sm font-medium text-secondary-900 mb-2">Términos</h3>
                <p className="text-sm text-secondary-600">
                  Crédito: {supplier.payment_terms} días
                </p>
                <p className="text-sm text-secondary-600">
                  Límite: {formatCurrency(supplier.credit_limit)}
                </p>
              </div>
            </div>
          </div>

          {/* Recent Orders */}
          <div>
            <h3 className="text-sm font-medium text-secondary-900 mb-3">Órdenes Recientes</h3>
            {purchaseOrders?.results && purchaseOrders.results.length > 0 ? (
              <div className="border border-secondary-200 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-secondary-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">
                        # Orden
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">
                        Fecha
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">
                        Estado
                      </th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-secondary-500">
                        Total
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-secondary-200">
                    {purchaseOrders.results.slice(0, 5).map((order) => (
                      <tr key={order.id}>
                        <td className="px-4 py-2 text-secondary-900">{order.order_number}</td>
                        <td className="px-4 py-2 text-secondary-600">
                          {order.order_date
                            ? new Date(order.order_date).toLocaleDateString()
                            : '-'}
                        </td>
                        <td className="px-4 py-2">
                          <OrderStatusBadge status={order.status} />
                        </td>
                        <td className="px-4 py-2 text-right text-secondary-900">
                          {formatCurrency(order.total)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-secondary-500">No hay órdenes registradas</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Order Status Badge Component
function OrderStatusBadge({ status }: { status: string }) {
  const variants: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'primary' | 'secondary'> = {
    draft: 'secondary',
    pending: 'warning',
    approved: 'primary',
    ordered: 'primary',
    partial: 'warning',
    received: 'success',
    cancelled: 'danger',
  }

  const labels: Record<string, string> = {
    draft: 'Borrador',
    pending: 'Pendiente',
    approved: 'Aprobada',
    ordered: 'Ordenada',
    partial: 'Parcial',
    received: 'Recibida',
    cancelled: 'Cancelada',
  }

  return <Badge variant={variants[status] || 'secondary'}>{labels[status] || status}</Badge>
}
