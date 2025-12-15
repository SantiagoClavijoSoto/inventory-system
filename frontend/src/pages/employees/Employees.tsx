import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'
import { employeesApi } from '@/api/employees'
import { branchesApi } from '@/api/branches'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Select,
  Badge,
  Modal,
  ModalFooter,
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  Spinner,
} from '@/components/ui'
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Users,
  AlertTriangle,
  RefreshCw,
  Clock,
  UserCheck,
  Calendar,
  Phone,
  Building2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import type { Employee, CreateEmployeeRequest, UpdateEmployeeRequest } from '@/types'

const EMPLOYMENT_TYPE_OPTIONS = [
  { value: 'full_time', label: 'Tiempo completo' },
  { value: 'part_time', label: 'Medio tiempo' },
  { value: 'contract', label: 'Por contrato' },
  { value: 'temporary', label: 'Temporal' },
]

const STATUS_OPTIONS = [
  { value: 'active', label: 'Activo' },
  { value: 'inactive', label: 'Inactivo' },
  { value: 'on_leave', label: 'De licencia' },
  { value: 'terminated', label: 'Terminado' },
]

export function Employees() {
  const queryClient = useQueryClient()
  useAuthStore()

  // State
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('active')
  const [employmentTypeFilter, setEmploymentTypeFilter] = useState<string>('')
  const [branchFilter, setBranchFilter] = useState<string>('')
  const [page, setPage] = useState(1)
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)

  // Queries
  const { data: employeesData, isLoading } = useQuery({
    queryKey: ['employees', { search, status: statusFilter, employment_type: employmentTypeFilter, branch: branchFilter, page }],
    queryFn: () =>
      employeesApi.getAll({
        search: search || undefined,
        status: statusFilter || undefined,
        employment_type: employmentTypeFilter || undefined,
        branch: branchFilter ? Number(branchFilter) : undefined,
        page,
        page_size: 20,
      }),
  })

  const { data: branches } = useQuery({
    queryKey: ['branches-simple'],
    queryFn: () => branchesApi.getSimple(),
  })

  // Mutations
  const deleteMutation = useMutation({
    mutationFn: employeesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      toast.success('Empleado eliminado correctamente')
      setIsDeleteModalOpen(false)
      setSelectedEmployee(null)
    },
    onError: () => {
      toast.error('Error al eliminar el empleado')
    },
  })

  const handleDelete = () => {
    if (selectedEmployee) {
      deleteMutation.mutate(selectedEmployee.id)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'success' | 'warning' | 'danger' | 'secondary'; label: string }> = {
      active: { variant: 'success', label: 'Activo' },
      inactive: { variant: 'secondary', label: 'Inactivo' },
      on_leave: { variant: 'warning', label: 'De licencia' },
      terminated: { variant: 'danger', label: 'Terminado' },
    }
    const config = statusConfig[status] || { variant: 'secondary', label: status }
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  const getEmploymentTypeBadge = (type: string) => {
    const typeLabels: Record<string, string> = {
      full_time: 'Tiempo completo',
      part_time: 'Medio tiempo',
      contract: 'Por contrato',
      temporary: 'Temporal',
    }
    return <Badge variant="secondary">{typeLabels[type] || type}</Badge>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Empleados</h1>
          <p className="text-secondary-500">
            Gestiona el personal de tu negocio
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4" />
          Nuevo Empleado
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
                <input
                  type="text"
                  placeholder="Buscar por nombre, código o puesto..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value)
                    setPage(1)
                  }}
                  className="w-full pl-10 pr-4 py-2 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <Select
              options={[
                { value: '', label: 'Todas las sucursales' },
                ...(branches?.map((b) => ({ value: String(b.id), label: b.name })) || []),
              ]}
              value={branchFilter}
              onChange={(e) => {
                setBranchFilter(e.target.value)
                setPage(1)
              }}
              className="w-48"
            />

            <Select
              options={[
                { value: '', label: 'Todos los estados' },
                ...STATUS_OPTIONS,
              ]}
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
              className="w-40"
            />

            <Select
              options={[
                { value: '', label: 'Tipo de empleo' },
                ...EMPLOYMENT_TYPE_OPTIONS,
              ]}
              value={employmentTypeFilter}
              onChange={(e) => {
                setEmploymentTypeFilter(e.target.value)
                setPage(1)
              }}
              className="w-44"
            />

            <Button
              variant="secondary"
              onClick={() => {
                setSearch('')
                setBranchFilter('')
                setStatusFilter('active')
                setEmploymentTypeFilter('')
                setPage(1)
              }}
            >
              <RefreshCw className="w-4 h-4" />
              Limpiar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Employees Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {employeesData?.count || 0} empleados encontrados
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Spinner size="lg" />
            </div>
          ) : employeesData?.results.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-secondary-500">
              <Users className="w-12 h-12 mb-4 text-secondary-300" />
              <p className="text-lg font-medium">No se encontraron empleados</p>
              <p className="text-sm">Intenta ajustar los filtros de búsqueda</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Empleado</TableHead>
                  <TableHead>Código</TableHead>
                  <TableHead>Sucursal</TableHead>
                  <TableHead>Puesto</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Turno</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="w-20">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {employeesData?.results.map((employee) => (
                  <TableRow key={employee.id} clickable>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                          <span className="text-sm text-primary-700 font-medium">
                            {employee.user.first_name?.[0]}
                            {employee.user.last_name?.[0]}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-secondary-900">{employee.full_name}</p>
                          <p className="text-xs text-secondary-500">{employee.user.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">{employee.employee_code}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-secondary-400" />
                        <span>{employee.branch.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>{employee.position}</TableCell>
                    <TableCell>{getEmploymentTypeBadge(employee.employment_type)}</TableCell>
                    <TableCell>
                      {employee.is_clocked_in ? (
                        <div className="flex items-center gap-1.5 text-success-600">
                          <Clock className="w-4 h-4" />
                          <span className="text-sm font-medium">En turno</span>
                        </div>
                      ) : (
                        <span className="text-secondary-400 text-sm">Sin turno</span>
                      )}
                    </TableCell>
                    <TableCell>{getStatusBadge(employee.status)}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => {
                            setSelectedEmployee(employee)
                            setIsModalOpen(true)
                          }}
                          className="p-2 hover:bg-secondary-100 rounded-lg transition-colors"
                        >
                          <Edit2 className="w-4 h-4 text-secondary-600" />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedEmployee(employee)
                            setIsDeleteModalOpen(true)
                          }}
                          className="p-2 hover:bg-danger-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4 text-danger-600" />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>

        {/* Pagination */}
        {employeesData && employeesData.total_pages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-secondary-200">
            <p className="text-sm text-secondary-500">
              Página {employeesData.current_page} de {employeesData.total_pages}
            </p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={!employeesData.previous}
                onClick={() => setPage(page - 1)}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={!employeesData.next}
                onClick={() => setPage(page + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Employee Form Modal */}
      <EmployeeFormModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setSelectedEmployee(null)
        }}
        employee={selectedEmployee}
        branches={branches || []}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false)
          setSelectedEmployee(null)
        }}
        title="Eliminar Empleado"
      >
        <div className="flex items-start gap-4">
          <div className="p-3 bg-danger-100 rounded-full">
            <AlertTriangle className="w-6 h-6 text-danger-600" />
          </div>
          <div>
            <p className="text-secondary-900">
              ¿Estás seguro de que deseas eliminar al empleado{' '}
              <strong>{selectedEmployee?.full_name}</strong>?
            </p>
            <p className="text-sm text-secondary-500 mt-1">
              Esta acción no se puede deshacer. El usuario asociado también será desactivado.
            </p>
          </div>
        </div>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => {
              setIsDeleteModalOpen(false)
              setSelectedEmployee(null)
            }}
          >
            Cancelar
          </Button>
          <Button
            variant="danger"
            onClick={handleDelete}
            isLoading={deleteMutation.isPending}
          >
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}

// Employee Form Modal Component
interface EmployeeFormModalProps {
  isOpen: boolean
  onClose: () => void
  employee: Employee | null
  branches: Array<{ id: number; name: string }>
}

function EmployeeFormModal({ isOpen, onClose, employee, branches }: EmployeeFormModalProps) {
  const queryClient = useQueryClient()
  const isEditing = !!employee

  const [formData, setFormData] = useState({
    // User fields
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    password: '',
    // Employee fields
    branch_id: '',
    position: '',
    department: '',
    employment_type: 'full_time',
    hire_date: new Date().toISOString().split('T')[0],
    salary: '',
    hourly_rate: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    address: '',
    tax_id: '',
    social_security_number: '',
    notes: '',
    status: 'active',
  })

  // Reset form when modal opens/closes or employee changes
  useEffect(() => {
    if (employee) {
      setFormData({
        email: employee.user.email,
        first_name: employee.user.first_name,
        last_name: employee.user.last_name,
        phone: employee.user.phone || '',
        password: '',
        branch_id: String(employee.branch.id),
        position: employee.position,
        department: employee.department || '',
        employment_type: employee.employment_type,
        hire_date: employee.hire_date,
        salary: employee.salary ? String(employee.salary) : '',
        hourly_rate: employee.hourly_rate ? String(employee.hourly_rate) : '',
        emergency_contact_name: employee.emergency_contact_name || '',
        emergency_contact_phone: employee.emergency_contact_phone || '',
        address: employee.address || '',
        tax_id: employee.tax_id || '',
        social_security_number: employee.social_security_number || '',
        notes: employee.notes || '',
        status: employee.status,
      })
    } else {
      setFormData({
        email: '',
        first_name: '',
        last_name: '',
        phone: '',
        password: '',
        branch_id: '',
        position: '',
        department: '',
        employment_type: 'full_time',
        hire_date: new Date().toISOString().split('T')[0],
        salary: '',
        hourly_rate: '',
        emergency_contact_name: '',
        emergency_contact_phone: '',
        address: '',
        tax_id: '',
        social_security_number: '',
        notes: '',
        status: 'active',
      })
    }
  }, [employee, isOpen])

  const createMutation = useMutation({
    mutationFn: employeesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      toast.success('Empleado creado correctamente')
      onClose()
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || error.response?.data?.error || 'Error al crear el empleado'
      toast.error(message)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateEmployeeRequest }) =>
      employeesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      toast.success('Empleado actualizado correctamente')
      onClose()
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || error.response?.data?.error || 'Error al actualizar el empleado'
      toast.error(message)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (isEditing && employee) {
      const updateData: UpdateEmployeeRequest = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone || undefined,
        branch: Number(formData.branch_id),
        position: formData.position,
        department: formData.department || undefined,
        employment_type: formData.employment_type as any,
        status: formData.status as any,
        salary: formData.salary ? Number(formData.salary) : undefined,
        hourly_rate: formData.hourly_rate ? Number(formData.hourly_rate) : undefined,
        emergency_contact_name: formData.emergency_contact_name || undefined,
        emergency_contact_phone: formData.emergency_contact_phone || undefined,
        address: formData.address || undefined,
        tax_id: formData.tax_id || undefined,
        social_security_number: formData.social_security_number || undefined,
        notes: formData.notes || undefined,
      }
      updateMutation.mutate({ id: employee.id, data: updateData })
    } else {
      const createData: CreateEmployeeRequest = {
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone || undefined,
        password: formData.password,
        branch_id: Number(formData.branch_id),
        position: formData.position,
        department: formData.department || undefined,
        employment_type: formData.employment_type as any,
        hire_date: formData.hire_date,
        salary: formData.salary ? Number(formData.salary) : undefined,
        hourly_rate: formData.hourly_rate ? Number(formData.hourly_rate) : undefined,
        emergency_contact_name: formData.emergency_contact_name || undefined,
        emergency_contact_phone: formData.emergency_contact_phone || undefined,
        address: formData.address || undefined,
        tax_id: formData.tax_id || undefined,
        social_security_number: formData.social_security_number || undefined,
        notes: formData.notes || undefined,
      }
      createMutation.mutate(createData)
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Editar Empleado' : 'Nuevo Empleado'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* User Information Section */}
        <div>
          <h3 className="text-sm font-semibold text-secondary-700 mb-3 flex items-center gap-2">
            <UserCheck className="w-4 h-4" />
            Información Personal
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Nombre"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              required
            />
            <Input
              label="Apellido"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <Input
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              disabled={isEditing}
            />
            <Input
              label="Teléfono"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>
          {!isEditing && (
            <div className="mt-4">
              <Input
                label="Contraseña"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                minLength={8}
                placeholder="Mínimo 8 caracteres"
              />
            </div>
          )}
        </div>

        {/* Employment Information Section */}
        <div>
          <h3 className="text-sm font-semibold text-secondary-700 mb-3 flex items-center gap-2">
            <Building2 className="w-4 h-4" />
            Información Laboral
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Sucursal"
              options={branches.map((b) => ({ value: String(b.id), label: b.name }))}
              value={formData.branch_id}
              onChange={(e) => setFormData({ ...formData, branch_id: e.target.value })}
              placeholder="Seleccionar sucursal"
              required
            />
            <Input
              label="Puesto"
              value={formData.position}
              onChange={(e) => setFormData({ ...formData, position: e.target.value })}
              required
              placeholder="ej: Vendedor, Cajero, Gerente"
            />
          </div>
          <div className="grid grid-cols-3 gap-4 mt-4">
            <Input
              label="Departamento"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              placeholder="Opcional"
            />
            <Select
              label="Tipo de empleo"
              options={EMPLOYMENT_TYPE_OPTIONS}
              value={formData.employment_type}
              onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
            />
            <Input
              label="Fecha de contratación"
              type="date"
              value={formData.hire_date}
              onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
              required
            />
          </div>
          {isEditing && (
            <div className="mt-4">
              <Select
                label="Estado"
                options={STATUS_OPTIONS}
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              />
            </div>
          )}
        </div>

        {/* Compensation Section */}
        <div>
          <h3 className="text-sm font-semibold text-secondary-700 mb-3 flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Compensación
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Salario mensual"
              type="number"
              step="0.01"
              value={formData.salary}
              onChange={(e) => setFormData({ ...formData, salary: e.target.value })}
              placeholder="0.00"
            />
            <Input
              label="Tarifa por hora"
              type="number"
              step="0.01"
              value={formData.hourly_rate}
              onChange={(e) => setFormData({ ...formData, hourly_rate: e.target.value })}
              placeholder="0.00"
            />
          </div>
        </div>

        {/* Emergency Contact Section */}
        <div>
          <h3 className="text-sm font-semibold text-secondary-700 mb-3 flex items-center gap-2">
            <Phone className="w-4 h-4" />
            Contacto de Emergencia
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Nombre del contacto"
              value={formData.emergency_contact_name}
              onChange={(e) => setFormData({ ...formData, emergency_contact_name: e.target.value })}
            />
            <Input
              label="Teléfono de emergencia"
              value={formData.emergency_contact_phone}
              onChange={(e) => setFormData({ ...formData, emergency_contact_phone: e.target.value })}
            />
          </div>
        </div>

        {/* Additional Information Section */}
        <div>
          <h3 className="text-sm font-semibold text-secondary-700 mb-3">
            Información Adicional
          </h3>
          <div className="space-y-4">
            <Input
              label="Dirección"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="RFC/CURP"
                value={formData.tax_id}
                onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
              />
              <Input
                label="Número de Seguro Social"
                value={formData.social_security_number}
                onChange={(e) => setFormData({ ...formData, social_security_number: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Notas
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                placeholder="Notas adicionales sobre el empleado..."
              />
            </div>
          </div>
        </div>

        <ModalFooter>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={isLoading}>
            {isEditing ? 'Guardar cambios' : 'Crear empleado'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}
