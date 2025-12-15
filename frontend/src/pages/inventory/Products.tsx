import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productApi, categoryApi } from '@/api/inventory'
import { useAuthStore } from '@/store/authStore'
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
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  Spinner,
} from '@/components/ui'
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Package,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import toast from 'react-hot-toast'
import type { Product, Category, ProductUnit } from '@/types'

export function Products() {
  const queryClient = useQueryClient()
  const currentBranch = useAuthStore((state) => state.currentBranch)

  // State
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [page, setPage] = useState(1)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)

  // Queries
  const { data: productsData, isLoading } = useQuery({
    queryKey: ['products', { search, category: categoryFilter, status: statusFilter, page, branch: currentBranch?.id }],
    queryFn: () =>
      productApi.getAll({
        search: search || undefined,
        category: categoryFilter ? Number(categoryFilter) : undefined,
        is_active: statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined,
        page,
        page_size: 20,
        branch: currentBranch?.id,
      }),
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: categoryApi.getTree,
  })

  // Mutations
  const deleteMutation = useMutation({
    mutationFn: productApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      toast.success('Producto eliminado correctamente')
      setIsDeleteModalOpen(false)
      setSelectedProduct(null)
    },
    onError: () => {
      toast.error('Error al eliminar el producto')
    },
  })

  const handleDelete = () => {
    if (selectedProduct) {
      deleteMutation.mutate(selectedProduct.id)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
    }).format(value)
  }

  const getStockBadge = (product: Product) => {
    const stock = product.total_stock || 0
    if (stock === 0) {
      return <Badge variant="danger">Sin stock</Badge>
    }
    if (stock <= product.min_stock) {
      return <Badge variant="warning">Stock bajo</Badge>
    }
    return <Badge variant="success">{stock} unidades</Badge>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Productos</h1>
          <p className="text-secondary-500">
            Gestiona el catálogo de productos de tu inventario
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4" />
          Nuevo Producto
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
                <input
                  type="text"
                  placeholder="Buscar por nombre, SKU o código de barras..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value)
                    setPage(1)
                  }}
                  className="w-full pl-10 pr-4 py-2 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <Select
              options={[
                { value: '', label: 'Todas las categorías' },
                ...(categories?.map((c) => ({ value: String(c.id), label: c.name })) || []),
              ]}
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value)
                setPage(1)
              }}
              className="w-48"
            />

            <Select
              options={[
                { value: '', label: 'Todos los estados' },
                { value: 'active', label: 'Activos' },
                { value: 'inactive', label: 'Inactivos' },
              ]}
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
              className="w-40"
            />

            <Button
              variant="secondary"
              onClick={() => {
                setSearch('')
                setCategoryFilter('')
                setStatusFilter('')
                setPage(1)
              }}
            >
              <RefreshCw className="w-4 h-4" />
              Limpiar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {productsData?.count || 0} productos encontrados
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Spinner size="lg" />
            </div>
          ) : productsData?.results.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-secondary-500">
              <Package className="w-12 h-12 mb-4 text-secondary-300" />
              <p className="text-lg font-medium">No se encontraron productos</p>
              <p className="text-sm">Intenta ajustar los filtros de búsqueda</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Producto</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Categoría</TableHead>
                  <TableHead className="text-right">Precio Costo</TableHead>
                  <TableHead className="text-right">Precio Venta</TableHead>
                  <TableHead>Stock</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="w-20">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {productsData?.results.map((product) => (
                  <TableRow key={product.id} clickable>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {product.image ? (
                          <img
                            src={product.image}
                            alt={product.name}
                            className="w-10 h-10 rounded-lg object-cover"
                          />
                        ) : (
                          <div className="w-10 h-10 bg-secondary-100 rounded-lg flex items-center justify-center">
                            <Package className="w-5 h-5 text-secondary-400" />
                          </div>
                        )}
                        <div>
                          <p className="font-medium text-secondary-900">{product.name}</p>
                          {product.barcode && (
                            <p className="text-xs text-secondary-500">{product.barcode}</p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">{product.sku}</TableCell>
                    <TableCell>{product.category_name}</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(product.cost_price)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(product.sale_price)}
                    </TableCell>
                    <TableCell>{getStockBadge(product)}</TableCell>
                    <TableCell>
                      {product.is_active ? (
                        <Badge variant="success">Activo</Badge>
                      ) : (
                        <Badge variant="secondary">Inactivo</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => {
                            setSelectedProduct(product)
                            setIsModalOpen(true)
                          }}
                          className="p-2 hover:bg-secondary-100 rounded-lg transition-colors"
                        >
                          <Edit2 className="w-4 h-4 text-secondary-600" />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedProduct(product)
                            setIsDeleteModalOpen(true)
                          }}
                          className="p-2 hover:bg-danger-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4 text-danger-600" />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>

        {/* Pagination */}
        {productsData && productsData.total_pages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-secondary-200">
            <p className="text-sm text-secondary-500">
              Página {productsData.current_page} de {productsData.total_pages}
            </p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={!productsData.previous}
                onClick={() => setPage(page - 1)}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={!productsData.next}
                onClick={() => setPage(page + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Product Form Modal */}
      <ProductFormModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setSelectedProduct(null)
        }}
        product={selectedProduct}
        categories={categories || []}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false)
          setSelectedProduct(null)
        }}
        title="Eliminar Producto"
      >
        <div className="flex items-start gap-4">
          <div className="p-3 bg-danger-100 rounded-full">
            <AlertTriangle className="w-6 h-6 text-danger-600" />
          </div>
          <div>
            <p className="text-secondary-900">
              ¿Estás seguro de que deseas eliminar el producto{' '}
              <strong>{selectedProduct?.name}</strong>?
            </p>
            <p className="text-sm text-secondary-500 mt-1">
              Esta acción no se puede deshacer.
            </p>
          </div>
        </div>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => {
              setIsDeleteModalOpen(false)
              setSelectedProduct(null)
            }}
          >
            Cancelar
          </Button>
          <Button
            variant="danger"
            onClick={handleDelete}
            isLoading={deleteMutation.isPending}
          >
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}

// Product Form Modal Component
interface ProductFormModalProps {
  isOpen: boolean
  onClose: () => void
  product: Product | null
  categories: Category[]
}

function ProductFormModal({ isOpen, onClose, product, categories }: ProductFormModalProps) {
  const queryClient = useQueryClient()
  const isEditing = !!product

  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false)
  const [newCategoryName, setNewCategoryName] = useState('')

  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    barcode: '',
    description: '',
    category: '',
    cost_price: '',
    sale_price: '',
    unit: 'unit',
    min_stock: '10',
    max_stock: '100',
    is_active: true,
    is_sellable: true,
  })

  // Reset form when modal opens/closes or product changes
  useEffect(() => {
    if (isOpen) {
      if (product) {
        setFormData({
          name: product.name,
          sku: product.sku,
          barcode: product.barcode || '',
          description: product.description || '',
          category: String(product.category),
          cost_price: String(product.cost_price),
          sale_price: String(product.sale_price),
          unit: product.unit,
          min_stock: String(product.min_stock),
          max_stock: String(product.max_stock),
          is_active: product.is_active,
          is_sellable: product.is_sellable,
        })
      } else {
        setFormData({
          name: '',
          sku: '',
          barcode: '',
          description: '',
          category: '',
          cost_price: '',
          sale_price: '',
          unit: 'unit',
          min_stock: '10',
          max_stock: '100',
          is_active: true,
          is_sellable: true,
        })
      }
    }
  }, [isOpen, product])

  const createMutation = useMutation({
    mutationFn: productApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      toast.success('Producto creado correctamente')
      onClose()
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Error al crear el producto'
      toast.error(message)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Product> }) =>
      productApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      toast.success('Producto actualizado correctamente')
      onClose()
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Error al actualizar el producto'
      toast.error(message)
    },
  })

  const createCategoryMutation = useMutation({
    mutationFn: (name: string) => categoryApi.create({ name, is_active: true }),
    onSuccess: (newCategory) => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      toast.success('Categoría creada correctamente')
      setFormData({ ...formData, category: String(newCategory.id) })
      setIsCategoryModalOpen(false)
      setNewCategoryName('')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Error al crear la categoría'
      toast.error(message)
    },
  })

  const handleCreateCategory = () => {
    if (newCategoryName.trim()) {
      createCategoryMutation.mutate(newCategoryName.trim())
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data: Partial<Product> = {
      name: formData.name,
      sku: formData.sku,
      ...(formData.barcode && { barcode: formData.barcode }),
      description: formData.description,
      category: Number(formData.category),
      cost_price: Number(formData.cost_price),
      sale_price: Number(formData.sale_price),
      unit: formData.unit as ProductUnit,
      min_stock: Number(formData.min_stock),
      max_stock: Number(formData.max_stock),
      is_active: formData.is_active,
      is_sellable: formData.is_sellable,
    }

    if (isEditing && product) {
      updateMutation.mutate({ id: product.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  return (
    <>
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Editar Producto' : 'Nuevo Producto'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Nombre del producto"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Input
            label="SKU"
            value={formData.sku}
            onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Código de barras"
            value={formData.barcode}
            onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
          />
          <div>
            <div className="flex items-end gap-2">
              <div className="flex-1">
                <Select
                  label="Categoría"
                  options={categories.map((c) => ({ value: String(c.id), label: c.name }))}
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  placeholder="Seleccionar categoría"
                />
              </div>
              <Button
                type="button"
                variant="outline"
                className="mb-0"
                onClick={() => setIsCategoryModalOpen(true)}
                title="Crear nueva categoría"
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <Input
            label="Precio de costo"
            type="number"
            step="0.01"
            value={formData.cost_price}
            onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
            required
          />
          <Input
            label="Precio de venta"
            type="number"
            step="0.01"
            value={formData.sale_price}
            onChange={(e) => setFormData({ ...formData, sale_price: e.target.value })}
            required
          />
          <Select
            label="Unidad"
            options={[
              { value: 'unit', label: 'Unidad' },
              { value: 'kg', label: 'Kilogramo' },
              { value: 'g', label: 'Gramo' },
              { value: 'l', label: 'Litro' },
              { value: 'ml', label: 'Mililitro' },
              { value: 'm', label: 'Metro' },
              { value: 'box', label: 'Caja' },
              { value: 'pack', label: 'Paquete' },
            ]}
            value={formData.unit}
            onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Stock mínimo"
            type="number"
            value={formData.min_stock}
            onChange={(e) => setFormData({ ...formData, min_stock: e.target.value })}
            required
          />
          <Input
            label="Stock máximo"
            type="number"
            value={formData.max_stock}
            onChange={(e) => setFormData({ ...formData, max_stock: e.target.value })}
            required
          />
        </div>

        <div className="flex gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-secondary-700">Producto activo</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.is_sellable}
              onChange={(e) => setFormData({ ...formData, is_sellable: e.target.checked })}
              className="rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-secondary-700">Disponible para venta</span>
          </label>
        </div>

        <ModalFooter>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={isLoading}>
            {isEditing ? 'Guardar cambios' : 'Crear producto'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>

    {/* Category Creation Modal */}
    <Modal
      isOpen={isCategoryModalOpen}
      onClose={() => {
        setIsCategoryModalOpen(false)
        setNewCategoryName('')
      }}
      title="Nueva Categoría"
      size="sm"
      zIndex="z-[60]"
    >
      <div className="space-y-4" onClick={(e) => e.stopPropagation()}>
        <Input
          label="Nombre de la categoría"
          value={newCategoryName}
          onChange={(e) => setNewCategoryName(e.target.value)}
          onMouseDown={(e) => e.stopPropagation()}
          placeholder="Ej: Herramientas, Electrónica..."
          autoFocus
        />
      </div>
      <ModalFooter>
        <Button
          type="button"
          variant="secondary"
          onClick={() => {
            setIsCategoryModalOpen(false)
            setNewCategoryName('')
          }}
        >
          Cancelar
        </Button>
        <Button
          onClick={handleCreateCategory}
          isLoading={createCategoryMutation.isPending}
          disabled={!newCategoryName.trim()}
        >
          Crear categoría
        </Button>
      </ModalFooter>
    </Modal>
    </>
  )
}
