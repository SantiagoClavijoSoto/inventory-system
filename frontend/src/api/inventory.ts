import { apiClient } from './client'
import type {
  Product,
  Category,
  BranchStock,
  StockMovement,
  PaginatedResponse,
} from '@/types'

// Types for API responses
interface ProductListResponse extends PaginatedResponse<Product> {}

interface BarcodeSearchResponse {
  product: Product
  stock_in_branch: number
  available_in_branch: number
}

interface StockAdjustmentRequest {
  product_id: number
  branch_id: number
  adjustment_type: 'add' | 'subtract' | 'set'
  quantity: number
  reason: string
  notes?: string
}

interface StockTransferRequest {
  product_id: number
  from_branch_id: number
  to_branch_id: number
  quantity: number
  notes?: string
}

interface ProductFilters {
  name?: string
  sku?: string
  barcode?: string
  category?: number
  category_tree?: number
  supplier?: number
  min_price?: number
  max_price?: number
  is_active?: boolean
  is_sellable?: boolean
  search?: string
  ordering?: string
  page?: number
  page_size?: number
}

// Category API
export const categoryApi = {
  getAll: async () => {
    const response = await apiClient.get<Category[]>('/inventory/categories/')
    return response.data
  },

  getTree: async () => {
    const response = await apiClient.get<Category[]>('/inventory/categories/tree/')
    return response.data
  },

  getRoot: async () => {
    const response = await apiClient.get<Category[]>('/inventory/categories/root/')
    return response.data
  },

  getById: async (id: number) => {
    const response = await apiClient.get<Category>(`/inventory/categories/${id}/`)
    return response.data
  },

  create: async (data: Partial<Category>) => {
    const response = await apiClient.post<Category>('/inventory/categories/', data)
    return response.data
  },

  update: async (id: number, data: Partial<Category>) => {
    const response = await apiClient.patch<Category>(
      `/inventory/categories/${id}/`,
      data
    )
    return response.data
  },

  delete: async (id: number) => {
    await apiClient.delete(`/inventory/categories/${id}/`)
  },
}

// Product API
export const productApi = {
  getAll: async (filters?: ProductFilters) => {
    const response = await apiClient.get<ProductListResponse>(
      '/inventory/products/',
      { params: filters }
    )
    return response.data
  },

  getById: async (id: number) => {
    const response = await apiClient.get<Product>(`/inventory/products/${id}/`)
    return response.data
  },

  getByBarcode: async (code: string, branchId: number) => {
    const response = await apiClient.get<BarcodeSearchResponse>(
      `/inventory/products/barcode/${code}/`,
      { params: { branch_id: branchId } }
    )
    return response.data
  },

  getStock: async (productId: number) => {
    const response = await apiClient.get<BranchStock[]>(
      `/inventory/products/${productId}/stock/`
    )
    return response.data
  },

  getMovements: async (productId: number, branchId?: number) => {
    const response = await apiClient.get<StockMovement[]>(
      `/inventory/products/${productId}/movements/`,
      { params: branchId ? { branch_id: branchId } : undefined }
    )
    return response.data
  },

  getLowStock: async (branchId?: number) => {
    const response = await apiClient.get<any[]>('/inventory/products/low_stock/', {
      params: branchId ? { branch_id: branchId } : undefined,
    })
    return response.data
  },

  create: async (data: FormData | Partial<Product>) => {
    const config = data instanceof FormData
      ? { headers: { 'Content-Type': 'multipart/form-data' } }
      : {}
    const response = await apiClient.post<Product>(
      '/inventory/products/',
      data,
      config
    )
    return response.data
  },

  update: async (id: number, data: FormData | Partial<Product>) => {
    const config = data instanceof FormData
      ? { headers: { 'Content-Type': 'multipart/form-data' } }
      : {}
    const response = await apiClient.patch<Product>(
      `/inventory/products/${id}/`,
      data,
      config
    )
    return response.data
  },

  delete: async (id: number) => {
    await apiClient.delete(`/inventory/products/${id}/`)
  },
}

// Stock API
export const stockApi = {
  adjust: async (data: StockAdjustmentRequest) => {
    const response = await apiClient.post<StockMovement>(
      '/inventory/stock/adjust/',
      data
    )
    return response.data
  },

  transfer: async (data: StockTransferRequest) => {
    const response = await apiClient.post<{
      outgoing: StockMovement
      incoming: StockMovement
    }>('/inventory/stock/transfer/', data)
    return response.data
  },

  getByBranch: async (branchId: number) => {
    const response = await apiClient.get<BranchStock[]>(
      '/inventory/stock/by_branch/',
      { params: { branch_id: branchId } }
    )
    return response.data
  },
}

// Stock Movement API
export const movementApi = {
  getAll: async (filters?: {
    product?: number
    branch?: number
    movement_type?: string
    created_by?: number
    date_from?: string
    date_to?: string
    page?: number
    page_size?: number
  }) => {
    const response = await apiClient.get<PaginatedResponse<StockMovement>>(
      '/inventory/movements/',
      { params: filters }
    )
    return response.data
  },

  getById: async (id: number) => {
    const response = await apiClient.get<StockMovement>(
      `/inventory/movements/${id}/`
    )
    return response.data
  },
}

// Stock Alerts API
export const alertApi = {
  getAll: async () => {
    const response = await apiClient.get('/inventory/alerts/')
    return response.data
  },

  getActive: async (branchId?: number) => {
    const response = await apiClient.get('/inventory/alerts/active/', {
      params: branchId ? { branch_id: branchId } : undefined,
    })
    return response.data
  },

  create: async (data: any) => {
    const response = await apiClient.post('/inventory/alerts/', data)
    return response.data
  },

  update: async (id: number, data: any) => {
    const response = await apiClient.patch(`/inventory/alerts/${id}/`, data)
    return response.data
  },

  delete: async (id: number) => {
    await apiClient.delete(`/inventory/alerts/${id}/`)
  },
}
