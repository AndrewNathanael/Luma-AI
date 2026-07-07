import { forwardRef, type HTMLAttributes, type ReactNode } from 'react'
import { clsx } from 'clsx'

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode
}

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card({ children, className, ...props }, ref) {
  return (
    <div className={clsx('bento-card p-5 md:p-6', className)} ref={ref} {...props}>
      {children}
    </div>
  )
})

