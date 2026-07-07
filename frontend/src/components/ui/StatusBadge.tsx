import { Badge } from './Badge'

type StatusTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

type StatusBadgeProps = {
  label: string
  value: string
  tone?: StatusTone
}

export function StatusBadge({ label, tone = 'neutral', value }: StatusBadgeProps) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
      <span className="text-sm text-[#94a3b8]">{label}</span>
      <Badge tone={tone}>{value}</Badge>
    </div>
  )
}
