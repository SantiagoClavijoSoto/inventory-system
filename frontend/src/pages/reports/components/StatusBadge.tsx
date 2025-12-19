import { ReportStatus, STATUS_CONFIG } from '@/api/userReports'

interface StatusBadgeProps {
  status: ReportStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status]

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.color}`}
    >
      {config.label}
    </span>
  )
}
