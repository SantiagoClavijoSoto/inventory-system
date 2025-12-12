import { apiClient } from './client'
import type {
  Employee,
  Shift,
  CreateEmployeeRequest,
  UpdateEmployeeRequest,
  EmployeeStats,
  ShiftSummary,
  PaginatedResponse,
} from '@/types'

export interface EmployeeListParams {
  search?: string
  branch?: number
  status?: string
  employment_type?: string
  page?: number
  page_size?: number
}

export interface ShiftListParams {
  branch?: number
  employee?: number
  date_from?: string
  date_to?: string
  is_complete?: boolean
  page?: number
  page_size?: number
}

export const employeesApi = {
  // Employee CRUD
  getAll: async (params?: EmployeeListParams): Promise<PaginatedResponse<Employee>> => {
    const response = await apiClient.get('/employees/', { params })
    return response.data
  },

  getById: async (id: number): Promise<Employee> => {
    const response = await apiClient.get(`/employees/${id}/`)
    return response.data
  },

  create: async (data: CreateEmployeeRequest): Promise<Employee> => {
    const response = await apiClient.post('/employees/', data)
    return response.data
  },

  update: async (id: number, data: UpdateEmployeeRequest): Promise<Employee> => {
    const response = await apiClient.patch(`/employees/${id}/`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/employees/${id}/`)
  },

  // Employee actions
  terminate: async (id: number, data: { termination_date?: string; reason?: string }): Promise<Employee> => {
    const response = await apiClient.post(`/employees/${id}/terminate/`, data)
    return response.data
  },

  getStats: async (id: number, params?: { date_from?: string; date_to?: string }): Promise<EmployeeStats> => {
    const response = await apiClient.get(`/employees/${id}/stats/`, { params })
    return response.data
  },

  getShifts: async (id: number, params?: { date_from?: string; date_to?: string }): Promise<Shift[]> => {
    const response = await apiClient.get(`/employees/${id}/shifts/`, { params })
    return response.data
  },

  getSales: async (id: number, params?: { date_from?: string; date_to?: string }) => {
    const response = await apiClient.get(`/employees/${id}/sales/`, { params })
    return response.data
  },
}

export const shiftsApi = {
  // Shift CRUD
  getAll: async (params?: ShiftListParams): Promise<PaginatedResponse<Shift>> => {
    const response = await apiClient.get('/shifts/', { params })
    return response.data
  },

  getById: async (id: number): Promise<Shift> => {
    const response = await apiClient.get(`/shifts/${id}/`)
    return response.data
  },

  create: async (data: Partial<Shift>): Promise<Shift> => {
    const response = await apiClient.post('/shifts/', data)
    return response.data
  },

  // Clock actions for current user
  clockIn: async (branchId?: number): Promise<Shift> => {
    const response = await apiClient.post('/shifts/clock_in/', { branch_id: branchId })
    return response.data
  },

  clockOut: async (notes?: string): Promise<Shift> => {
    const response = await apiClient.post('/shifts/clock_out/', { notes })
    return response.data
  },

  startBreak: async (): Promise<Shift> => {
    const response = await apiClient.post('/shifts/start_break/')
    return response.data
  },

  endBreak: async (): Promise<Shift> => {
    const response = await apiClient.post('/shifts/end_break/')
    return response.data
  },

  // Get current shift
  getCurrent: async (): Promise<Shift | null> => {
    try {
      const response = await apiClient.get('/shifts/current/')
      return response.data
    } catch {
      return null
    }
  },

  // Daily summary
  getDailySummary: async (branchId: number, date?: string): Promise<ShiftSummary> => {
    const response = await apiClient.get('/shifts/daily_summary/', {
      params: { branch: branchId, date },
    })
    return response.data
  },
}
