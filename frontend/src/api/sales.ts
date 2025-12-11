import { apiClient } from './client'
import type {
  Sale,
  CreateSaleRequest,
  DailySummary,
  TopProduct,
  DailyCashRegister,
  PaginatedResponse,
} from '@/types'

// Sale API
export const saleApi = {
  getAll: async (filters?: {
    branch?: number
    date_from?: string
    date_to?: string
    status?: string
    cashier?: number
    payment_method?: string
    page?: number
    page_size?: number
  }) => {
    const response = await apiClient.get<PaginatedResponse<Sale>>(
      '/sales/sales/',
      { params: filters }
    )
    return response.data
  },

  getById: async (id: number) => {
    const response = await apiClient.get<Sale>(`/sales/sales/${id}/`)
    return response.data
  },

  create: async (data: CreateSaleRequest) => {
    const response = await apiClient.post<Sale>('/sales/sales/', data)
    return response.data
  },

  void: async (id: number, reason: string) => {
    const response = await apiClient.post<Sale>(`/sales/sales/${id}/void/`, {
      reason,
    })
    return response.data
  },

  refund: async (
    id: number,
    items: { sale_item_id: number; quantity: number }[],
    reason: string
  ) => {
    const response = await apiClient.post<Sale>(`/sales/sales/${id}/refund/`, {
      items,
      reason,
    })
    return response.data
  },

  getDailySummary: async (branchId?: number, date?: string) => {
    const response = await apiClient.get<DailySummary>(
      '/sales/sales/daily_summary/',
      {
        params: {
          branch: branchId,
          date,
        },
      }
    )
    return response.data
  },

  getTopProducts: async (
    branchId?: number,
    dateFrom?: string,
    dateTo?: string,
    limit?: number
  ) => {
    const response = await apiClient.get<TopProduct[]>(
      '/sales/sales/top_products/',
      {
        params: {
          branch: branchId,
          date_from: dateFrom,
          date_to: dateTo,
          limit,
        },
      }
    )
    return response.data
  },

  getReceipt: async (id: number) => {
    const response = await apiClient.get<{
      sale_number: string
      date: string
      branch: {
        name: string
        address: string
        phone: string
      }
      cashier: string
      items: {
        name: string
        sku: string
        quantity: number
        unit_price: string
        discount: string
        subtotal: string
      }[]
      subtotal: string
      discount: string
      tax: string
      total: string
      payment_method: string
      amount_tendered: string
      change: string
      customer_name: string
    }>(`/sales/sales/${id}/receipt/`)
    return response.data
  },
}

// Cash Register API
export const cashRegisterApi = {
  getAll: async (filters?: { branch?: number; page?: number }) => {
    const response = await apiClient.get<PaginatedResponse<DailyCashRegister>>(
      '/sales/cash-register/',
      { params: filters }
    )
    return response.data
  },

  getById: async (id: number) => {
    const response = await apiClient.get<DailyCashRegister>(
      `/sales/cash-register/${id}/`
    )
    return response.data
  },

  getCurrent: async (branchId: number) => {
    const response = await apiClient.get<DailyCashRegister>(
      '/sales/cash-register/current/',
      { params: { branch: branchId } }
    )
    return response.data
  },

  open: async (branchId: number, openingAmount: number) => {
    const response = await apiClient.post<DailyCashRegister>(
      '/sales/cash-register/open/',
      {
        branch_id: branchId,
        opening_amount: openingAmount,
      }
    )
    return response.data
  },

  close: async (id: number, closingAmount: number, notes?: string) => {
    const response = await apiClient.post<DailyCashRegister>(
      `/sales/cash-register/${id}/close/`,
      {
        closing_amount: closingAmount,
        notes,
      }
    )
    return response.data
  },
}
