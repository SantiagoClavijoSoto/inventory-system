import { apiClient } from './client'

// Types
export type AlertType =
  // Company-level alerts
  | 'low_stock'
  | 'out_of_stock'
  | 'overstock'
  | 'cash_difference'
  | 'high_void_rate'
  | 'sales_anomaly'
  | 'shift_overtime'
  | 'system'
  // Platform-level alerts (for SuperAdmin) - Subscription related
  | 'subscription_payment_due'
  | 'subscription_overdue'
  | 'subscription_trial_ending'
  | 'subscription_cancelled'
  | 'subscription_suspended'
  | 'new_subscription'
  | 'subscription_plan_changed'
  // Platform-level alerts (for SuperAdmin) - Business health
  | 'high_churn_rate'
  | 'revenue_anomaly'
  | 'low_platform_activity'
  // Platform-level alerts (for SuperAdmin) - Tenant health
  | 'tenant_limit_approaching'
  | 'tenant_inactive'
  | 'onboarding_stalled'
  // Platform-level alerts (for SuperAdmin) - System health
  | 'high_error_rate'
  | 'system_performance'

// Platform alert types (for filtering in UI)
export const PLATFORM_ALERT_TYPES: AlertType[] = [
  // Subscription related
  'subscription_payment_due',
  'subscription_overdue',
  'subscription_trial_ending',
  'subscription_cancelled',
  'subscription_suspended',
  'new_subscription',
  'subscription_plan_changed',
  // Business health
  'high_churn_rate',
  'revenue_anomaly',
  'low_platform_activity',
  // Tenant health
  'tenant_limit_approaching',
  'tenant_inactive',
  'onboarding_stalled',
  // System health
  'high_error_rate',
  'system_performance',
]

// Company alert types (for filtering in UI)
export const COMPANY_ALERT_TYPES: AlertType[] = [
  'low_stock',
  'out_of_stock',
  'overstock',
  'cash_difference',
  'high_void_rate',
  'sales_anomaly',
  'shift_overtime',
  'system',
]

export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical'
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'dismissed'

export interface Alert {
  id: number
  alert_type: AlertType
  alert_type_display: string
  severity: AlertSeverity
  severity_display: string
  title: string
  message: string
  branch?: number
  branch_name?: string
  product?: number
  product_name?: string
  product_sku?: string
  employee?: number
  employee_name?: string
  // Subscription info (for platform alerts)
  subscription?: number
  subscription_company_name?: string
  subscription_plan?: string
  subscription_status?: string
  status: AlertStatus
  status_display: string
  is_read: boolean
  read_at?: string
  read_by?: number
  read_by_name?: string
  resolved_at?: string
  resolved_by?: number
  resolved_by_name?: string
  resolution_notes?: string
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface AlertListParams {
  branch_id?: number
  alert_type?: AlertType
  status?: AlertStatus
  severity?: AlertSeverity
  is_read?: boolean
  limit?: number
}

export interface AlertUnreadCount {
  total: number
  by_severity: {
    low: number
    medium: number
    high: number
    critical: number
  }
}

export interface AlertConfiguration {
  id: number
  scope: 'global' | 'branch' | 'category'
  branch?: number
  branch_name?: string
  category?: number
  category_name?: string
  low_stock_threshold: number
  overstock_threshold: number
  cash_difference_threshold: number
  void_rate_threshold: number
  overtime_threshold: number
  email_notifications: boolean
  dashboard_notifications: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserAlertPreference {
  id: number
  receive_low_stock: boolean
  receive_out_of_stock: boolean
  receive_cash_difference: boolean
  receive_void_alerts: boolean
  receive_shift_alerts: boolean
  receive_system_alerts: boolean
  // Platform-level alerts (SuperAdmin)
  receive_subscription_alerts: boolean
  minimum_severity: AlertSeverity
  email_digest: boolean
}

// Alert API
export const alertsApi = {
  // Get all alerts
  getAll: async (params?: AlertListParams): Promise<Alert[]> => {
    const response = await apiClient.get('/alerts/', { params })
    return response.data
  },

  // Get single alert
  getById: async (id: number): Promise<Alert> => {
    const response = await apiClient.get(`/alerts/${id}/`)
    return response.data
  },

  // Get unread count
  getUnreadCount: async (branchId?: number): Promise<AlertUnreadCount> => {
    const response = await apiClient.get('/alerts/unread-count/', {
      params: branchId ? { branch_id: branchId } : undefined,
    })
    return response.data
  },

  // Mark as read
  markAsRead: async (id: number): Promise<Alert> => {
    const response = await apiClient.post(`/alerts/${id}/read/`)
    return response.data
  },

  // Mark all as read
  markAllAsRead: async (branchId?: number): Promise<{ count: number }> => {
    const response = await apiClient.post('/alerts/read-all/', null, {
      params: branchId ? { branch_id: branchId } : undefined,
    })
    return response.data
  },

  // Acknowledge alert
  acknowledge: async (id: number): Promise<Alert> => {
    const response = await apiClient.post(`/alerts/${id}/acknowledge/`)
    return response.data
  },

  // Resolve alert
  resolve: async (id: number, notes?: string): Promise<Alert> => {
    const response = await apiClient.post(`/alerts/${id}/resolve/`, { notes })
    return response.data
  },

  // Dismiss alert
  dismiss: async (id: number): Promise<Alert> => {
    const response = await apiClient.post(`/alerts/${id}/dismiss/`)
    return response.data
  },

  // Bulk resolve
  bulkResolve: async (alertIds: number[], notes?: string): Promise<{ count: number }> => {
    const response = await apiClient.post('/alerts/bulk-resolve/', {
      alert_ids: alertIds,
      notes,
    })
    return response.data
  },

  // Generate alerts (admin)
  generate: async (): Promise<{ alerts_created: number }> => {
    const response = await apiClient.post('/alerts/generate/')
    return response.data
  },
}

// Alert Configuration API
export const alertConfigApi = {
  // Get all configurations
  getAll: async (): Promise<AlertConfiguration[]> => {
    const response = await apiClient.get('/alerts/configurations/')
    return response.data
  },

  // Get global configuration
  getGlobal: async (): Promise<AlertConfiguration> => {
    const response = await apiClient.get('/alerts/configurations/global/')
    return response.data
  },

  // Get branch configuration
  getBranch: async (branchId: number): Promise<AlertConfiguration> => {
    const response = await apiClient.get('/alerts/configurations/branch/', {
      params: { branch_id: branchId },
    })
    return response.data
  },

  // Create configuration
  create: async (data: Partial<AlertConfiguration>): Promise<AlertConfiguration> => {
    const response = await apiClient.post('/alerts/configurations/', data)
    return response.data
  },

  // Update configuration
  update: async (id: number, data: Partial<AlertConfiguration>): Promise<AlertConfiguration> => {
    const response = await apiClient.patch(`/alerts/configurations/${id}/`, data)
    return response.data
  },

  // Delete configuration
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/alerts/configurations/${id}/`)
  },
}

// User Preferences API
export const alertPreferencesApi = {
  // Get current user's preferences
  get: async (): Promise<UserAlertPreference> => {
    const response = await apiClient.get('/alerts/preferences/')
    return response.data
  },

  // Update preferences
  update: async (data: Partial<UserAlertPreference>): Promise<UserAlertPreference> => {
    const response = await apiClient.put('/alerts/preferences/me/', data)
    return response.data
  },
}

// Activity Log Types
export type ActivityModule =
  | 'inventory'
  | 'sales'
  | 'employees'
  | 'branches'
  | 'users'
  | 'suppliers'

export type ActivityAction =
  | 'product_created'
  | 'product_updated'
  | 'product_deleted'
  | 'stock_adjusted'
  | 'stock_transferred'
  | 'sale_created'
  | 'sale_voided'
  | 'cash_register_opened'
  | 'cash_register_closed'
  | 'employee_created'
  | 'employee_updated'
  | 'shift_started'
  | 'shift_ended'
  | 'branch_created'
  | 'branch_updated'
  | 'user_created'
  | 'user_updated'
  | 'role_changed'
  | 'supplier_created'
  | 'supplier_updated'
  | 'purchase_order_created'

export interface ActivityLog {
  id: number
  action: ActivityAction
  action_display: string
  module: ActivityModule
  module_display: string
  user?: number
  user_name: string
  branch?: number
  branch_name?: string
  description: string
  target_type: string
  target_id?: number
  target_name: string
  metadata: Record<string, unknown>
  is_read: boolean
  read_by?: number
  read_by_name?: string
  read_at?: string
  created_at: string
}

export interface ActivityLogListParams {
  module?: ActivityModule
  action?: ActivityAction
  user_id?: number
  is_read?: boolean
  limit?: number
  offset?: number
}

// Activity Log API
export const activityLogApi = {
  // Get all activity logs
  getAll: async (params?: ActivityLogListParams): Promise<ActivityLog[]> => {
    const response = await apiClient.get('/alerts/activities/', { params })
    return response.data
  },

  // Get single activity log
  getById: async (id: number): Promise<ActivityLog> => {
    const response = await apiClient.get(`/alerts/activities/${id}/`)
    return response.data
  },

  // Get unread count
  getUnreadCount: async (): Promise<{ count: number }> => {
    const response = await apiClient.get('/alerts/activities/unread-count/')
    return response.data
  },

  // Mark as read
  markAsRead: async (id: number): Promise<ActivityLog> => {
    const response = await apiClient.post(`/alerts/activities/${id}/read/`)
    return response.data
  },

  // Mark all as read
  markAllAsRead: async (): Promise<{ count: number }> => {
    const response = await apiClient.post('/alerts/activities/read-all/')
    return response.data
  },
}
