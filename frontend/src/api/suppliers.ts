import { apiClient } from './client'
import type {
  Supplier,
  PurchaseOrder,
  CreateSupplierRequest,
  SupplierStats,
  PaginatedResponse,
} from '@/types'

export interface SupplierListParams {
  search?: string
  is_active?: boolean
  city?: string
  page?: number
  page_size?: number
}

export interface PurchaseOrderListParams {
  supplier?: number
  branch?: number
  status?: string
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

export const suppliersApi = {
  // Supplier CRUD
  getAll: async (params?: SupplierListParams): Promise<PaginatedResponse<Supplier>> => {
    const response = await apiClient.get('/suppliers/', { params })
    return response.data
  },

  getById: async (id: number): Promise<Supplier> => {
    const response = await apiClient.get(`/suppliers/${id}/`)
    return response.data
  },

  create: async (data: CreateSupplierRequest): Promise<Supplier> => {
    const response = await apiClient.post('/suppliers/', data)
    return response.data
  },

  update: async (id: number, data: Partial<CreateSupplierRequest>): Promise<Supplier> => {
    const response = await apiClient.patch(`/suppliers/${id}/`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/suppliers/${id}/`)
  },

  // Supplier actions
  getPurchaseOrders: async (id: number, params?: { status?: string }): Promise<PaginatedResponse<PurchaseOrder>> => {
    const response = await apiClient.get(`/suppliers/${id}/purchase_orders/`, { params })
    return response.data
  },

  getStats: async (id: number): Promise<SupplierStats> => {
    const response = await apiClient.get(`/suppliers/${id}/stats/`)
    return response.data
  },
}

export interface CreatePurchaseOrderItem {
  product_id: number
  quantity_ordered: number
  unit_price: number
}

export interface CreatePurchaseOrderRequest {
  supplier: number
  branch: number
  order_date?: string
  expected_date?: string
  notes?: string
  items: CreatePurchaseOrderItem[]
}

export interface ReceiveItemRequest {
  item_id: number
  quantity_received: number
}

export const purchaseOrdersApi = {
  // Purchase Order CRUD
  getAll: async (params?: PurchaseOrderListParams): Promise<PaginatedResponse<PurchaseOrder>> => {
    const response = await apiClient.get('/purchase-orders/', { params })
    return response.data
  },

  getById: async (id: number): Promise<PurchaseOrder> => {
    const response = await apiClient.get(`/purchase-orders/${id}/`)
    return response.data
  },

  create: async (data: CreatePurchaseOrderRequest): Promise<PurchaseOrder> => {
    const response = await apiClient.post('/purchase-orders/', data)
    return response.data
  },

  update: async (id: number, data: { order_date?: string; expected_date?: string; notes?: string }): Promise<PurchaseOrder> => {
    const response = await apiClient.patch(`/purchase-orders/${id}/`, data)
    return response.data
  },

  // Purchase Order actions
  approve: async (id: number): Promise<PurchaseOrder> => {
    const response = await apiClient.post(`/purchase-orders/${id}/approve/`)
    return response.data
  },

  receive: async (id: number, items: ReceiveItemRequest[]): Promise<PurchaseOrder> => {
    const response = await apiClient.post(`/purchase-orders/${id}/receive/`, { items })
    return response.data
  },

  cancel: async (id: number): Promise<PurchaseOrder> => {
    const response = await apiClient.post(`/purchase-orders/${id}/cancel/`)
    return response.data
  },

  getSummary: async (): Promise<{
    total_orders: number
    total_amount: number
    by_status: Record<string, number>
  }> => {
    const response = await apiClient.get('/purchase-orders/summary/')
    return response.data
  },
}
