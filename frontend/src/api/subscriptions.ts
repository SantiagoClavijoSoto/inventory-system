import { apiClient } from './client'
import type {
  Subscription,
  SubscriptionListItem,
  SubscriptionStats,
  SubscriptionStatus,
  CompanyPlan,
  BillingCycle,
  PaginatedResponse,
} from '@/types'

// Request types
export interface SubscriptionListParams {
  search?: string
  plan?: CompanyPlan
  status?: SubscriptionStatus
  billing_cycle?: BillingCycle
  page?: number
  page_size?: number
  ordering?: string
}

export interface UpdateSubscriptionRequest {
  plan?: CompanyPlan
  status?: SubscriptionStatus
  billing_cycle?: BillingCycle
  next_payment_date?: string
  amount?: number
  currency?: string
  notes?: string
}

// Platform Usage Stats (SuperAdmin dashboard) - SaaS Revenue Metrics
export interface PlatformUsageStats {
  // Revenue metrics
  mrr: {
    total: number
    currency: string
  }
  expected_revenue: {
    this_month: number
    currency: string
  }
  upcoming_payments: {
    count: number
    amount: number
    days: number
  }
  overdue_payments: {
    count: number
    amount: number
  }
  new_subscriptions: {
    count: number
    revenue: number
    last_month_count: number
    change_percent: number
  }
  // Distribution
  revenue_by_plan: Array<{
    plan: string
    count: number
    revenue: number
  }>
  top_subscribers: Array<{
    id: number
    name: string
    plan: string
    amount: number
    billing_cycle: string
  }>
  // Platform health
  total_companies: number
  total_users: number
  status_distribution: Array<{
    status: string
    count: number
  }>
  trials_ending_soon: number
  active_subscriptions: number
  total_subscriptions: number
}

// Subscriptions API (SuperAdmin only)
export const subscriptionsApi = {
  // Get all subscriptions (paginated)
  getAll: async (params?: SubscriptionListParams): Promise<PaginatedResponse<SubscriptionListItem>> => {
    const response = await apiClient.get('/subscriptions/', { params })
    return response.data
  },

  // Get subscription stats for dashboard
  getStats: async (): Promise<SubscriptionStats> => {
    const response = await apiClient.get('/subscriptions/stats/')
    return response.data
  },

  // Get single subscription
  getById: async (id: number): Promise<Subscription> => {
    const response = await apiClient.get(`/subscriptions/${id}/`)
    return response.data
  },

  // Update subscription
  update: async (id: number, data: UpdateSubscriptionRequest): Promise<Subscription> => {
    const response = await apiClient.patch(`/subscriptions/${id}/`, data)
    return response.data
  },

  // Get platform usage stats for SuperAdmin dashboard
  getPlatformUsage: async (): Promise<PlatformUsageStats> => {
    const response = await apiClient.get('/subscriptions/platform_usage/')
    return response.data
  },
}
