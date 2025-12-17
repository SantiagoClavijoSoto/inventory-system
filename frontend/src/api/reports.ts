import { apiClient } from './client'

// Types for report parameters
export interface DateRangeParams {
  date_from: string
  date_to: string
  branch_id?: number
}

export interface SalesPeriodParams extends DateRangeParams {
  group_by: 'day' | 'week' | 'month'
}

export interface TopProductsParams {
  days?: number
  limit?: number
  branch_id?: number
}

export interface HourlySalesParams {
  target_date?: string
  branch_id?: number
}

export interface LowStockParams {
  branch_id?: number
  limit?: number
}

export interface ProductMovementParams {
  product_id: number
  branch_id?: number
  days?: number
}

// Response types
export interface TodaySummary {
  total_sales: number
  total_transactions: number
  average_ticket: number
  total_profit: number
  cash_total: number
  card_total: number
  transfer_total: number
  items_sold: number
}

export interface PeriodComparison {
  current_period: {
    sales: number
    transactions: number
    average_ticket: number
  }
  previous_period: {
    sales: number
    transactions: number
    average_ticket: number
  }
  changes: {
    sales_change: number
    transactions_change: number
    ticket_change: number
  }
}

export interface TopProduct {
  product_id: number
  product_name: string
  product_sku: string
  total_quantity: number
  total_revenue: number
  total_profit: number
}

export interface LowStockCount {
  low_stock_count: number
  out_of_stock_count: number
  total_alerts: number
}

export interface SalesByPeriod {
  period: string
  total_sales: number
  transaction_count: number
  items_sold: number
  average_ticket: number
  profit: number
}

export interface SalesByPaymentMethod {
  payment_method: string
  payment_method_display: string
  total_amount: number
  transaction_count: number
  percentage: number
}

export interface SalesByCashier {
  cashier_id: number
  cashier_name: string
  total_sales: number
  transaction_count: number
  average_ticket: number
  total_profit: number
}

export interface SalesByCategory {
  category_id: number
  category_name: string
  total_quantity: number
  total_revenue: number
  total_profit: number
  percentage: number
}

export interface HourlySales {
  hour: number
  total_sales: number
  transaction_count: number
}

export interface StockSummary {
  total_products: number
  total_stock_value: number
  total_retail_value: number
  potential_profit: number
  low_stock_count: number
  out_of_stock_count: number
  categories_count: number
}

export interface StockByCategory {
  category_id: number
  category_name: string
  product_count: number
  total_quantity: number
  stock_value: number
  retail_value: number
}

export interface LowStockProduct {
  product_id: number
  product_name: string
  product_sku: string
  branch_id: number
  branch_name: string
  current_quantity: number
  min_stock: number
  is_out_of_stock: boolean
}

export interface MovementsSummary {
  date: string
  date_display: string
  transaction_count: number
  total_amount: number
  items_sold: number
}

export interface SaleDetail {
  id: number
  sale_number: string
  time: string
  total: number
  items_count: number
  payment_method: string
  cashier_name: string
}

export interface SaleListItem {
  id: number
  sale_number: string
  date: string
  date_display: string
  time: string
  total: number
  items_count: number
  payment_method: string
  cashier_name: string
  branch_name: string
}

export interface ProductMovement {
  id: number
  date: string
  movement_type: string
  movement_type_display: string
  quantity: number
  previous_quantity: number
  new_quantity: number
  reference?: string
  notes?: string
  created_by_name: string
}

export interface EmployeePerformance {
  employee_id: number
  employee_name: string
  employee_code: string
  branch_name: string
  total_sales: number
  transaction_count: number
  average_ticket: number
  total_profit: number
  hours_worked: number
  sales_per_hour: number
}

export interface ShiftSummary {
  total_shifts: number
  total_hours: number
  average_shift_length: number
  employees_count: number
  by_weekday: {
    weekday: number
    weekday_name: string
    shift_count: number
    total_hours: number
  }[]
}

export interface BranchComparison {
  branch_id: number
  branch_name: string
  total_sales: number
  transaction_count: number
  average_ticket: number
  total_profit: number
  profit_margin: number
  items_sold: number
}

// Dashboard API
export const dashboardApi = {
  getTodaySummary: async (branchId?: number): Promise<TodaySummary> => {
    const response = await apiClient.get('/reports/dashboard/today/', {
      params: branchId ? { branch_id: branchId } : undefined,
    })
    return response.data
  },

  getPeriodComparison: async (days: number = 7, branchId?: number): Promise<PeriodComparison> => {
    const response = await apiClient.get('/reports/dashboard/comparison/', {
      params: { days, branch_id: branchId },
    })
    return response.data
  },

  getLowStockCount: async (branchId?: number): Promise<LowStockCount> => {
    const response = await apiClient.get('/reports/dashboard/low-stock-count/', {
      params: branchId ? { branch_id: branchId } : undefined,
    })
    return response.data
  },

  getTopProducts: async (params?: TopProductsParams): Promise<TopProduct[]> => {
    const response = await apiClient.get('/reports/dashboard/top-products/', { params })
    return response.data
  },
}

// Sales Reports API
export const salesReportsApi = {
  getByPeriod: async (params: SalesPeriodParams): Promise<SalesByPeriod[]> => {
    const response = await apiClient.get('/reports/sales/by-period/', { params })
    return response.data
  },

  getByPaymentMethod: async (params: DateRangeParams): Promise<SalesByPaymentMethod[]> => {
    const response = await apiClient.get('/reports/sales/by-payment-method/', { params })
    return response.data
  },

  getByCashier: async (params: DateRangeParams): Promise<SalesByCashier[]> => {
    const response = await apiClient.get('/reports/sales/by-cashier/', { params })
    return response.data
  },

  getByCategory: async (params: DateRangeParams): Promise<SalesByCategory[]> => {
    const response = await apiClient.get('/reports/sales/by-category/', { params })
    return response.data
  },

  getHourly: async (params?: HourlySalesParams): Promise<HourlySales[]> => {
    const response = await apiClient.get('/reports/sales/hourly/', { params })
    return response.data
  },

  getTopProducts: async (params: DateRangeParams & { limit?: number }): Promise<TopProduct[]> => {
    const response = await apiClient.get('/reports/sales/top-products/', { params })
    return response.data
  },
}

// Inventory Reports API
export const inventoryReportsApi = {
  getSummary: async (branchId?: number): Promise<StockSummary> => {
    const response = await apiClient.get('/reports/inventory/summary/', {
      params: branchId ? { branch_id: branchId } : undefined,
    })
    return response.data
  },

  getByCategory: async (branchId?: number): Promise<StockByCategory[]> => {
    const response = await apiClient.get('/reports/inventory/by-category/', {
      params: branchId ? { branch_id: branchId } : undefined,
    })
    return response.data
  },

  getLowStock: async (params?: LowStockParams): Promise<LowStockProduct[]> => {
    const response = await apiClient.get('/reports/inventory/low-stock/', { params })
    return response.data
  },

  getMovementsSummary: async (params: DateRangeParams): Promise<MovementsSummary[]> => {
    const response = await apiClient.get('/reports/inventory/movements-summary/', { params })
    return response.data
  },

  getProductHistory: async (params: ProductMovementParams): Promise<ProductMovement[]> => {
    const response = await apiClient.get('/reports/inventory/product-history/', { params })
    return response.data
  },

  getSalesByDate: async (params: { target_date: string; branch_id?: number }): Promise<SaleDetail[]> => {
    const response = await apiClient.get('/reports/inventory/sales-by-date/', { params })
    return response.data
  },

  getAllSales: async (params: DateRangeParams): Promise<SaleListItem[]> => {
    const response = await apiClient.get('/reports/inventory/all-sales/', { params })
    return response.data
  },
}

// Employee Reports API
export const employeeReportsApi = {
  getPerformance: async (params: DateRangeParams): Promise<EmployeePerformance[]> => {
    const response = await apiClient.get('/reports/employees/performance/', { params })
    return response.data
  },

  getShiftSummary: async (params: DateRangeParams): Promise<ShiftSummary> => {
    const response = await apiClient.get('/reports/employees/shifts/', { params })
    return response.data
  },
}

// Branch Reports API
export const branchReportsApi = {
  getComparison: async (params: Omit<DateRangeParams, 'branch_id'>): Promise<BranchComparison[]> => {
    const response = await apiClient.get('/reports/branches/comparison/', { params })
    return response.data
  },
}
