import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X, Clock, User, CheckCircle, Eye, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { userReportsApi } from '@/api/userReports'
import { useAuthStore } from '@/store/authStore'
import { StatusBadge } from './StatusBadge'
import { PriorityBadge } from './PriorityBadge'

interface ReportDetailModalProps {
  reportId: number | null
  isOpen: boolean
  onClose: () => void
}

export function ReportDetailModal({ reportId, isOpen, onClose }: ReportDetailModalProps) {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const isAdmin = user?.is_platform_admin || user?.role?.role_type === 'admin'

  const [resolutionNotes, setResolutionNotes] = useState('')
  const [showResolveForm, setShowResolveForm] = useState(false)

  // Fetch report detail
  const { data: report, isLoading } = useQuery({
    queryKey: ['user-report', reportId],
    queryFn: () => userReportsApi.getById(reportId!),
    enabled: isOpen && reportId !== null,
  })

  // Set in review mutation
  const setInReviewMutation = useMutation({
    mutationFn: (id: number) => userReportsApi.setInReview(id),
    onSuccess: () => {
      toast.success('Reporte marcado como en revisión')
      queryClient.invalidateQueries({ queryKey: ['user-reports'] })
      queryClient.invalidateQueries({ queryKey: ['user-report', reportId] })
      queryClient.invalidateQueries({ queryKey: ['user-reports-counts'] })
    },
    onError: () => {
      toast.error('Error al actualizar el estado')
    },
  })

  // Resolve mutation
  const resolveMutation = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes?: string }) =>
      userReportsApi.resolve(id, notes),
    onSuccess: () => {
      toast.success('Reporte marcado como resuelto')
      queryClient.invalidateQueries({ queryKey: ['user-reports'] })
      queryClient.invalidateQueries({ queryKey: ['user-report', reportId] })
      queryClient.invalidateQueries({ queryKey: ['user-reports-counts'] })
      setShowResolveForm(false)
      setResolutionNotes('')
    },
    onError: () => {
      toast.error('Error al resolver el reporte')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => userReportsApi.delete(id),
    onSuccess: () => {
      toast.success('Reporte eliminado')
      queryClient.invalidateQueries({ queryKey: ['user-reports'] })
      queryClient.invalidateQueries({ queryKey: ['user-reports-counts'] })
      onClose()
    },
    onError: () => {
      toast.error('Error al eliminar el reporte')
    },
  })

  const handleResolve = () => {
    if (report) {
      resolveMutation.mutate({ id: report.id, notes: resolutionNotes })
    }
  }

  const handleDelete = () => {
    if (report && confirm('¿Estás seguro de eliminar este reporte?')) {
      deleteMutation.mutate(report.id)
    }
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString('es-MX', {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-secondary-200">
          <h2 className="text-lg font-semibold text-secondary-900">Detalle del Reporte</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-secondary-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="p-8 text-center text-secondary-500">Cargando...</div>
        ) : report ? (
          <div className="p-4 space-y-6">
            {/* Status and Priority */}
            <div className="flex items-center gap-3">
              <StatusBadge status={report.status} />
              <PriorityBadge priority={report.priority} />
            </div>

            {/* Title */}
            <div>
              <h3 className="text-xl font-semibold text-secondary-900">{report.title}</h3>
              <p className="text-sm text-secondary-500 mt-1">
                Categoría: {report.category_display}
              </p>
            </div>

            {/* Description */}
            <div>
              <h4 className="text-sm font-medium text-secondary-700 mb-2">Descripción</h4>
              <div className="bg-secondary-50 rounded-lg p-4">
                <p className="text-secondary-700 whitespace-pre-wrap">{report.description}</p>
              </div>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 text-sm text-secondary-600">
                <User className="w-4 h-4" />
                <span>Creado por: {report.created_by_name}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-secondary-600">
                <Clock className="w-4 h-4" />
                <span>{formatDate(report.created_at)}</span>
              </div>
            </div>

            {/* Assignment info (for empleados category) */}
            {report.category === 'empleados' && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="text-sm font-medium text-blue-800 mb-2">Asignación</h4>
                {report.assign_to_all ? (
                  <p className="text-sm text-blue-700">Asignado a todos los empleados</p>
                ) : report.assigned_employee_names.length > 0 ? (
                  <p className="text-sm text-blue-700">
                    Asignado a: {report.assigned_employee_names.join(', ')}
                  </p>
                ) : (
                  <p className="text-sm text-blue-700">Sin asignación específica</p>
                )}
              </div>
            )}

            {/* Review info */}
            {report.reviewed_at && (
              <div className="flex items-center gap-2 text-sm text-blue-600">
                <Eye className="w-4 h-4" />
                <span>
                  Revisado por {report.reviewed_by_name} el {formatDate(report.reviewed_at)}
                </span>
              </div>
            )}

            {/* Resolution info */}
            {report.resolved_at && (
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2 text-sm text-green-700 mb-2">
                  <CheckCircle className="w-4 h-4" />
                  <span>
                    Resuelto por {report.resolved_by_name} el {formatDate(report.resolved_at)}
                  </span>
                </div>
                {report.resolution_notes && (
                  <div>
                    <h5 className="text-sm font-medium text-green-800 mb-1">Notas de resolución:</h5>
                    <p className="text-sm text-green-700">{report.resolution_notes}</p>
                  </div>
                )}
              </div>
            )}

            {/* Status Actions - Admin or assigned employee can change status */}
            {report.can_change_status && (
              <div className="border-t border-secondary-200 pt-4 space-y-3">
                <h4 className="text-sm font-medium text-secondary-700">
                  {isAdmin ? 'Acciones de Administrador' : 'Actualizar Estado'}
                </h4>

                  {/* Set in review button */}
                  {report.status === 'pendiente' && (
                    <button
                      onClick={() => setInReviewMutation.mutate(report.id)}
                      disabled={setInReviewMutation.isPending}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 rounded-lg transition-colors disabled:opacity-50"
                    >
                      <Eye className="w-4 h-4" />
                      {setInReviewMutation.isPending ? 'Procesando...' : 'Marcar en Revisión'}
                    </button>
                  )}

                  {/* Resolve section */}
                  {!showResolveForm ? (
                    <button
                      onClick={() => setShowResolveForm(true)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-green-700 bg-green-100 hover:bg-green-200 rounded-lg transition-colors"
                    >
                      <CheckCircle className="w-4 h-4" />
                      Marcar como Resuelto
                    </button>
                  ) : (
                    <div className="space-y-3 p-4 bg-secondary-50 rounded-lg">
                      <textarea
                        value={resolutionNotes}
                        onChange={(e) => setResolutionNotes(e.target.value)}
                        placeholder="Notas de resolución (opcional)"
                        rows={3}
                        className="w-full px-3 py-2 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setShowResolveForm(false)
                            setResolutionNotes('')
                          }}
                          className="flex-1 px-4 py-2 text-sm font-medium text-secondary-700 hover:bg-secondary-200 rounded-lg transition-colors"
                        >
                          Cancelar
                        </button>
                        <button
                          onClick={handleResolve}
                          disabled={resolveMutation.isPending}
                          className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50"
                        >
                          {resolveMutation.isPending ? 'Procesando...' : 'Confirmar'}
                        </button>
                      </div>
                    </div>
                  )}
              </div>
            )}

            {/* Delete button (for own reports or admin) */}
            {(isAdmin || report.created_by === user?.id) && report.status === 'pendiente' && (
              <div className="border-t border-secondary-200 pt-4">
                <button
                  onClick={handleDelete}
                  disabled={deleteMutation.isPending}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-red-700 bg-red-100 hover:bg-red-200 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                  {deleteMutation.isPending ? 'Eliminando...' : 'Eliminar Reporte'}
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="p-8 text-center text-secondary-500">Reporte no encontrado</div>
        )}
      </div>
    </div>
  )
}
