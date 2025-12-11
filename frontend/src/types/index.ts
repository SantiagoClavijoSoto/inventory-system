// User and Authentication Types
export interface Permission {
  id: number
  code: string
  name: string
  module: string
  action: string
  description?: string
}

export interface Role {
  id: number
  name: string
  role_type: 'admin' | 'supervisor' | 'cashier' | 'warehouse' | 'viewer'
  description?: string
  permissions?: Permission[]
  is_active: boolean
  created_at: string
  updated_at: string
}

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
  employee_count?: number
  created_at: string
  updated_at: string
}

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone?: string
  avatar?: string
  role?: {
    id: number
    name: string
    role_type: string
  }
  permissions: string[]
  default_branch?: number
  allowed_branches?: number[]
  is_active: boolean
  created_at: string
  updated_at: string
  last_login?: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface LoginResponse extends AuthTokens {
  user: User
}

// API Response Types
export interface PaginatedResponse<T> {
  count: number
  total_pages: number
  current_page: number
  page_size: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ApiError {
  detail?: string
  message?: string
  [key: string]: unknown
}

// Product Types
export interface Category {
  id: number
  name: string
  description?: string
  parent?: number | null
  children?: Category[]
  product_count?: number
  full_path?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export type ProductUnit = 'unit' | 'kg' | 'g' | 'l' | 'ml' | 'm' | 'box' | 'pack'

export interface Product {
  id: number
  name: string
  sku: string
  barcode?: string
  description?: string
  category: number
  category_name?: string
  category_path?: string
  cost_price: number
  sale_price: number
  profit_margin?: number
  unit: ProductUnit
  min_stock: number
  max_stock: number
  total_stock?: number
  image?: string
  is_active: boolean
  is_sellable: boolean
  supplier?: number | null
  supplier_name?: string
  branch_stocks?: BranchStock[]
  created_at: string
  updated_at: string
}

export interface BranchStock {
  id: number
  branch: number
  branch_name?: string
  branch_code?: string
  quantity: number
  reserved_quantity: number
  available_quantity?: number
  is_low_stock?: boolean
  is_out_of_stock?: boolean
  updated_at?: string
}

export type MovementType =
  | 'purchase'
  | 'sale'
  | 'transfer_in'
  | 'transfer_out'
  | 'adjustment_in'
  | 'adjustment_out'
  | 'return_customer'
  | 'return_supplier'
  | 'damage'
  | 'initial'

export interface StockMovement {
  id: number
  product: number
  product_name?: string
  product_sku?: string
  branch: number
  branch_name?: string
  movement_type: MovementType
  movement_type_display?: string
  quantity: number
  previous_quantity: number
  new_quantity: number
  reference?: string
  related_branch?: number
  related_branch_name?: string
  notes?: string
  created_by: number
  created_by_name?: string
  created_at: string
}

export interface LowStockItem {
  product_id: number
  product_name: string
  product_sku: string
  branch_id: number
  branch_name: string
  current_quantity: number
  min_stock: number
  is_out_of_stock: boolean
}

// Sale Types
export type PaymentMethod = 'cash' | 'card' | 'transfer' | 'mixed'
export type SaleStatus = 'completed' | 'voided' | 'refunded'

export interface SaleItem {
  id: number
  product: number
  product_name: string
  product_sku: string
  quantity: number
  unit_price: number
  cost_price: number
  discount_amount: number
  subtotal: number
  profit?: number
  profit_margin?: number
}

export interface Sale {
  id: number
  sale_number: string
  branch: number
  branch_name: string
  cashier: number
  cashier_name: string
  subtotal: number
  discount_amount: number
  discount_percent: number
  tax_amount: number
  total: number
  payment_method: PaymentMethod
  payment_method_display: string
  amount_tendered: number
  change_amount: number
  payment_reference?: string
  status: SaleStatus
  status_display: string
  voided_at?: string
  voided_by?: number
  voided_by_name?: string
  void_reason?: string
  customer_name?: string
  customer_phone?: string
  customer_email?: string
  notes?: string
  items: SaleItem[]
  items_count: number
  total_quantity: number
  profit?: number
  is_voided: boolean
  created_at: string
  updated_at: string
}

export interface CreateSaleItem {
  product_id: number
  quantity: number
  discount?: number
  custom_price?: number
}

export interface CreateSaleRequest {
  items: CreateSaleItem[]
  payment_method: PaymentMethod
  amount_tendered?: number
  discount_percent?: number
  discount_amount?: number
  customer_name?: string
  customer_phone?: string
  customer_email?: string
  payment_reference?: string
  notes?: string
  branch_id?: number
}

export interface DailySummary {
  date: string
  branch: string
  total_sales: number
  total_items_sold: number
  sale_count: number
  average_sale: number
  total_discounts: number
  cash_total: number
  card_total: number
  transfer_total: number
  voided_count: number
}

export interface TopProduct {
  product_id: number
  product_name: string
  product_sku: string
  total_quantity: number
  total_revenue: number
  total_profit: number
}

export interface DailyCashRegister {
  id: number
  branch: number
  branch_name: string
  date: string
  opening_amount: number
  opened_by: number
  opened_by_name: string
  opened_at: string
  closing_amount?: number
  closed_by?: number
  closed_by_name?: string
  closed_at?: string
  expected_amount: number
  cash_sales_total: number
  card_sales_total: number
  transfer_sales_total: number
  difference: number
  is_closed: boolean
  notes?: string
  created_at: string
  updated_at: string
}

// Cart Types (for POS frontend)
export interface CartItem {
  product: Product
  quantity: number
  discount: number
  customPrice?: number
}

// Employee Types (for later phases)
export interface Employee {
  id: number
  user: User
  employee_number: string
  branch: Branch
  position: string
  hire_date: string
  is_active: boolean
}

export interface Shift {
  id: number
  employee: Employee
  branch: Branch
  clock_in: string
  clock_out?: string
  notes?: string
}

// Dashboard Types
export interface DashboardSummary {
  sales_today: number
  sales_amount_today: number
  sales_this_month: number
  sales_amount_this_month: number
  total_products: number
  low_stock_alerts: number
  active_employees: number
}

export interface SalesChartData {
  date: string
  sales: number
  amount: number
}

// Utility Types
export type SortDirection = 'asc' | 'desc'

export interface TableColumn<T> {
  key: keyof T | string
  label: string
  sortable?: boolean
  render?: (value: unknown, item: T) => React.ReactNode
}

export interface FilterOption {
  value: string
  label: string
}
