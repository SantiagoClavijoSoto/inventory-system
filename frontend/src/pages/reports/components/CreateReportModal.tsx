import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import {
  userReportsApi,
  ReportCategory,
  ReportPriority,
  CreateUserReportData,
  CATEGORY_LABELS,
  PRIORITY_CONFIG,
} from '@/api/userReports'
import { employeesApi } from '@/api/employees'
import { useAuthStore } from '@/store/authStore'

interface CreateReportModalProps {
  isOpen: boolean
  onClose: () => void
  defaultCategory?: ReportCategory
}

export function CreateReportModal({ isOpen, onClose, defaultCategory }: CreateReportModalProps) {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const isAdmin = user?.is_platform_admin || user?.role?.role_type === 'admin'

  const [formData, setFormData] = useState<CreateUserReportData>({
    title: '',
    description: '',
    category: defaultCategory || 'inventario',
    priority: 'media',
    assign_to_all: false,
    assigned_employees: [],
  })

  // Fetch employees for assignment (admin only, empleados category)
  const { data: employees } = useQuery({
    queryKey: ['employees-for-reports'],
    queryFn: () => employeesApi.getAll(),
    enabled: isAdmin && formData.category === 'empleados',
  })

  const createMutation = useMutation({
    mutationFn: (data: CreateUserReportData) => userReportsApi.create(data),
    onSuccess: () => {
      toast.success('Reporte creado exitosamente')
      queryClient.invalidateQueries({ queryKey: ['user-reports'] })
      queryClient.invalidateQueries({ queryKey: ['user-reports-counts'] })
      onClose()
      resetForm()
    },
    onError: () => {
      toast.error('Error al crear el reporte')
    },
  })

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      category: defaultCategory || 'inventario',
      priority: 'media',
      assign_to_all: false,
      assigned_employees: [],
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim() || !formData.description.trim()) {
      toast.error('Completa todos los campos requeridos')
      return
    }
    createMutation.mutate(formData)
  }

  const handleClose = () => {
    resetForm()
    onClose()
  }

  // Categories available based on role
  const availableCategories: ReportCategory[] = isAdmin
    ? ['inventario', 'empleados', 'sucursales']
    : ['inventario', 'sucursales']

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-secondary-200">
          <h2 className="text-lg font-semibold text-secondary-900">Crear Nuevo Reporte</h2>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-secondary-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">
              Categoría
            </label>
            <select
              value={formData.category}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  category: e.target.value as ReportCategory,
                  assign_to_all: false,
                  assigned_employees: [],
                })
              }
              className="w-full px-3 py-2 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {availableCategories.map((cat) => (
                <option key={cat} value={cat}>
                  {CATEGORY_LABELS[cat]}
                </option>
              ))}
            </select>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">
              Título <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Escribe un título descriptivo"
              className="w-full px-3 py-2 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              maxLength={200}
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">
              Descripción <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe el problema o situación en detalle"
              rows={5}
              className="w-full px-3 py-2 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">
              Prioridad
            </label>
            <select
              value={formData.priority}
              onChange={(e) =>
                setFormData({ ...formData, priority: e.target.value as ReportPriority })
              }
              className="w-full px-3 py-2 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {(Object.keys(PRIORITY_CONFIG) as ReportPriority[]).map((priority) => (
                <option key={priority} value={priority}>
                  {PRIORITY_CONFIG[priority].label}
                </option>
              ))}
            </select>
          </div>

          {/* Assignment (only for admin + empleados category) */}
          {isAdmin && formData.category === 'empleados' && (
            <div className="p-4 bg-secondary-50 rounded-lg space-y-3">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-secondary-500" />
                <span className="text-sm font-medium text-secondary-700">Asignación</span>
              </div>

              {/* Assign to all */}
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.assign_to_all}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      assign_to_all: e.target.checked,
                      assigned_employees: e.target.checked ? [] : formData.assigned_employees,
                    })
                  }
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <span className="text-sm text-secondary-700">Asignar a todos los empleados</span>
              </label>

              {/* Specific employees */}
              {!formData.assign_to_all && employees && employees.results.length > 0 && (
                <div>
                  <label className="block text-sm text-secondary-600 mb-2">
                    O selecciona empleados específicos:
                  </label>
                  <div className="max-h-40 overflow-y-auto space-y-1 border border-secondary-200 rounded-lg p-2 bg-white">
                    {employees.results.map((emp) => (
                      <label
                        key={emp.id}
                        className="flex items-center gap-2 cursor-pointer hover:bg-secondary-50 p-1 rounded"
                      >
                        <input
                          type="checkbox"
                          checked={formData.assigned_employees?.includes(emp.id)}
                          onChange={(e) => {
                            const newEmployees = e.target.checked
                              ? [...(formData.assigned_employees || []), emp.id]
                              : formData.assigned_employees?.filter((id) => id !== emp.id) || []
                            setFormData({ ...formData, assigned_employees: newEmployees })
                          }}
                          className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                        />
                        <span className="text-sm text-secondary-700">{emp.full_name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-secondary-700 hover:bg-secondary-100 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creando...' : 'Crear Reporte'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
