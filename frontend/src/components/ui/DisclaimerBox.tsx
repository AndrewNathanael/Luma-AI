import type { ReactNode } from 'react'

type DisclaimerBoxProps = {
  children: ReactNode
}

export function DisclaimerBox({ children }: DisclaimerBoxProps) {
  return (
    <div className="lp-disclaimer" role="note">
      {children}
    </div>
  )
}
