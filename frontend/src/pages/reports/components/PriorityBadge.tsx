import { ReportPriority, PRIORITY_CONFIG } from '@/api/userReports'

interface PriorityBadgeProps {
  priority: ReportPriority
}

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  const config = PRIORITY_CONFIG[priority]

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.color}`}
    >
      {config.label}
    </span>
  )
}
