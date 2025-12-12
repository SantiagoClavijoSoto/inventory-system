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
  // Branding fields
  store_name?: string
  display_name?: string
  logo?: string
  logo_url?: string
  favicon?: string
  favicon_url?: string
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  // Business config
  tax_rate?: number
  currency?: string
  currency_symbol?: string
  receipt_header?: string
  receipt_footer?: string
  created_at: string
  updated_at: string
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
  accent_color?: string
  tax_rate: number
  currency: string
  currency_symbol: string
}

// Company and Subscription Types (Multi-tenant)
export type CompanyPlan = 'free' | 'basic' | 'professional' | 'enterprise'
export type SubscriptionStatus = 'trial' | 'active' | 'past_due' | 'cancelled' | 'suspended'
export type BillingCycle = 'monthly' | 'quarterly' | 'annual'

export interface Subscription {
  id: number
  plan: CompanyPlan
  plan_display: string
  status: SubscriptionStatus
  status_display: string
  billing_cycle: BillingCycle
  billing_cycle_display: string
  start_date: string
  next_payment_date?: string
  trial_ends_at?: string
  amount: number
  currency: string
  notes?: string
  is_active: boolean
  days_until_payment?: number
  created_at: string
  updated_at: string
}

export interface Company {
  id: number
  name: string
  slug: string
  legal_name?: string
  tax_id?: string
  // Branding
  logo?: string
  primary_color: string
  secondary_color: string
  // Contact
  email: string
  phone?: string
  website?: string
  address?: string
  // Plan & Limits
  plan: CompanyPlan
  max_branches: number
  max_users: number
  max_products: number
  // Status
  is_active: boolean
  owner?: number
  owner_email?: string
  // Computed
  branch_count?: number
  user_count?: number
  product_count?: number
  plan_limits?: {
    max_branches: number
    max_users: number
    max_products: number
    current_branches: number
    current_users: number
    current_products: number
  }
  // Subscription (from related model)
  subscription?: Subscription
  subscription_status?: SubscriptionStatus
  subscription_status_display?: string
  next_payment_date?: string
  // Timestamps
  created_at: string
  updated_at: string
}

export interface CompanyListItem {
  id: number
  name: string
  slug: string
  email: string
  plan: CompanyPlan
  is_active: boolean
  branch_count: number
  user_count: number
  primary_color: string
  created_at: string
  subscription_status?: SubscriptionStatus
  subscription_status_display?: string
  next_payment_date?: string
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
  is_platform_admin?: boolean
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

// Employee Types
export type EmploymentType = 'full_time' | 'part_time' | 'contract' | 'temporary'
export type EmployeeStatus = 'active' | 'inactive' | 'on_leave' | 'terminated'

export interface EmployeeUser {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone?: string
  avatar?: string
}

export interface EmployeeBranch {
  id: number
  name: string
  code: string
}

export interface Employee {
  id: number
  employee_code: string
  user: EmployeeUser
  branch: EmployeeBranch
  full_name: string
  position: string
  department?: string
  employment_type: EmploymentType
  status: EmployeeStatus
  hire_date: string
  termination_date?: string
  salary?: number
  hourly_rate?: number
  emergency_contact_name?: string
  emergency_contact_phone?: string
  address?: string
  tax_id?: string
  social_security_number?: string
  notes?: string
  years_of_service?: number
  is_clocked_in: boolean
  current_shift?: Shift | null
  created_at: string
  updated_at: string
}

export interface Shift {
  id: number
  employee: number
  employee_name: string
  branch: number
  branch_name: string
  clock_in: string
  clock_out?: string
  break_start?: string
  break_end?: string
  total_hours?: number
  break_hours?: number
  worked_hours?: number
  notes?: string
  is_manual_entry: boolean
  adjusted_by?: number
  is_complete: boolean
  created_at: string
}

export interface CreateEmployeeRequest {
  email: string
  first_name: string
  last_name: string
  phone?: string
  password: string
  role_id?: number
  branch_id: number
  position: string
  department?: string
  employment_type?: EmploymentType
  hire_date: string
  salary?: number
  hourly_rate?: number
  emergency_contact_name?: string
  emergency_contact_phone?: string
  address?: string
  tax_id?: string
  social_security_number?: string
  notes?: string
}

export interface UpdateEmployeeRequest {
  first_name?: string
  last_name?: string
  phone?: string
  branch?: number
  position?: string
  department?: string
  employment_type?: EmploymentType
  status?: EmployeeStatus
  termination_date?: string
  salary?: number
  hourly_rate?: number
  emergency_contact_name?: string
  emergency_contact_phone?: string
  address?: string
  tax_id?: string
  social_security_number?: string
  notes?: string
}

export interface EmployeeStats {
  total_shifts: number
  total_hours: number
  total_sales: number
  total_revenue: number
  average_sale: number
  period_start: string
  period_end: string
}

export interface ShiftSummary {
  date: string
  total_employees: number
  total_hours: number
  shifts_count: number
}

// Supplier Types
export interface Supplier {
  id: number
  name: string
  code: string
  contact_name?: string
  email?: string
  phone?: string
  mobile?: string
  address?: string
  city?: string
  state?: string
  postal_code?: string
  country: string
  tax_id?: string
  website?: string
  notes?: string
  payment_terms: number
  credit_limit: number
  is_active: boolean
  full_address?: string
  purchase_orders_count?: number
  total_purchases?: number
  created_at: string
  updated_at: string
}

export type PurchaseOrderStatus = 'draft' | 'pending' | 'approved' | 'ordered' | 'partial' | 'received' | 'cancelled'

export interface PurchaseOrderItem {
  id: number
  product: {
    id: number
    name: string
    sku: string
    barcode?: string
  }
  product_id?: number
  quantity_ordered: number
  quantity_received: number
  unit_price: number
  subtotal: number
  is_fully_received: boolean
  pending_quantity: number
}

export interface PurchaseOrder {
  id: number
  order_number: string
  supplier: number | Supplier
  supplier_name?: string
  branch: number | EmployeeBranch
  branch_name?: string
  status: PurchaseOrderStatus
  order_date?: string
  expected_date?: string
  received_date?: string
  subtotal: number
  tax: number
  total: number
  notes?: string
  created_by?: number
  created_by_name?: string
  approved_by?: number
  approved_by_name?: string
  received_by?: number
  received_by_name?: string
  items?: PurchaseOrderItem[]
  items_count?: number
  created_at: string
  updated_at: string
}

export interface CreateSupplierRequest {
  name: string
  code: string
  contact_name?: string
  email?: string
  phone?: string
  mobile?: string
  address?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  tax_id?: string
  website?: string
  notes?: string
  payment_terms?: number
  credit_limit?: number
  is_active?: boolean
}

export interface SupplierStats {
  total_orders: number
  total_amount: number
  pending_orders: number
  ordered_count: number
  partial_count: number
  received_orders: number
  cancelled_orders: number
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
