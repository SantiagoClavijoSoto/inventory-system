import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore, useIsPlatformAdmin } from '@/store/authStore'
import {
  shiftsApi,
  getShiftStatus,
  getShiftStatusLabel,
  getShiftStatusColor,
  type Shift,
  type ShiftStatus,
} from '@/api/shifts'
import { branchesApi } from '@/api/branches'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Select,
  Badge,
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  Spinner,
} from '@/components/ui'
import {
  Clock,
  LogIn,
  LogOut,
  Coffee,
  PlayCircle,
  Users,
  Calendar,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { extractErrorMessage } from '@/utils/errorSanitizer'

function formatTime(dateString: string | null): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleTimeString('es-CO', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('es-CO', {
    weekday: 'short',
    day: '2-digit',
    month: '2-digit',
  })
}

function formatHours(hours: number | string | null | undefined): string {
  if (hours === null || hours === undefined) return '-'
  const numHours = typeof hours === 'string' ? parseFloat(hours) : hours
  if (isNaN(numHours)) return '-'
  const totalMinutes = Math.round(numHours * 60)
  const h = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  return `${h}:${m.toString().padStart(2, '0')}`
}

function getWeekDateRange(): { dateFrom: string; dateTo: string } {
  const today = new Date()
  const dayOfWeek = today.getDay()
  const monday = new Date(today)
  monday.setDate(today.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1))

  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)

  return {
    dateFrom: monday.toISOString().split('T')[0],
    dateTo: sunday.toISOString().split('T')[0],
  }
}

// Current Shift Card Component
function CurrentShiftCard() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()

  const { data: currentShift, isLoading } = useQuery({
    queryKey: ['current-shift'],
    queryFn: shiftsApi.getCurrent,
    refetchInterval: 60000, // Refresh every minute
  })

  const clockInMutation = useMutation({
    mutationFn: shiftsApi.clockIn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-shift'] })
      queryClient.invalidateQueries({ queryKey: ['shifts'] })
      queryClient.invalidateQueries({ queryKey: ['my-shifts'] })
      toast.success('Entrada registrada correctamente')
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error))
    },
  })

  const clockOutMutation = useMutation({
    mutationFn: shiftsApi.clockOut,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-shift'] })
      queryClient.invalidateQueries({ queryKey: ['shifts'] })
      queryClient.invalidateQueries({ queryKey: ['my-shifts'] })
      toast.success('Salida registrada correctamente')
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error))
    },
  })

  const startBreakMutation = useMutation({
    mutationFn: shiftsApi.startBreak,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-shift'] })
      queryClient.invalidateQueries({ queryKey: ['shifts'] })
      queryClient.invalidateQueries({ queryKey: ['my-shifts'] })
      toast.success('Salida a almuerzo registrada')
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error))
    },
  })

  const endBreakMutation = useMutation({
    mutationFn: shiftsApi.endBreak,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-shift'] })
      queryClient.invalidateQueries({ queryKey: ['shifts'] })
      queryClient.invalidateQueries({ queryKey: ['my-shifts'] })
      toast.success('Regreso de almuerzo registrado')
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error))
    },
  })

  const status = getShiftStatus(currentShift ?? null)
  const statusLabel = getShiftStatusLabel(status)
  const statusColor = getShiftStatusColor(status)

  const isLoading_any =
    clockInMutation.isPending ||
    clockOutMutation.isPending ||
    startBreakMutation.isPending ||
    endBreakMutation.isPending

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Mi Turno
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center py-8">
            <Spinner size="lg" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Mi Turno
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Status Display */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm text-secondary-500">Estado actual</p>
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
                {statusLabel}
              </span>
              {currentShift && (
                <span className="text-sm text-secondary-600">
                  desde {formatTime(currentShift.clock_in)}
                </span>
              )}
            </div>
          </div>
          {currentShift && currentShift.worked_hours !== null && (
            <div className="text-right">
              <p className="text-sm text-secondary-500">Horas trabajadas</p>
              <p className="text-2xl font-bold text-primary-600">
                {formatHours(currentShift.worked_hours)}
              </p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3">
          {/* Clock In Button */}
          <Button
            onClick={() => clockInMutation.mutate({ branch_id: user?.default_branch })}
            disabled={status !== 'not_clocked_in' || isLoading_any}
            variant={status === 'not_clocked_in' ? 'primary' : 'secondary'}
            className="flex-1 min-w-[120px]"
          >
            <LogIn className="w-4 h-4" />
            Entrada
          </Button>

          {/* Break Out Button */}
          <Button
            onClick={() => startBreakMutation.mutate()}
            disabled={status !== 'working' || isLoading_any}
            variant={status === 'working' ? 'outline' : 'secondary'}
            className="flex-1 min-w-[120px]"
          >
            <Coffee className="w-4 h-4" />
            Salida Almuerzo
          </Button>

          {/* Break Return Button */}
          <Button
            onClick={() => endBreakMutation.mutate()}
            disabled={status !== 'on_break' || isLoading_any}
            variant={status === 'on_break' ? 'primary' : 'secondary'}
            className="flex-1 min-w-[120px]"
          >
            <PlayCircle className="w-4 h-4" />
            Regreso Almuerzo
          </Button>

          {/* Clock Out Button */}
          <Button
            onClick={() => clockOutMutation.mutate({})}
            disabled={(status !== 'working' && status !== 'on_break') || isLoading_any}
            variant={status === 'working' || status === 'on_break' ? 'danger' : 'secondary'}
            className="flex-1 min-w-[120px]"
          >
            <LogOut className="w-4 h-4" />
            Salida
          </Button>
        </div>

        {/* Current Shift Details */}
        {currentShift && (
          <div className="pt-4 border-t border-secondary-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-secondary-500">Entrada</p>
                <p className="font-medium">{formatTime(currentShift.clock_in)}</p>
              </div>
              <div>
                <p className="text-secondary-500">Salida Almuerzo</p>
                <p className="font-medium">{formatTime(currentShift.break_start)}</p>
              </div>
              <div>
                <p className="text-secondary-500">Regreso Almuerzo</p>
                <p className="font-medium">{formatTime(currentShift.break_end)}</p>
              </div>
              <div>
                <p className="text-secondary-500">Salida</p>
                <p className="font-medium">{formatTime(currentShift.clock_out)}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Weekly History Table Component
function WeeklyHistoryTable() {
  const { user } = useAuthStore()
  const { dateFrom, dateTo } = useMemo(() => getWeekDateRange(), [])

  const { data: shifts, isLoading } = useQuery({
    queryKey: ['my-shifts', dateFrom, dateTo],
    queryFn: () =>
      shiftsApi.list({
        date_from: dateFrom,
        date_to: dateTo,
      }),
    enabled: !!user,
  })

  // Filter shifts for current user (by employee_name matching user's full_name)
  const myShifts = useMemo(() => {
    if (!shifts || !user) return []
    return shifts.filter((s) => s.employee_name === user.full_name)
  }, [shifts, user])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Mi Historial Semanal
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Spinner size="lg" />
          </div>
        ) : myShifts.length === 0 ? (
          <div className="text-center py-8 text-secondary-500">
            No hay registros esta semana
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Entrada</TableHead>
                  <TableHead>Sal. Almuerzo</TableHead>
                  <TableHead>Reg. Almuerzo</TableHead>
                  <TableHead>Salida</TableHead>
                  <TableHead className="text-right">Horas</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {myShifts.map((shift) => (
                  <TableRow key={shift.id}>
                    <TableCell className="font-medium">
                      {formatDate(shift.clock_in)}
                    </TableCell>
                    <TableCell>{formatTime(shift.clock_in)}</TableCell>
                    <TableCell>{formatTime(shift.break_start)}</TableCell>
                    <TableCell>{formatTime(shift.break_end)}</TableCell>
                    <TableCell>{formatTime(shift.clock_out)}</TableCell>
                    <TableCell className="text-right font-medium">
                      {formatHours(shift.worked_hours)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Employees Today Table Component (Admin/Supervisor only)
function EmployeesTodayTable({ branchId }: { branchId?: number }) {
  const today = new Date().toISOString().split('T')[0]

  const { data: shifts, isLoading } = useQuery({
    queryKey: ['branch-shifts-today', branchId, today],
    queryFn: () =>
      shiftsApi.list({
        branch: branchId,
        date_from: today,
        date_to: today,
      }),
    enabled: !!branchId,
  })

  const getStatusBadge = (shift: Shift) => {
    const status = getShiftStatus(shift)
    const statusConfig: Record<ShiftStatus, { variant: 'success' | 'warning' | 'secondary' | 'primary'; label: string }> = {
      working: { variant: 'success', label: 'Activo' },
      on_break: { variant: 'warning', label: 'Almuerzo' },
      clocked_out: { variant: 'secondary', label: 'Salida' },
      not_clocked_in: { variant: 'secondary', label: 'Sin marcar' },
    }
    const config = statusConfig[status]
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  // Calculate worked hours excluding lunch break
  const calculateWorkedHours = (shift: Shift): string => {
    if (shift.clock_out) {
      // Shift completed - use stored worked_hours (already excludes break)
      return formatHours(shift.worked_hours)
    }

    // Calculate running hours for active shifts
    const start = new Date(shift.clock_in)
    const now = new Date()
    let hours = (now.getTime() - start.getTime()) / 3600000

    if (shift.break_start && !shift.break_end) {
      // Currently on break - subtract time since break started
      const breakStart = new Date(shift.break_start)
      hours -= (now.getTime() - breakStart.getTime()) / 3600000
    } else if (shift.break_start && shift.break_end) {
      // Break completed - subtract break duration
      const breakStart = new Date(shift.break_start)
      const breakEnd = new Date(shift.break_end)
      hours -= (breakEnd.getTime() - breakStart.getTime()) / 3600000
    }

    return formatHours(Math.max(0, hours))
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5" />
          Empleados Hoy
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Spinner size="lg" />
          </div>
        ) : !shifts || shifts.length === 0 ? (
          <div className="text-center py-8 text-secondary-500">
            No hay registros de turnos hoy
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Empleado</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Entrada</TableHead>
                  <TableHead>Sal. Almuerzo</TableHead>
                  <TableHead>Reg. Almuerzo</TableHead>
                  <TableHead>Salida</TableHead>
                  <TableHead className="text-right">Horas</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shifts.map((shift) => (
                  <TableRow key={shift.id}>
                    <TableCell className="font-medium">
                      {shift.employee_name}
                    </TableCell>
                    <TableCell>{getStatusBadge(shift)}</TableCell>
                    <TableCell>{formatTime(shift.clock_in)}</TableCell>
                    <TableCell>{formatTime(shift.break_start)}</TableCell>
                    <TableCell>{formatTime(shift.break_end)}</TableCell>
                    <TableCell>{formatTime(shift.clock_out)}</TableCell>
                    <TableCell className="text-right font-medium">
                      <span className={shift.clock_out ? '' : 'text-secondary-400'}>
                        {calculateWorkedHours(shift)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Main Schedule Page
export function Schedule() {
  const { user, hasPermission } = useAuthStore()
  const isPlatformAdmin = useIsPlatformAdmin()
  const [selectedBranch, setSelectedBranch] = useState<number | undefined>(
    user?.default_branch || undefined
  )

  const { data: branches } = useQuery({
    queryKey: ['branches-simple'],
    queryFn: () => branchesApi.getSimple(),
  })

  // Check if user can view employee schedules (supervisors/admins)
  // Regular employees only see their own clock in/out interface
  const isAdmin = isPlatformAdmin || hasPermission('employees:view')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Horario</h1>
          <p className="text-secondary-500">
            {isAdmin
              ? 'Visualización de horarios de empleados'
              : 'Control de entrada, almuerzo y salida'}
          </p>
        </div>

        {/* Branch Selector (for admins) */}
        {isAdmin && branches && branches.length > 1 && (
          <Select
            options={[
              { value: '', label: 'Todas las sucursales' },
              ...branches.map((b) => ({ value: String(b.id), label: b.name })),
            ]}
            value={selectedBranch?.toString() || ''}
            onChange={(e) => setSelectedBranch(e.target.value ? Number(e.target.value) : undefined)}
            className="w-48"
          />
        )}
      </div>

      {isAdmin ? (
        /* Admin View: Only see employee schedules (no clock in/out) */
        <EmployeesTodayTable branchId={selectedBranch} />
      ) : (
        /* Employee View: Clock in/out functionality + personal history */
        <>
          <CurrentShiftCard />
          <WeeklyHistoryTable />
        </>
      )}
    </div>
  )
}
