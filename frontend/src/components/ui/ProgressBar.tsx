type ProgressBarProps = {
  value: number
  max?: number
  label?: string
}

export function ProgressBar({ label, max = 100, value }: ProgressBarProps) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100))

  return (
    <div aria-label={label} aria-valuemax={max} aria-valuemin={0} aria-valuenow={value} role="progressbar">
      <div className="h-3 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-[linear-gradient(90deg,#8affc4,#00a5ef,#4f39f6)] shadow-[0_0_18px_rgba(138,255,196,0.25)] transition-all duration-500" style={{ width: `${percent}%` }} />
      </div>
    </div>
  )
}
