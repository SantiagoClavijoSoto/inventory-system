import { apiClient } from './client'

// Types
export interface Permission {
  id: number
  code: string
  name: string
  module: string
  action: string
  description: string
}

export interface Role {
  id: number
  name: string
  description: string
  role_type: 'admin' | 'supervisor' | 'employee' | 'cashier' | 'warehouse' | 'viewer'
  company: number | null  // null = global system role, number = company-specific role
  permissions: Permission[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  role: Role | null
  role_name: string
  default_branch: number | null
  default_branch_name: string
  allowed_branches: number[]
  // Company info (for SuperAdmin view)
  company_id: number | null
  company_name: string | null
  is_company_admin: boolean
  // Permission flags
  can_create_roles: boolean
  created_at: string
  updated_at: string
}

export interface UserListParams {
  search?: string
  is_active?: boolean
  role?: number
  default_branch?: number
  page?: number
  page_size?: number
}

export type EmploymentType = 'full_time' | 'part_time' | 'contract' | 'temporary'

export interface CreateUserRequest {
  email: string
  password: string
  password_confirm: string
  first_name: string
  last_name: string
  role_id?: number
  default_branch?: number
  allowed_branches?: number[]
  is_active?: boolean
  company_id?: number  // For SuperAdmin to assign company
  // Employee fields (optional)
  is_employee?: boolean
  employee_position?: string
  employee_branch_id?: number
  employment_type?: EmploymentType
  hire_date?: string  // YYYY-MM-DD format
}

export interface UpdateUserRequest {
  email?: string
  first_name?: string
  last_name?: string
  role_id?: number | null
  default_branch?: number
  allowed_branches?: number[]
  is_active?: boolean
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// Auth/Profile API
export const authApi = {
  // Get current user profile
  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me/')
    return response.data
  },

  // Update current user profile
  updateMe: async (data: UpdateUserRequest): Promise<User> => {
    const response = await apiClient.patch('/auth/me/', data)
    return response.data
  },

  // Change password
  changePassword: async (data: ChangePasswordRequest): Promise<{ message: string }> => {
    const response = await apiClient.post('/auth/change-password/', data)
    return response.data
  },
}

// Users API (Admin)
export const usersApi = {
  // Get all users
  getAll: async (params?: UserListParams): Promise<PaginatedResponse<User>> => {
    const response = await apiClient.get('/auth/users/', { params })
    return response.data
  },

  // Get single user
  getById: async (id: number): Promise<User> => {
    const response = await apiClient.get(`/auth/users/${id}/`)
    return response.data
  },

  // Create user
  create: async (data: CreateUserRequest): Promise<User> => {
    const response = await apiClient.post('/auth/users/', data)
    return response.data
  },

  // Update user
  update: async (id: number, data: UpdateUserRequest): Promise<User> => {
    const response = await apiClient.patch(`/auth/users/${id}/`, data)
    return response.data
  },

  // Delete user
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/auth/users/${id}/`)
  },

  // Activate user
  activate: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.post(`/auth/users/${id}/activate/`)
    return response.data
  },

  // Deactivate user
  deactivate: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.post(`/auth/users/${id}/deactivate/`)
    return response.data
  },

  // Reset password
  resetPassword: async (id: number, newPassword: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`/auth/users/${id}/reset_password/`, {
      new_password: newPassword,
    })
    return response.data
  },
}

// Roles API
export const rolesApi = {
  // Get all roles
  getAll: async (): Promise<Role[]> => {
    const response = await apiClient.get('/auth/roles/')
    // Handle both paginated and non-paginated responses
    const data = response.data
    return Array.isArray(data) ? data : (data.results || [])
  },

  // Get single role
  getById: async (id: number): Promise<Role> => {
    const response = await apiClient.get(`/auth/roles/${id}/`)
    return response.data
  },

  // Create role
  create: async (data: Partial<Role>): Promise<Role> => {
    const response = await apiClient.post('/auth/roles/', data)
    return response.data
  },

  // Update role
  update: async (id: number, data: Partial<Role>): Promise<Role> => {
    const response = await apiClient.patch(`/auth/roles/${id}/`, data)
    return response.data
  },

  // Delete role
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/auth/roles/${id}/`)
  },
}

// Permissions API
export const permissionsApi = {
  // Get all permissions
  getAll: async (): Promise<Permission[]> => {
    const response = await apiClient.get('/auth/permissions/')
    // Handle both paginated and non-paginated responses
    const data = response.data
    return Array.isArray(data) ? data : (data.results || [])
  },
}
