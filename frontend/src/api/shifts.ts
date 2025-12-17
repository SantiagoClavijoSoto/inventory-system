import { apiClient } from './client'

// Types
export interface Shift {
  id: number
  employee: number
  employee_name: string
  branch: number
  branch_name: string
  clock_in: string
  clock_out: string | null
  break_start: string | null
  break_end: string | null
  total_hours: number | null
  break_hours: number
  worked_hours: number | null
  notes: string
  is_manual_entry: boolean
  adjusted_by: number | null
  is_complete: boolean
  created_at: string
}

export interface ShiftSummary {
  date: string
  total_employees: number
  total_hours: number
  shifts_count: number
}

export interface ClockInParams {
  branch_id?: number
}

export interface ClockOutParams {
  notes?: string
}

export interface ShiftFilters {
  branch?: number
  employee?: number
  date_from?: string
  date_to?: string
  is_complete?: boolean
}

// Shift status helpers
export type ShiftStatus = 'not_clocked_in' | 'working' | 'on_break' | 'clocked_out'

export function getShiftStatus(shift: Shift | null): ShiftStatus {
  if (!shift) return 'not_clocked_in'
  if (shift.clock_out) return 'clocked_out'
  if (shift.break_start && !shift.break_end) return 'on_break'
  return 'working'
}

export function getShiftStatusLabel(status: ShiftStatus): string {
  const labels: Record<ShiftStatus, string> = {
    not_clocked_in: 'Sin marcar',
    working: 'Trabajando',
    on_break: 'En almuerzo',
    clocked_out: 'Turno cerrado',
  }
  return labels[status]
}

export function getShiftStatusColor(status: ShiftStatus): string {
  const colors: Record<ShiftStatus, string> = {
    not_clocked_in: 'bg-gray-100 text-gray-800',
    working: 'bg-green-100 text-green-800',
    on_break: 'bg-yellow-100 text-yellow-800',
    clocked_out: 'bg-blue-100 text-blue-800',
  }
  return colors[status]
}

// API Functions
export const shiftsApi = {
  // Get current user's active shift
  getCurrent: async (): Promise<Shift | null> => {
    const response = await apiClient.get('/shifts/current/')
    return response.data // Returns null if no active shift (200 OK with null body)
  },

  // List shifts with filters (handles paginated response)
  list: async (filters?: ShiftFilters): Promise<Shift[]> => {
    const response = await apiClient.get('/shifts/', { params: filters })
    // Handle paginated response
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results
    }
    // Fallback if response is already an array
    return Array.isArray(response.data) ? response.data : []
  },

  // Clock in
  clockIn: async (params?: ClockInParams): Promise<Shift> => {
    const response = await apiClient.post('/shifts/clock_in/', params || {})
    return response.data
  },

  // Clock out
  clockOut: async (params?: ClockOutParams): Promise<Shift> => {
    const response = await apiClient.post('/shifts/clock_out/', params || {})
    return response.data
  },

  // Start break (lunch)
  startBreak: async (): Promise<Shift> => {
    const response = await apiClient.post('/shifts/start_break/')
    return response.data
  },

  // End break (lunch)
  endBreak: async (): Promise<Shift> => {
    const response = await apiClient.post('/shifts/end_break/')
    return response.data
  },

  // Get daily summary for a branch
  getDailySummary: async (branchId?: number, date?: string): Promise<ShiftSummary> => {
    const response = await apiClient.get('/shifts/daily_summary/', {
      params: { branch: branchId, date },
    })
    return response.data
  },

  // Get employee shifts history
  getEmployeeShifts: async (
    employeeId: number,
    dateFrom?: string,
    dateTo?: string
  ): Promise<Shift[]> => {
    const response = await apiClient.get(`/employees/${employeeId}/shifts/`, {
      params: { date_from: dateFrom, date_to: dateTo },
    })
    return response.data
  },
}
