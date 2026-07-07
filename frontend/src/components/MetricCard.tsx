import { clsx } from 'clsx'

type MetricCardProps = {
  label: string
  value: string
  helper?: string
  tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'info'
}

const toneClass: Record<NonNullable<MetricCardProps['tone']>, string> = {
  neutral: 'border-white/15 bg-white/10',
  success: 'border-[#8affc4]/25 bg-[#8affc4]/10',
  warning: 'border-orange-400/30 bg-orange-400/10',
  danger: 'border-[#fb7185]/25 bg-[#fb7185]/10',
  info: 'border-sky-400/25 bg-sky-400/10',
}

export function MetricCard({ helper, label, tone = 'neutral', value }: MetricCardProps) {
  return (
    <div
      className={clsx(
        'rounded-[20px] border p-4 shadow-[0_8px_32px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.28)] backdrop-blur-[20px]',
        toneClass[tone],
      )}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.08em] text-[#94a3b8]">{label}</p>
      <p className="mt-2 text-2xl font-bold text-white">{value}</p>
      {helper ? <p className="mt-1 text-xs leading-5 text-[#94a3b8]">{helper}</p> : null}
    </div>
  )
}
