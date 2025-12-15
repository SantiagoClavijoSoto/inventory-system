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
      '/sales/',
      { params: filters }
    )
    return response.data
  },

  getById: async (id: number) => {
    const response = await apiClient.get<Sale>(`/sales/${id}/`)
    return response.data
  },

  create: async (data: CreateSaleRequest) => {
    const response = await apiClient.post<Sale>('/sales/', data)
    return response.data
  },

  void: async (id: number, reason: string) => {
    const response = await apiClient.post<Sale>(`/sales/${id}/void/`, {
      reason,
    })
    return response.data
  },

  refund: async (
    id: number,
    items: { sale_item_id: number; quantity: number }[],
    reason: string
  ) => {
    const response = await apiClient.post<Sale>(`/sales/${id}/refund/`, {
      items,
      reason,
    })
    return response.data
  },

  getDailySummary: async (branchId?: number, date?: string) => {
    const response = await apiClient.get<DailySummary>(
      '/sales/daily_summary/',
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
      '/sales/top_products/',
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
    }>(`/sales/${id}/receipt/`)
    return response.data
  },

  downloadReceiptPdf: async (id: number, saleNumber: string) => {
    const response = await apiClient.get(`/sales/${id}/receipt_pdf/`, {
      responseType: 'blob',
    })

    // Create a blob URL and trigger download
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `recibo_${saleNumber}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },
}

// Cash Register API
export const cashRegisterApi = {
  getAll: async (filters?: { branch?: number; page?: number }) => {
    const response = await apiClient.get<PaginatedResponse<DailyCashRegister>>(
      '/registers/',
      { params: filters }
    )
    return response.data
  },

  getById: async (id: number) => {
    const response = await apiClient.get<DailyCashRegister>(
      `/registers/${id}/`
    )
    return response.data
  },

  getCurrent: async (branchId: number) => {
    const response = await apiClient.get<DailyCashRegister>(
      '/registers/current/',
      { params: { branch: branchId } }
    )
    return response.data
  },

  open: async (branchId: number, openingAmount: number) => {
    const response = await apiClient.post<DailyCashRegister>(
      '/registers/open/',
      {
        branch_id: branchId,
        opening_amount: openingAmount,
      }
    )
    return response.data
  },

  close: async (id: number, closingAmount: number, notes?: string) => {
    const response = await apiClient.post<DailyCashRegister>(
      `/registers/${id}/close/`,
      {
        closing_amount: closingAmount,
        notes,
      }
    )
    return response.data
  },
}
