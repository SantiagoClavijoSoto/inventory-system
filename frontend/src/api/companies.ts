import { apiClient } from './client'
import type {
  Company,
  CompanyListItem,
  CompanyPlan,
  PaginatedResponse,
} from '@/types'

// Request types
export interface CompanyListParams {
  search?: string
  plan?: CompanyPlan
  is_active?: boolean
  include_inactive?: boolean
  page?: number
  page_size?: number
  ordering?: string
}

export interface CreateCompanyRequest {
  name: string
  slug: string
  legal_name?: string
  tax_id?: string
  logo?: File | null
  primary_color?: string
  secondary_color?: string
  email: string
  phone?: string
  website?: string
  address?: string
  plan?: CompanyPlan
  max_branches?: number
  max_users?: number
  max_products?: number
  is_active?: boolean
  owner?: number
}

export interface UpdateCompanyRequest {
  name?: string
  slug?: string
  legal_name?: string
  tax_id?: string
  logo?: File | null
  primary_color?: string
  secondary_color?: string
  email?: string
  phone?: string
  website?: string
  address?: string
  plan?: CompanyPlan
  max_branches?: number
  max_users?: number
  max_products?: number
  is_active?: boolean
}

export interface CompanySimple {
  id: number
  name: string
  slug: string
  primary_color: string
  is_active: boolean
}

export interface CompanyStats {
  company: Company
  limits: {
    max_branches: number
    max_users: number
    max_products: number
    current_branches: number
    current_users: number
    current_products: number
  }
  usage: {
    branches_used: number
    branches_remaining: number
    users_used: number
    users_remaining: number
    products_used: number
    products_remaining: number
  }
  can_add: {
    branch: boolean
    user: boolean
    product: boolean
  }
}

// Company Administrator type (for SuperAdmin view)
export interface CompanyAdmin {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  is_company_admin: boolean
  is_active: boolean
  created_at: string
  // Company info
  company_id: number
  company_name: string
  company_slug: string
  company_plan: CompanyPlan
  company_is_active: boolean
  // Role info
  role_id: number | null
  role_name: string | null
  role_type: string | null
  // Permissions
  can_manage_roles: boolean
}

// Companies API (SuperAdmin only)
export const companiesApi = {
  // Get all companies (paginated)
  getAll: async (params?: CompanyListParams): Promise<PaginatedResponse<CompanyListItem>> => {
    const response = await apiClient.get('/companies/', { params })
    return response.data
  },

  // Get simple list (for dropdowns)
  getSimple: async (): Promise<CompanySimple[]> => {
    const response = await apiClient.get('/companies/simple/')
    return response.data
  },

  // Get single company
  getById: async (id: number): Promise<Company> => {
    const response = await apiClient.get(`/companies/${id}/`)
    return response.data
  },

  // Get company stats
  getStats: async (id: number): Promise<CompanyStats> => {
    const response = await apiClient.get(`/companies/${id}/stats/`)
    return response.data
  },

  // Create company
  create: async (data: CreateCompanyRequest): Promise<Company> => {
    const hasFile = data.logo instanceof File
    if (hasFile) {
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
      const response = await apiClient.post('/companies/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    }
    const response = await apiClient.post('/companies/', data)
    return response.data
  },

  // Update company
  update: async (id: number, data: UpdateCompanyRequest): Promise<Company> => {
    const hasFile = data.logo instanceof File
    if (hasFile) {
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
      const response = await apiClient.patch(`/companies/${id}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    }
    const response = await apiClient.patch(`/companies/${id}/`, data)
    return response.data
  },

  // Delete company (soft delete)
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/companies/${id}/`)
  },

  // Activate company
  activate: async (id: number): Promise<Company> => {
    const response = await apiClient.post(`/companies/${id}/activate/`)
    return response.data
  },

  // Deactivate company
  deactivate: async (id: number): Promise<Company> => {
    const response = await apiClient.post(`/companies/${id}/deactivate/`)
    return response.data
  },

  // Get all company administrators (SuperAdmin only)
  getAdmins: async (): Promise<CompanyAdmin[]> => {
    const response = await apiClient.get('/companies/admins/')
    return response.data
  },

  // Get administrators for a specific company (SuperAdmin only)
  getCompanyAdmins: async (companyId: number): Promise<CompanyAdmin[]> => {
    const response = await apiClient.get(`/companies/${companyId}/company_admins/`)
    return response.data
  },
}
