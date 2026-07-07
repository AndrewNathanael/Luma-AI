import type { ReactNode } from 'react'
import { clsx } from 'clsx'

type BadgeTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

type BadgeProps = {
  children: ReactNode
  tone?: BadgeTone
}

const toneClass: Record<BadgeTone, string> = {
  neutral: 'border-white/15 bg-white/10 text-[#94a3b8]',
  info: 'border-sky-400/25 bg-sky-400/10 text-sky-100',
  success: 'border-[#8affc4]/25 bg-[#8affc4]/10 text-[#b8ffd9]',
  warning: 'border-orange-400/30 bg-orange-400/10 text-orange-100',
  danger: 'border-[#fb7185]/25 bg-[#fb7185]/10 text-[#fecdd3]',
}

export function Badge({ children, tone = 'neutral' }: BadgeProps) {
  return (
    <span className={clsx('inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold', toneClass[tone])}>
      {children}
    </span>
  )
}
