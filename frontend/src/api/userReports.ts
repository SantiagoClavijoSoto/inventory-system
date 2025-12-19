import { apiClient } from './client'

// Types
export type ReportCategory = 'inventario' | 'empleados' | 'sucursales'
export type ReportStatus = 'pendiente' | 'en_revision' | 'resuelto'
export type ReportPriority = 'baja' | 'media' | 'alta' | 'urgente'

export interface UserReport {
  id: number
  title: string
  description: string
  category: ReportCategory
  category_display: string
  priority: ReportPriority
  priority_display: string
  status: ReportStatus
  status_display: string
  created_by: number
  created_by_name: string
  assign_to_all: boolean
  assigned_employees: number[]
  assigned_employee_names: string[]
  reviewed_at: string | null
  reviewed_by: number | null
  reviewed_by_name: string | null
  resolved_at: string | null
  resolved_by: number | null
  resolved_by_name: string | null
  resolution_notes: string
  can_change_status: boolean
  created_at: string
  updated_at: string
}

export interface UserReportListItem {
  id: number
  title: string
  category: ReportCategory
  category_display: string
  priority: ReportPriority
  priority_display: string
  status: ReportStatus
  status_display: string
  created_by_name: string
  created_at: string
}

export interface CreateUserReportData {
  title: string
  description: string
  category: ReportCategory
  priority?: ReportPriority
  assign_to_all?: boolean
  assigned_employees?: number[]
}

export interface UpdateUserReportData {
  title?: string
  description?: string
  priority?: ReportPriority
  assign_to_all?: boolean
  assigned_employees?: number[]
}

export interface UserReportListParams {
  category?: ReportCategory
  status?: ReportStatus
  priority?: ReportPriority
  mine_only?: boolean
}

export interface UserReportCounts {
  total: number
  by_status: {
    pendiente: number
    en_revision: number
    resuelto: number
  }
  by_category: {
    inventario: number
    empleados: number
    sucursales: number
  }
}

// Category display names
export const CATEGORY_LABELS: Record<ReportCategory, string> = {
  inventario: 'Inventario',
  empleados: 'Empleados',
  sucursales: 'Sucursales',
}

// Status display names and colors
export const STATUS_CONFIG: Record<ReportStatus, { label: string; color: string; bgColor: string }> = {
  pendiente: { label: 'Pendiente', color: 'text-yellow-700', bgColor: 'bg-yellow-100' },
  en_revision: { label: 'En revisión', color: 'text-blue-700', bgColor: 'bg-blue-100' },
  resuelto: { label: 'Resuelto', color: 'text-green-700', bgColor: 'bg-green-100' },
}

// Priority display names and colors
export const PRIORITY_CONFIG: Record<ReportPriority, { label: string; color: string; bgColor: string }> = {
  baja: { label: 'Baja', color: 'text-gray-700', bgColor: 'bg-gray-100' },
  media: { label: 'Media', color: 'text-blue-700', bgColor: 'bg-blue-100' },
  alta: { label: 'Alta', color: 'text-orange-700', bgColor: 'bg-orange-100' },
  urgente: { label: 'Urgente', color: 'text-red-700', bgColor: 'bg-red-100' },
}

// User Reports API
export const userReportsApi = {
  // Get all reports (with optional filters)
  getAll: async (params?: UserReportListParams): Promise<UserReportListItem[]> => {
    const response = await apiClient.get('/reports/user-reports/', { params })
    return response.data
  },

  // Get single report by ID
  getById: async (id: number): Promise<UserReport> => {
    const response = await apiClient.get(`/reports/user-reports/${id}/`)
    return response.data
  },

  // Create new report
  create: async (data: CreateUserReportData): Promise<UserReport> => {
    const response = await apiClient.post('/reports/user-reports/', data)
    return response.data
  },

  // Update report
  update: async (id: number, data: UpdateUserReportData): Promise<UserReport> => {
    const response = await apiClient.patch(`/reports/user-reports/${id}/`, data)
    return response.data
  },

  // Delete report
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/reports/user-reports/${id}/`)
  },

  // Set report status to "En revisión" (admin only)
  setInReview: async (id: number): Promise<UserReport> => {
    const response = await apiClient.post(`/reports/user-reports/${id}/set-in-review/`)
    return response.data
  },

  // Resolve report with optional notes (admin only)
  resolve: async (id: number, notes?: string): Promise<UserReport> => {
    const response = await apiClient.post(`/reports/user-reports/${id}/resolve/`, { notes })
    return response.data
  },

  // Get report counts by status and category
  getCounts: async (): Promise<UserReportCounts> => {
    const response = await apiClient.get('/reports/user-reports/counts/')
    return response.data
  },
}
