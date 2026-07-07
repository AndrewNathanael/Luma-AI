import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { clsx } from 'clsx'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  variant?: ButtonVariant
  size?: ButtonSize
}

const variantClass: Record<ButtonVariant, string> = {
  primary: 'bg-[#8affc4] text-[#020617] shadow-[0_8px_22px_rgba(138,255,196,0.2)] hover:bg-[#b8ffd9] focus-visible:ring-[#8affc4]',
  secondary:
    'border border-white/15 bg-white/10 text-white backdrop-blur-[20px] hover:border-white/25 hover:bg-white/15 focus-visible:ring-[#8affc4]',
  ghost: 'text-[#94a3b8] hover:bg-white/10 hover:text-white focus-visible:ring-[#8affc4]',
  danger: 'bg-[#fb7185] text-[#0a0a0a] shadow-[0_0_24px_rgba(251,113,133,0.18)] hover:bg-[#fda4af] focus-visible:ring-[#fb7185]',
}

const sizeClass: Record<ButtonSize, string> = {
  sm: 'min-h-9 px-3 text-sm',
  md: 'min-h-11 px-4 text-sm',
  lg: 'min-h-12 px-6 text-base',
}

export function Button({ children, className, size = 'md', type = 'button', variant = 'primary', ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center rounded-xl font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0a0a] disabled:cursor-not-allowed disabled:opacity-55',
        variantClass[variant],
        sizeClass[size],
        className,
      )}
      type={type}
      {...props}
    >
      {children}
    </button>
  )
}
