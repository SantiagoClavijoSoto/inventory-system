import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  dashboardApi,
  salesReportsApi,
  inventoryReportsApi,
  employeeReportsApi,
  branchReportsApi,
  type DateRangeParams,
  type SalesPeriodParams,
} from '@/api/reports'
import { useAuthStore } from '@/store/authStore'
import { Badge } from '@/components/ui/Badge'
import { formatCurrency } from '@/utils/formatters'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Package,
  Users,
  Building2,
  Calendar,
  DollarSign,
  ShoppingCart,
  AlertTriangle,
  Clock,
} from 'lucide-react'

type ReportTab = 'sales' | 'inventory' | 'employees' | 'branches'

// Helper to format dates for API
const formatDate = (date: Date): string => {
  return date.toISOString().split('T')[0]
}

// Helper to get date range presets
const getDateRange = (preset: string): { date_from: string; date_to: string } => {
  const today = new Date()
  const date_to = formatDate(today)

  switch (preset) {
    case 'today':
      return { date_from: date_to, date_to }
    case 'week': {
      const weekAgo = new Date(today)
      weekAgo.setDate(weekAgo.getDate() - 7)
      return { date_from: formatDate(weekAgo), date_to }
    }
    case 'month': {
      const monthAgo = new Date(today)
      monthAgo.setMonth(monthAgo.getMonth() - 1)
      return { date_from: formatDate(monthAgo), date_to }
    }
    case 'quarter': {
      const quarterAgo = new Date(today)
      quarterAgo.setMonth(quarterAgo.getMonth() - 3)
      return { date_from: formatDate(quarterAgo), date_to }
    }
    case 'year': {
      const yearAgo = new Date(today)
      yearAgo.setFullYear(yearAgo.getFullYear() - 1)
      return { date_from: formatDate(yearAgo), date_to }
    }
    default:
      return { date_from: formatDate(new Date(today.setDate(today.getDate() - 30))), date_to }
  }
}

export function Reports() {
  const { currentBranch } = useAuthStore()
  const [activeTab, setActiveTab] = useState<ReportTab>('sales')
  const [datePreset, setDatePreset] = useState('month')

  const branchId = currentBranch?.id
  const dateRange = useMemo(() => getDateRange(datePreset), [datePreset])

  const tabs = [
    { id: 'sales' as const, label: 'Ventas', icon: ShoppingCart },
    { id: 'inventory' as const, label: 'Inventario', icon: Package },
    { id: 'employees' as const, label: 'Empleados', icon: Users },
    { id: 'branches' as const, label: 'Sucursales', icon: Building2 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Reportes</h1>
          <p className="text-secondary-500 mt-1">
            Analiza el rendimiento de tu negocio
          </p>
        </div>

        {/* Date Preset Selector */}
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-secondary-400" />
          <select
            className="px-3 py-2 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={datePreset}
            onChange={(e) => setDatePreset(e.target.value)}
          >
            <option value="today">Hoy</option>
            <option value="week">Última semana</option>
            <option value="month">Último mes</option>
            <option value="quarter">Último trimestre</option>
            <option value="year">Último año</option>
          </select>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200">
        <div className="border-b border-secondary-200">
          <nav className="flex -mb-px">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'sales' && <SalesReport dateRange={dateRange} branchId={branchId} />}
          {activeTab === 'inventory' && <InventoryReport branchId={branchId} dateRange={dateRange} />}
          {activeTab === 'employees' && <EmployeesReport dateRange={dateRange} branchId={branchId} />}
          {activeTab === 'branches' && <BranchesReport dateRange={dateRange} />}
        </div>
      </div>
    </div>
  )
}

// Sales Report Component
function SalesReport({ dateRange, branchId }: { dateRange: DateRangeParams; branchId?: number }) {
  const params: SalesPeriodParams = { ...dateRange, branch_id: branchId, group_by: 'day' }

  const { data: todaySummary } = useQuery({
    queryKey: ['today-summary', branchId],
    queryFn: () => dashboardApi.getTodaySummary(branchId),
  })

  const { data: comparison } = useQuery({
    queryKey: ['period-comparison', branchId],
    queryFn: () => dashboardApi.getPeriodComparison(7, branchId),
  })

  const { data: salesByPeriod, isLoading: isLoadingPeriod } = useQuery({
    queryKey: ['sales-by-period', params],
    queryFn: () => salesReportsApi.getByPeriod(params),
  })

  const { data: salesByPayment } = useQuery({
    queryKey: ['sales-by-payment', dateRange, branchId],
    queryFn: () => salesReportsApi.getByPaymentMethod({ ...dateRange, branch_id: branchId }),
  })

  const { data: salesByCategory } = useQuery({
    queryKey: ['sales-by-category', dateRange, branchId],
    queryFn: () => salesReportsApi.getByCategory({ ...dateRange, branch_id: branchId }),
  })

  const { data: topProducts } = useQuery({
    queryKey: ['top-products', dateRange, branchId],
    queryFn: () => salesReportsApi.getTopProducts({ ...dateRange, limit: 10, branch_id: branchId }),
  })

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Ventas Hoy"
          value={formatCurrency(todaySummary?.total_sales || 0)}
          change={comparison?.changes?.sales_change}
          icon={DollarSign}
          iconBg="bg-success-100"
          iconColor="text-success-600"
        />
        <MetricCard
          title="Transacciones"
          value={todaySummary?.total_transactions?.toString() || '0'}
          change={comparison?.changes?.transactions_change}
          icon={ShoppingCart}
          iconBg="bg-primary-100"
          iconColor="text-primary-600"
        />
        <MetricCard
          title="Ticket Promedio"
          value={formatCurrency(todaySummary?.average_ticket || 0)}
          change={comparison?.changes?.ticket_change}
          icon={BarChart3}
          iconBg="bg-warning-100"
          iconColor="text-warning-600"
        />
        <MetricCard
          title="Artículos Vendidos"
          value={todaySummary?.items_sold?.toString() || '0'}
          icon={Package}
          iconBg="bg-info-100"
          iconColor="text-info-600"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales by Period */}
        <div className="bg-secondary-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-secondary-900 mb-4">Ventas por Período</h3>
          {isLoadingPeriod ? (
            <div className="h-64 flex items-center justify-center text-secondary-500">
              Cargando...
            </div>
          ) : salesByPeriod && salesByPeriod.length > 0 ? (
            <div className="h-64">
              <SimpleBarChart data={salesByPeriod} />
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-secondary-500">
              No hay datos disponibles
            </div>
          )}
        </div>

        {/* Sales by Payment Method */}
        <div className="bg-secondary-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-secondary-900 mb-4">Por Método de Pago</h3>
          {salesByPayment && salesByPayment.length > 0 ? (
            <div className="space-y-3">
              {salesByPayment.map((item) => (
                <div key={item.payment_method} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{
                        backgroundColor:
                          item.payment_method === 'cash'
                            ? '#22c55e'
                            : item.payment_method === 'card'
                            ? '#3b82f6'
                            : '#f59e0b',
                      }}
                    />
                    <span className="text-sm text-secondary-700">
                      {item.payment_method_display}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-secondary-900">
                      {formatCurrency(item.total_amount || 0)}
                    </p>
                    <p className="text-xs text-secondary-500">{(item.percentage || 0).toFixed(1)}%</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-secondary-500">
              No hay datos disponibles
            </div>
          )}
        </div>
      </div>

      {/* Tables Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <div className="bg-secondary-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-secondary-900 mb-4">Productos Más Vendidos</h3>
          {topProducts && topProducts.length > 0 ? (
            <div className="space-y-2">
              {topProducts.slice(0, 5).map((product, index) => (
                <div
                  key={product.product_id}
                  className="flex items-center justify-between py-2 border-b border-secondary-200 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-secondary-400 w-6">
                      #{index + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-secondary-900">
                        {product.product_name}
                      </p>
                      <p className="text-xs text-secondary-500">{product.product_sku}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-secondary-900">
                      {product.total_quantity} vendidos
                    </p>
                    <p className="text-xs text-secondary-500">
                      {formatCurrency(product.total_revenue || 0)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-secondary-500">
              No hay datos disponibles
            </div>
          )}
        </div>

        {/* Sales by Category */}
        <div className="bg-secondary-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-secondary-900 mb-4">Ventas por Categoría</h3>
          {salesByCategory && salesByCategory.length > 0 ? (
            <div className="space-y-2">
              {salesByCategory.slice(0, 5).map((category) => (
                <div
                  key={category.category_id}
                  className="flex items-center justify-between py-2 border-b border-secondary-200 last:border-0"
                >
                  <span className="text-sm text-secondary-700">{category.category_name}</span>
                  <div className="text-right">
                    <p className="text-sm font-medium text-secondary-900">
                      {formatCurrency(category.total_revenue || 0)}
                    </p>
                    <p className="text-xs text-secondary-500">{(category.percentage || 0).toFixed(1)}%</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-secondary-500">
              No hay datos disponibles
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Inventory Report Component
function InventoryReport({ branchId }: { branchId?: number; dateRange: DateRangeParams }) {
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().split('T')[0])

  const { data: summary } = useQuery({
    queryKey: ['inventory-summary', branchId],
    queryFn: () => inventoryReportsApi.getSummary(branchId),
  })

  const { data: stockByCategory } = useQuery({
    queryKey: ['stock-by-category', branchId],
    queryFn: () => inventoryReportsApi.getByCategory(branchId),
  })

  const { data: salesByDate, isLoading: isLoadingSales } = useQuery({
    queryKey: ['sales-by-date', selectedDate, branchId],
    queryFn: () => inventoryReportsApi.getSalesByDate({ target_date: selectedDate, branch_id: branchId }),
    enabled: !!selectedDate,
  })

  const totalSalesAmount = useMemo(() => {
    return salesByDate?.reduce((sum, sale) => sum + sale.total, 0) || 0
  }, [salesByDate])

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Productos"
          value={summary?.total_products?.toString() || '0'}
          icon={Package}
          iconBg="bg-primary-100"
          iconColor="text-primary-600"
        />
        <MetricCard
          title="Valor en Stock"
          value={formatCurrency(summary?.total_stock_value || 0)}
          icon={DollarSign}
          iconBg="bg-success-100"
          iconColor="text-success-600"
        />
        <MetricCard
          title="Stock Bajo"
          value={summary?.low_stock_count?.toString() || '0'}
          icon={AlertTriangle}
          iconBg="bg-warning-100"
          iconColor="text-warning-600"
        />
        <MetricCard
          title="Sin Stock"
          value={summary?.out_of_stock_count?.toString() || '0'}
          icon={AlertTriangle}
          iconBg="bg-danger-100"
          iconColor="text-danger-600"
        />
      </div>

      {/* Stock by Category */}
      <div className="bg-secondary-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-secondary-900 mb-4">Stock por Categoría</h3>
        {stockByCategory && stockByCategory.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {stockByCategory.map((category) => (
              <div
                key={category.category_id}
                className="bg-white rounded-lg p-3 border border-secondary-200"
              >
                <p className="text-sm font-medium text-secondary-900 mb-1">
                  {category.category_name}
                </p>
                <div className="flex justify-between text-xs text-secondary-500">
                  <span>{category.product_count} productos</span>
                  <span>{category.total_quantity} unidades</span>
                </div>
                <p className="text-sm font-medium text-success-600 mt-1">
                  {formatCurrency(category.stock_value || 0)}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="h-32 flex items-center justify-center text-secondary-500">
            No hay datos disponibles
          </div>
        )}
      </div>

      {/* Sales by Date Table */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-medium text-secondary-900">Ventas del Día</h3>
            <p className="text-xs text-secondary-500 mt-1">
              {salesByDate?.length || 0} ventas · Total: {formatCurrency(totalSalesAmount)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-secondary-400" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="px-3 py-1.5 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
        {isLoadingSales ? (
          <div className="h-64 flex items-center justify-center text-secondary-500">
            Cargando...
          </div>
        ) : salesByDate && salesByDate.length > 0 ? (
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-white border-b border-secondary-200">
                <tr className="text-left text-secondary-500">
                  <th className="pb-2 pr-4 font-medium">N° Venta</th>
                  <th className="pb-2 pr-4 font-medium">Hora</th>
                  <th className="pb-2 pr-4 font-medium">Cajero</th>
                  <th className="pb-2 pr-4 font-medium text-center">Items</th>
                  <th className="pb-2 pr-4 font-medium">Método</th>
                  <th className="pb-2 font-medium text-right">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secondary-200">
                {salesByDate.map((sale) => (
                  <tr key={sale.id} className="hover:bg-secondary-50">
                    <td className="py-2 pr-4 font-medium text-secondary-900">{sale.sale_number}</td>
                    <td className="py-2 pr-4 text-secondary-600">{sale.time}</td>
                    <td className="py-2 pr-4 text-secondary-600">{sale.cashier_name}</td>
                    <td className="py-2 pr-4 text-center text-secondary-600">{sale.items_count}</td>
                    <td className="py-2 pr-4 text-secondary-600">{sale.payment_method}</td>
                    <td className="py-2 text-right font-medium text-success-600">
                      {formatCurrency(sale.total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center text-secondary-500">
            No hay ventas en esta fecha
          </div>
        )}
      </div>

    </div>
  )
}

// Employees Report Component
function EmployeesReport({ dateRange, branchId }: { dateRange: DateRangeParams; branchId?: number }) {
  const { data: performance, isLoading: isLoadingPerformance } = useQuery({
    queryKey: ['employee-performance', dateRange, branchId],
    queryFn: () => employeeReportsApi.getPerformance({ ...dateRange, branch_id: branchId }),
  })

  const { data: shiftSummary } = useQuery({
    queryKey: ['shift-summary', dateRange, branchId],
    queryFn: () => employeeReportsApi.getShiftSummary({ ...dateRange, branch_id: branchId }),
  })

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Turnos"
          value={shiftSummary?.total_shifts?.toString() || '0'}
          icon={Clock}
          iconBg="bg-primary-100"
          iconColor="text-primary-600"
        />
        <MetricCard
          title="Horas Trabajadas"
          value={`${(shiftSummary?.total_hours || 0).toFixed(1)}h`}
          icon={Clock}
          iconBg="bg-success-100"
          iconColor="text-success-600"
        />
        <MetricCard
          title="Promedio por Turno"
          value={`${(shiftSummary?.average_shift_length || 0).toFixed(1)}h`}
          icon={BarChart3}
          iconBg="bg-warning-100"
          iconColor="text-warning-600"
        />
        <MetricCard
          title="Empleados Activos"
          value={shiftSummary?.employees_count?.toString() || '0'}
          icon={Users}
          iconBg="bg-info-100"
          iconColor="text-info-600"
        />
      </div>

      {/* Performance Table */}
      <div className="bg-secondary-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-secondary-900 mb-4">Rendimiento de Empleados</h3>
        {isLoadingPerformance ? (
          <div className="h-64 flex items-center justify-center text-secondary-500">
            Cargando...
          </div>
        ) : performance && performance.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-secondary-500">
                  <th className="pb-2 font-medium">Empleado</th>
                  <th className="pb-2 font-medium">Sucursal</th>
                  <th className="pb-2 font-medium text-right">Ventas</th>
                  <th className="pb-2 font-medium text-right">Transacciones</th>
                  <th className="pb-2 font-medium text-right">Ticket Prom.</th>
                  <th className="pb-2 font-medium text-right">Horas</th>
                  <th className="pb-2 font-medium text-right">Ventas/Hora</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secondary-200">
                {performance.map((emp) => (
                  <tr key={emp.employee_id}>
                    <td className="py-2">
                      <div>
                        <p className="font-medium text-secondary-900">{emp.employee_name}</p>
                        <p className="text-xs text-secondary-500">{emp.employee_code}</p>
                      </div>
                    </td>
                    <td className="py-2 text-secondary-600">{emp.branch_name}</td>
                    <td className="py-2 text-right font-medium text-secondary-900">
                      {formatCurrency(emp.total_sales)}
                    </td>
                    <td className="py-2 text-right text-secondary-600">{emp.transaction_count || 0}</td>
                    <td className="py-2 text-right text-secondary-600">
                      {formatCurrency(emp.average_ticket || 0)}
                    </td>
                    <td className="py-2 text-right text-secondary-600">
                      {(emp.hours_worked || 0).toFixed(1)}h
                    </td>
                    <td className="py-2 text-right font-medium text-success-600">
                      {formatCurrency(emp.sales_per_hour || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center text-secondary-500">
            No hay datos disponibles
          </div>
        )}
      </div>

      {/* Shifts by Weekday */}
      {shiftSummary?.by_weekday && shiftSummary.by_weekday.length > 0 && (
        <div className="bg-secondary-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-secondary-900 mb-4">Turnos por Día</h3>
          <div className="grid grid-cols-7 gap-2">
            {shiftSummary.by_weekday.map((day) => (
              <div
                key={day.weekday}
                className="bg-white rounded-lg p-3 text-center border border-secondary-200"
              >
                <p className="text-xs text-secondary-500">{day.weekday_name}</p>
                <p className="text-lg font-bold text-secondary-900">{day.shift_count}</p>
                <p className="text-xs text-secondary-500">{(day.total_hours || 0).toFixed(1)}h</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Branches Report Component
function BranchesReport({ dateRange }: { dateRange: Omit<DateRangeParams, 'branch_id'> }) {
  const { data: comparison, isLoading } = useQuery({
    queryKey: ['branch-comparison', dateRange],
    queryFn: () => branchReportsApi.getComparison(dateRange),
  })

  const totalSales = comparison?.reduce((sum, b) => sum + (b.total_sales || 0), 0) || 0

  return (
    <div className="space-y-6">
      {/* Branch Comparison Table */}
      <div className="bg-secondary-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-secondary-900 mb-4">Comparación de Sucursales</h3>
        {isLoading ? (
          <div className="h-64 flex items-center justify-center text-secondary-500">
            Cargando...
          </div>
        ) : comparison && comparison.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-secondary-500">
                  <th className="pb-2 font-medium">Sucursal</th>
                  <th className="pb-2 font-medium text-right">Ventas</th>
                  <th className="pb-2 font-medium text-right">% del Total</th>
                  <th className="pb-2 font-medium text-right">Transacciones</th>
                  <th className="pb-2 font-medium text-right">Ticket Prom.</th>
                  <th className="pb-2 font-medium text-right">Utilidad</th>
                  <th className="pb-2 font-medium text-right">Margen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secondary-200">
                {comparison.map((branch) => (
                  <tr key={branch.branch_id}>
                    <td className="py-3 font-medium text-secondary-900">{branch.branch_name}</td>
                    <td className="py-3 text-right font-medium text-secondary-900">
                      {formatCurrency(branch.total_sales)}
                    </td>
                    <td className="py-3 text-right text-secondary-600">
                      {totalSales > 0 ? (((branch.total_sales || 0) / totalSales) * 100).toFixed(1) : 0}%
                    </td>
                    <td className="py-3 text-right text-secondary-600">
                      {branch.transaction_count || 0}
                    </td>
                    <td className="py-3 text-right text-secondary-600">
                      {formatCurrency(branch.average_ticket || 0)}
                    </td>
                    <td className="py-3 text-right text-success-600">
                      {formatCurrency(branch.total_profit || 0)}
                    </td>
                    <td className="py-3 text-right">
                      <Badge
                        variant={
                          (branch.profit_margin || 0) >= 30
                            ? 'success'
                            : (branch.profit_margin || 0) >= 20
                            ? 'warning'
                            : 'danger'
                        }
                      >
                        {(branch.profit_margin || 0).toFixed(1)}%
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="border-t-2 border-secondary-300">
                <tr>
                  <td className="py-3 font-bold text-secondary-900">Total</td>
                  <td className="py-3 text-right font-bold text-secondary-900">
                    {formatCurrency(totalSales)}
                  </td>
                  <td className="py-3 text-right font-bold text-secondary-600">100%</td>
                  <td className="py-3 text-right font-bold text-secondary-600">
                    {comparison.reduce((sum, b) => sum + (b.transaction_count || 0), 0)}
                  </td>
                  <td className="py-3 text-right text-secondary-600">-</td>
                  <td className="py-3 text-right font-bold text-success-600">
                    {formatCurrency(comparison.reduce((sum, b) => sum + (b.total_profit || 0), 0))}
                  </td>
                  <td className="py-3"></td>
                </tr>
              </tfoot>
            </table>
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center text-secondary-500">
            No hay datos disponibles
          </div>
        )}
      </div>

      {/* Branch Cards (Visual Summary) */}
      {comparison && comparison.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {comparison.map((branch) => (
            <div
              key={branch.branch_id}
              className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4"
            >
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-medium text-secondary-900">{branch.branch_name}</h4>
                <Badge
                  variant={
                    (branch.profit_margin || 0) >= 30
                      ? 'success'
                      : (branch.profit_margin || 0) >= 20
                      ? 'warning'
                      : 'danger'
                  }
                >
                  {(branch.profit_margin || 0).toFixed(1)}% margen
                </Badge>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-secondary-500">Ventas</p>
                  <p className="text-lg font-bold text-secondary-900">
                    {formatCurrency(branch.total_sales || 0)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-secondary-500">Utilidad</p>
                  <p className="text-lg font-bold text-success-600">
                    {formatCurrency(branch.total_profit || 0)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-secondary-500">Transacciones</p>
                  <p className="text-sm font-medium text-secondary-700">
                    {branch.transaction_count || 0}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-secondary-500">Artículos</p>
                  <p className="text-sm font-medium text-secondary-700">{branch.items_sold || 0}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Reusable Metric Card Component
interface MetricCardProps {
  title: string
  value: string
  change?: number
  icon: React.ElementType
  iconBg: string
  iconColor: string
}

function MetricCard({ title, value, change, icon: Icon, iconBg, iconColor }: MetricCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${iconBg}`}>
          <Icon className={`w-5 h-5 ${iconColor}`} />
        </div>
        <div className="flex-1">
          <p className="text-sm text-secondary-500">{title}</p>
          <div className="flex items-center gap-2">
            <p className="text-xl font-bold text-secondary-900">{value}</p>
            {change !== undefined && (
              <span
                className={`flex items-center text-xs font-medium ${
                  change >= 0 ? 'text-success-600' : 'text-danger-600'
                }`}
              >
                {change >= 0 ? (
                  <TrendingUp className="w-3 h-3 mr-0.5" />
                ) : (
                  <TrendingDown className="w-3 h-3 mr-0.5" />
                )}
                {Math.abs(change).toFixed(1)}%
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Simple Bar Chart Component (CSS-based, no external library)
interface SimpleBarChartProps {
  data: { period: string; total_sales: number }[]
}

function SimpleBarChart({ data }: SimpleBarChartProps) {
  const maxValue = Math.max(...data.map((d) => d.total_sales), 1)

  return (
    <div className="flex items-end gap-1 h-full pt-4 pb-6">
      {data.slice(-14).map((item, index) => {
        const height = (item.total_sales / maxValue) * 100
        return (
          <div key={index} className="flex-1 flex flex-col items-center group h-full">
            <div className="relative w-full flex justify-center items-end h-full">
              <div
                className="w-full max-w-8 bg-primary-500 rounded-t hover:bg-primary-600 transition-colors"
                style={{ height: `${Math.max(height, 2)}%`, minHeight: '4px' }}
              />
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 hidden group-hover:block bg-secondary-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">
                {formatCurrency(item.total_sales)}
              </div>
            </div>
            <span className="text-[10px] text-secondary-500 truncate w-full text-center mt-1 flex-shrink-0">
              {item.period.slice(-5)}
            </span>
          </div>
        )
      })}
    </div>
  )
}
