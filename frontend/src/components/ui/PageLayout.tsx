import type { ReactNode } from 'react'

type PageLayoutProps = {
  children: ReactNode
  eyebrow?: string
  title: string
  description?: string
}

export function PageLayout({ children, description, eyebrow, title }: PageLayoutProps) {
  return (
    <main className="bento-page px-4 py-8 sm:px-6 lg:px-8">
      <div className="bento-shell">
        <header className="glass-panel relative mb-8 overflow-hidden rounded-[28px] px-5 py-8 text-center shadow-2xl md:rounded-[40px] md:px-10 md:py-12">
          <div className="bento-orbit" />
          {eyebrow ? <p className="bento-badge mx-auto">{eyebrow}</p> : null}
          <h1 className="mx-auto mt-5 max-w-4xl bg-gradient-to-b from-white via-white to-[#94a3b8] bg-clip-text text-4xl font-bold leading-tight text-transparent sm:text-5xl">
            {title}
          </h1>
          {description ? <p className="mx-auto mt-4 max-w-3xl text-base leading-7 text-[#94a3b8]">{description}</p> : null}
        </header>
        {children}
      </div>
    </main>
  )
}
