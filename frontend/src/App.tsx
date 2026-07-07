import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'

import { HomePage } from './pages/HomePage'
import { MeasurementPage } from './pages/MeasurementPage'

type AppRoute = 'home' | 'measurement'

const validRoutes: AppRoute[] = ['home', 'measurement']

function getRouteFromHash(): AppRoute {
  const hash = window.location.hash.replace('#', '')
  return validRoutes.includes(hash as AppRoute) ? (hash as AppRoute) : 'home'
}

function App() {
  const [route, setRoute] = useState<AppRoute>(() => getRouteFromHash())
  const [isTransitioning, setIsTransitioning] = useState(false)
  const contentWrapperRef = useRef<HTMLDivElement>(null)

  const navigate = (nextRoute: AppRoute) => {
    if (isTransitioning || route === nextRoute) return
    setIsTransitioning(true)

    const tl = gsap.timeline({
      onComplete: () => {
        setIsTransitioning(false)
      }
    })

    // 1. Fade out and slide up leaving page
    tl.to(contentWrapperRef.current, {
      opacity: 0,
      y: -12,
      duration: 0.22,
      ease: 'power2.in'
    })
    // 2. Swap the route
    .call(() => {
      setRoute(nextRoute)
      window.location.hash = nextRoute
    })
    // 3. Set new page initial position (faded out, shifted down slightly)
    .set(contentWrapperRef.current, {
      opacity: 0,
      y: 12
    })
    // 4. Fade in and slide up to center entering page
    .to(contentWrapperRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.32,
      ease: 'power3.out'
    })
  }

  useEffect(() => {
    const handleHashChange = () => {
      const nextRoute = getRouteFromHash()
      if (nextRoute !== route) {
        navigate(nextRoute)
      }
    }
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [route])

  return (
    <div className="relative w-full min-h-screen bg-[#0a0f1d] text-white">
      <div 
        ref={contentWrapperRef} 
        className="w-full will-change-transform-opacity"
      >
        {route === 'measurement' ? (
          <MeasurementPage onBack={() => navigate('home')} />
        ) : (
          <HomePage onStart={() => navigate('measurement')} />
        )}
      </div>
    </div>
  )
}

export default App
