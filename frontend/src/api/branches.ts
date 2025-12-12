import { apiClient } from './client'

// Types
export interface Branch {
  id: number
  name: string
  code: string
  address?: string
  city?: string
  state?: string
  postal_code?: string
  country: string
  phone?: string
  email?: string
  manager_name?: string
  manager_phone?: string
  is_active: boolean
  is_main: boolean
  opening_time?: string
  closing_time?: string
  full_address?: string
  // Branding
  store_name?: string
  display_name: string
  logo?: string
  logo_url?: string
  favicon?: string
  favicon_url?: string
  primary_color: string
  secondary_color: string
  accent_color: string
  // Business config
  tax_rate: number
  currency: string
  currency_symbol: string
  receipt_header?: string
  receipt_footer?: string
  // Meta
  employee_count: number
  created_at: string
  updated_at: string
}

export interface BranchSimple {
  id: number
  name: string
  code: string
  is_main: boolean
  display_name: string
  primary_color: string
}

export interface BranchStats {
  total_products: number
  total_stock_value: number
  sales_today: number
  sales_amount_today: number
  sales_this_month: number
  sales_amount_this_month: number
  active_employees: number
  low_stock_alerts: number
}

export interface BranchBranding {
  id: number
  store_name?: string
  display_name: string
  logo?: string
  logo_url?: string
  favicon?: string
  favicon_url?: string
  primary_color: string
  secondary_color: string
  accent_color: string
  tax_rate: number
  currency: string
  currency_symbol: string
}

export interface BranchListParams {
  search?: string
  is_active?: boolean
  is_main?: boolean
  city?: string
  state?: string
  simple?: boolean
  page?: number
  page_size?: number
}

export interface CreateBranchRequest {
  name: string
  code: string
  address?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  phone?: string
  email?: string
  manager_name?: string
  manager_phone?: string
  is_active?: boolean
  is_main?: boolean
  opening_time?: string
  closing_time?: string
  // Branding
  store_name?: string
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  // Business config
  tax_rate?: number
  currency?: string
  currency_symbol?: string
  receipt_header?: string
  receipt_footer?: string
}

export interface UpdateBrandingRequest {
  store_name?: string
  logo?: File | null
  favicon?: File | null
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  tax_rate?: number
  currency?: string
  currency_symbol?: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// Branch API
export const branchesApi = {
  // Get all branches
  getAll: async (params?: BranchListParams): Promise<PaginatedResponse<Branch>> => {
    const response = await apiClient.get('/branches/', { params })
    return response.data
  },

  // Get simple list (for dropdowns)
  getSimple: async (): Promise<BranchSimple[]> => {
    const response = await apiClient.get('/branches/simple/')
    return response.data
  },

  // Get single branch
  getById: async (id: number): Promise<Branch> => {
    const response = await apiClient.get(`/branches/${id}/`)
    return response.data
  },

  // Get branch stats
  getStats: async (id: number): Promise<BranchStats> => {
    const response = await apiClient.get(`/branches/${id}/stats/`)
    return response.data
  },

  // Get branding info
  getBranding: async (id: number): Promise<BranchBranding> => {
    const response = await apiClient.get(`/branches/${id}/branding/`)
    return response.data
  },

  // Create branch
  create: async (data: CreateBranchRequest): Promise<Branch> => {
    const response = await apiClient.post('/branches/', data)
    return response.data
  },

  // Update branch
  update: async (id: number, data: Partial<CreateBranchRequest>): Promise<Branch> => {
    const response = await apiClient.patch(`/branches/${id}/`, data)
    return response.data
  },

  // Update branding with file support
  updateBranding: async (id: number, data: UpdateBrandingRequest): Promise<BranchBranding> => {
    // Use FormData if there are files
    const hasFiles = data.logo instanceof File || data.favicon instanceof File
    if (hasFiles) {
      const formData = new FormData()
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (value instanceof File) {
            formData.append(key, value)
          } else {
            formData.append(key, String(value))
          }
        }
      })
      const response = await apiClient.patch(`/branches/${id}/branding/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    }
    const response = await apiClient.patch(`/branches/${id}/branding/`, data)
    return response.data
  },

  // Delete branch
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/branches/${id}/`)
  },

  // Set as main branch
  setAsMain: async (id: number): Promise<Branch> => {
    const response = await apiClient.post(`/branches/${id}/set-main/`)
    return response.data
  },
}
