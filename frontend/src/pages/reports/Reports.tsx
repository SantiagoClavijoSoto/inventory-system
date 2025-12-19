import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  userReportsApi,
  ReportCategory,
  ReportStatus,
  UserReportListItem,
  CATEGORY_LABELS,
  STATUS_CONFIG,
} from '@/api/userReports'
import { useAuthStore } from '@/store/authStore'
import {
  Package,
  Users,
  Building2,
  Plus,
  FileText,
  Filter,
  User,
  Inbox,
} from 'lucide-react'
import { StatusBadge, PriorityBadge, CreateReportModal, ReportDetailModal } from './components'

type ViewMode = 'my-reports' | 'inbox'

export function Reports() {
  const { user } = useAuthStore()
  const isAdmin = user?.is_platform_admin || user?.role?.role_type === 'admin'

  const [viewMode, setViewMode] = useState<ViewMode>('my-reports')
  const [activeTab, setActiveTab] = useState<ReportCategory>('inventario')
  const [statusFilter, setStatusFilter] = useState<ReportStatus | ''>('')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null)

  // Fetch MY reports (created by me)
  const { data: myReports, isLoading: isLoadingMy } = useQuery({
    queryKey: ['user-reports', 'mine', statusFilter],
    queryFn: () =>
      userReportsApi.getAll({
        mine_only: true,
        status: statusFilter || undefined,
      }),
    enabled: viewMode === 'my-reports',
  })

  // Fetch INBOX reports (assigned to me or all reports for admin)
  // Admins filter by category tab; regular users see all assigned reports
  const { data: inboxReports, isLoading: isLoadingInbox } = useQuery({
    queryKey: ['user-reports', 'inbox', isAdmin ? activeTab : 'all', statusFilter],
    queryFn: () =>
      userReportsApi.getAll({
        category: isAdmin ? activeTab : undefined,
        status: statusFilter || undefined,
        mine_only: false,
      }),
    enabled: viewMode === 'inbox',
  })

  // Fetch counts
  const { data: counts } = useQuery({
    queryKey: ['user-reports-counts'],
    queryFn: () => userReportsApi.getCounts(),
  })

  // Category tabs for inbox view
  const categoryTabs = [
    { id: 'inventario' as const, label: 'Inventario', icon: Package },
    ...(isAdmin ? [{ id: 'empleados' as const, label: 'Empleados', icon: Users }] : []),
    { id: 'sucursales' as const, label: 'Sucursales', icon: Building2 },
  ]

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  }

  const reports = viewMode === 'my-reports' ? myReports : inboxReports
  const isLoading = viewMode === 'my-reports' ? isLoadingMy : isLoadingInbox

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Reportes</h1>
          <p className="text-secondary-500 mt-1">
            {viewMode === 'my-reports'
              ? 'Reportes que has creado'
              : isAdmin
              ? 'Reportes de tu equipo para gestionar'
              : 'Reportes asignados a ti'}
          </p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Crear Reporte
        </button>
      </div>

      {/* View Mode Toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => {
            setViewMode('my-reports')
            setStatusFilter('')
          }}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-colors ${
            viewMode === 'my-reports'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-secondary-700 border border-secondary-300 hover:bg-secondary-50'
          }`}
        >
          <User className="w-4 h-4" />
          Mis Reportes
        </button>
        <button
          onClick={() => {
            setViewMode('inbox')
            setStatusFilter('')
          }}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-colors ${
            viewMode === 'inbox'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-secondary-700 border border-secondary-300 hover:bg-secondary-50'
          }`}
        >
          <Inbox className="w-4 h-4" />
          {isAdmin ? 'Bandeja de Reportes' : 'Asignados a Mí'}
        </button>
      </div>

      {/* Summary Cards */}
      {counts && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <SummaryCard
            title="Total"
            value={counts.total}
            color="bg-secondary-100 text-secondary-700"
          />
          <SummaryCard
            title="Pendientes"
            value={counts.by_status.pendiente}
            color="bg-yellow-100 text-yellow-700"
          />
          <SummaryCard
            title="En Revisión"
            value={counts.by_status.en_revision}
            color="bg-blue-100 text-blue-700"
          />
          <SummaryCard
            title="Resueltos"
            value={counts.by_status.resuelto}
            color="bg-green-100 text-green-700"
          />
        </div>
      )}

      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-sm border border-secondary-200">
        {/* Category Tabs (only for admin in inbox view) */}
        {viewMode === 'inbox' && isAdmin && (
          <div className="border-b border-secondary-200">
            <nav className="flex -mb-px">
              {categoryTabs.map((tab) => {
                const Icon = tab.icon
                const count = counts?.by_category[tab.id] || 0
                return (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveTab(tab.id)
                      setStatusFilter('')
                    }}
                    className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                    {count > 0 && (
                      <span className="ml-1 px-2 py-0.5 text-xs bg-secondary-100 text-secondary-600 rounded-full">
                        {count}
                      </span>
                    )}
                  </button>
                )
              })}
            </nav>
          </div>
        )}

        {/* Filters */}
        <div className="p-4 border-b border-secondary-200 bg-secondary-50">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-secondary-400" />
              <span className="text-sm text-secondary-600">Filtrar por estado:</span>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ReportStatus | '')}
              className="px-3 py-1.5 border border-secondary-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">Todos</option>
              {(Object.keys(STATUS_CONFIG) as ReportStatus[]).map((status) => (
                <option key={status} value={status}>
                  {STATUS_CONFIG[status].label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Reports List */}
        <div className="p-4">
          {isLoading ? (
            <div className="py-12 text-center text-secondary-500">Cargando reportes...</div>
          ) : reports && reports.length > 0 ? (
            <div className="space-y-3">
              {reports.map((report) => (
                <ReportCard
                  key={report.id}
                  report={report}
                  onClick={() => setSelectedReportId(report.id)}
                  formatDate={formatDate}
                  showAuthor={viewMode === 'inbox'}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              viewMode={viewMode}
              category={activeTab}
              onCreateClick={() => setIsCreateModalOpen(true)}
            />
          )}
        </div>
      </div>

      {/* Create Modal */}
      <CreateReportModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        defaultCategory={viewMode === 'inbox' ? activeTab : 'inventario'}
      />

      {/* Detail Modal */}
      <ReportDetailModal
        reportId={selectedReportId}
        isOpen={selectedReportId !== null}
        onClose={() => setSelectedReportId(null)}
      />
    </div>
  )
}

// Summary Card Component
function SummaryCard({
  title,
  value,
  color,
}: {
  title: string
  value: number
  color: string
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-4">
      <p className="text-sm text-secondary-500">{title}</p>
      <div className="flex items-center gap-2 mt-1">
        <span className="text-2xl font-bold text-secondary-900">{value}</span>
        <span className={`px-2 py-0.5 text-xs rounded-full ${color}`}>{title.toLowerCase()}</span>
      </div>
    </div>
  )
}

// Report Card Component
function ReportCard({
  report,
  onClick,
  formatDate,
  showAuthor,
}: {
  report: UserReportListItem
  onClick: () => void
  formatDate: (date: string) => string
  showAuthor: boolean
}) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 bg-secondary-50 hover:bg-secondary-100 rounded-lg transition-colors"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <StatusBadge status={report.status} />
            <PriorityBadge priority={report.priority} />
            <span className="text-xs text-secondary-400 px-2 py-0.5 bg-secondary-200 rounded">
              {report.category_display}
            </span>
          </div>
          <h3 className="font-medium text-secondary-900 truncate">{report.title}</h3>
          <p className="text-sm text-secondary-500 mt-1">
            {showAuthor ? `Por ${report.created_by_name} · ` : ''}
            {formatDate(report.created_at)}
          </p>
        </div>
        <FileText className="w-5 h-5 text-secondary-400 flex-shrink-0 ml-4" />
      </div>
    </button>
  )
}

// Empty State Component
function EmptyState({
  viewMode,
  category,
  onCreateClick,
}: {
  viewMode: ViewMode
  category: ReportCategory
  onCreateClick: () => void
}) {
  return (
    <div className="py-12 text-center">
      <FileText className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-secondary-900 mb-1">
        {viewMode === 'my-reports' ? 'No has creado reportes' : 'No hay reportes'}
      </h3>
      <p className="text-secondary-500 mb-4">
        {viewMode === 'my-reports'
          ? 'Crea tu primer reporte para empezar'
          : `No hay reportes en la categoría ${CATEGORY_LABELS[category].toLowerCase()}`}
      </p>
      <button
        onClick={onCreateClick}
        className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Crear Reporte
      </button>
    </div>
  )
}
