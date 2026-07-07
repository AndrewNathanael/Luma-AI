import { useEffect, useState, useMemo } from 'react'

import { ArrowRight, Clock3, ShieldCheck, Sparkles, MessageSquare, Send, X, Heart, Film, User } from 'lucide-react'

import { Button } from '../components/ui/Button'
import lumaLogo from '../assets/Luma. logo.svg'
import reactLogo from '../assets/react.svg'
import viteLogo from '../assets/vite.svg'

// Import emoticon SVGs
import grinningFaceUrl from '../assets/emoticon/Grinning Face.svg'
import slightlySmilingFaceUrl from '../assets/emoticon/Slightly Smiling Face.svg'
import relievedFaceUrl from '../assets/emoticon/Relieved Face.svg'
import poutingFaceUrl from '../assets/emoticon/Pouting Face.svg'
import fearfulFaceUrl from '../assets/emoticon/Fearful Face.svg'

type HomePageProps = {
  onStart: () => void
}

/* ─── Data ─── */

const heroParticles = [
  { top: '12%', left: '7%' },
  { top: '25%', right: '10%' },
  { top: '55%', left: '15%' },
  { top: '70%', right: '18%' },
  { top: '38%', left: '80%' },
  { top: '82%', left: '42%' },
]

/* ─── Emoticon Image Elements ─── */
const happyEmoji = <img src={grinningFaceUrl} className="size-8" alt="Senang" />
const cheerfulEmoji = <img src={slightlySmilingFaceUrl} className="size-8" alt="Ceria" />
const relievedEmoji = <img src={relievedFaceUrl} className="size-8" alt="Rileks" />
const sadEmoji = <img src={fearfulFaceUrl} className="size-8" alt="Sedih" />
const angryEmoji = <img src={poutingFaceUrl} className="size-8" alt="Marah" />
const stressedEmoji = <img src={fearfulFaceUrl} className="size-8" alt="Stres" />

const moods = [
  { id: 'happy', label: 'Senang', stress: 18, hr: 68, stressLabel: 'Sangat Rendah (Rileks)', emoji: happyEmoji },
  { id: 'cheerful', label: 'Ceria', stress: 10, hr: 72, stressLabel: 'Normal (Tenang & Fokus)', emoji: cheerfulEmoji },
  { id: 'relieved', label: 'Rileks', stress: 25, hr: 65, stressLabel: 'Rendah (Tenang)', emoji: relievedEmoji },
  { id: 'sad', label: 'Sedih', stress: 52, hr: 62, stressLabel: 'Sedang (Kelelahan Ringan)', emoji: sadEmoji },
  { id: 'angry', label: 'Marah', stress: 78, hr: 88, stressLabel: 'Tinggi (Sinyal Agitasi)', emoji: angryEmoji },
  { id: 'stressed', label: 'Stres', stress: 92, hr: 95, stressLabel: 'Sangat Tinggi (Stres Akut)', emoji: stressedEmoji },
]


/* ═══════════════════════════════════════════
   COMPONENT
   ═══════════════════════════════════════════ */
export function HomePage({ onStart }: HomePageProps) {
  const [navHidden, setNavHidden] = useState(false)
  const [navScrolled, setNavScrolled] = useState(false)
  const [introActive, setIntroActive] = useState(true)
  const [introRendered, setIntroRendered] = useState(true)
  const [contentVisible, setContentVisible] = useState(false)
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState([
    { id: 1, text: "Halo! Saya Luma Assistant. Ada yang bisa saya bantu terkait monitoring tingkat stres atau teknologi rPPG?", sender: 'bot', time: '01:21' }
  ])
  const [chatInput, setChatInput] = useState("")

  const [hoverStyle, setHoverStyle] = useState<React.CSSProperties>({
    opacity: 0,
    transform: 'translateY(-50%) scale(0.9)',
  })

  const handleMouseEnterLink = (e: React.MouseEvent<HTMLAnchorElement>) => {
    const link = e.currentTarget
    const parent = link.parentElement
    if (parent) {
      const linkRect = link.getBoundingClientRect()
      const parentRect = parent.getBoundingClientRect()
      
      setHoverStyle({
        opacity: 1,
        left: `${linkRect.left - parentRect.left}px`,
        width: `${linkRect.width}px`,
        height: `${linkRect.height}px`,
        transform: 'translateY(-50%) scale(1)',
      })
    }
  }

  const handleMouseLeaveLink = () => {
    setHoverStyle(prev => ({
      ...prev,
      opacity: 0,
      transform: 'translateY(-50%) scale(0.9)',
    }))
  }

  // Demo Interaktif States
  const [demoTab, setDemoTab] = useState<'demo' | 'video' | 'visuals'>('demo')
  const [demoScanning, setDemoScanning] = useState(false)
  const [demoProgress, setDemoProgress] = useState(0)
  const [demoFinished, setDemoFinished] = useState(false)
  const [demoHeartRate, setDemoHeartRate] = useState(72)
  const [demoStress, setDemoStress] = useState<number | null>(null)
  const [demoStressLabel, setDemoStressLabel] = useState<string>("Rendah (Rileks)")

  const selectMood = (stress: number, hr: number, stressLabel: string) => {
    setDemoScanning(false)
    setDemoFinished(true)
    setDemoStress(stress)
    setDemoHeartRate(hr)
    setDemoStressLabel(stressLabel)
    setDemoTab('visuals') // switch directly to Tab 3 (Hasil Laporan)
  }

  const startDemoSimulation = () => {
    if (demoScanning) return
    setDemoTab('demo') // ensure we are on Tab 1 during scanning
    setDemoScanning(true)
    setDemoProgress(0)
    setDemoFinished(false)
    setDemoStress(null)
    setDemoStressLabel("Mengukur...")
    
    let currentProgress = 0
    const interval = setInterval(() => {
      currentProgress += 5
      setDemoProgress(currentProgress)
      
      setDemoHeartRate(Math.floor(Math.random() * 8) + 68)
      
      if (currentProgress >= 100) {
        clearInterval(interval)
        setDemoScanning(false)
        setDemoFinished(true)
        setDemoStress(34)
        setDemoStressLabel("Rendah (Rileks)")
        setDemoTab('visuals') // transition to Tab 3 (Visuals / Laporan) when finished
      }
    }, 150)
  }

  const presenterSubtitle = useMemo(() => {
    if (demoTab === 'demo') {
      if (demoScanning) {
        return "Scanning face... rPPG extracts blood volume changes from skin reflections to estimate stress levels in real-time."
      }
      if (demoFinished) {
        return "Scan complete! Let's explore the final stress report and physiological metrics computed from HRV."
      }
      return "Discover Figma's Dev Mode and learn how to export code for smooth teamwork and"
    }
    if (demoTab === 'video') {
      return "rPPG splits the raw webcam video feed into Red, Green, and Blue color channels to isolate blood volume changes."
    }
    if (demoTab === 'visuals') {
      return "The final dashboard displays stress index (34% - Low Stress) alongside physiological metrics SDNN (56ms) and RMSSD (48ms)."
    }
    return ""
  }, [demoTab, demoScanning, demoFinished])

  const handleSendChat = (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim()) return
    
    const userMsg = {
      id: Date.now(),
      text: chatInput,
      sender: 'user',
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
    }
    
    setChatMessages(prev => [...prev, userMsg])
    setChatInput("")
    
    setTimeout(() => {
      let botResponse = "Terima kasih! Tim kami sedang online dan akan segera membalas pertanyaan Anda."
      const lower = userMsg.text.toLowerCase()
      if (lower.includes("rppg") || lower.includes("cara")) {
        botResponse = "Teknologi rPPG bekerja dengan mendeteksi perubahan mikro pada warna kulit wajah akibat aliran darah setiap detak jantung, menggunakan kamera standar."
      } else if (lower.includes("stres") || lower.includes("stress")) {
        botResponse = "Kami mengestimasi tingkat stres berdasarkan variabilitas detak jantung (HRV) yang dihitung dari sinyal rPPG selama sesi pengukuran 30 detik."
      } else if (lower.includes("harga") || lower.includes("bayar") || lower.includes("gratis")) {
        botResponse = "Luma Vulse saat ini dapat dicoba secara gratis untuk kepentingan riset akademis dan demonstrasi teknologi."
      }
      
      setChatMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: botResponse,
        sender: 'bot',
        time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
      }])
    }, 1000)
  }

  // Generate random stars once
  const stars = useMemo(() => {
    const starList = []
    for (let i = 0; i < 120; i++) {
      const top = Math.random() * 100
      const left = Math.random() * 100
      const size = Math.random() * 1.5 + 0.4 // size between 0.4px and 1.9px
      const opacity = Math.random() * 0.6 + 0.3 // initial opacity
      const duration = Math.random() * 5 + 3 // twinkle duration between 3s and 8s
      const delay = Math.random() * 5 // animation delay
      starList.push({
        id: i,
        top: `${top}%`,
        left: `${left}%`,
        size,
        opacity,
        duration: `${duration}s`,
        delay: `${delay}s`
      })
    }
    return starList
  }, [])

  const handleSmoothScroll = (e: React.MouseEvent<HTMLButtonElement | HTMLAnchorElement>, targetId: string) => {
    e.preventDefault()
    const targetElement = document.getElementById(targetId)
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: 'smooth' })
    }
  }

  // page load intro timing & scroll-to-top
  useEffect(() => {
    // Force browser to scroll to top on reload
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual'
    }
    window.scrollTo(0, 0)

    const timerIntro = setTimeout(() => {
      setIntroActive(false)
    }, 1200)

    const timerContent = setTimeout(() => {
      setContentVisible(true)
    }, 1400)

    const timerUnmount = setTimeout(() => {
      setIntroRendered(false)
    }, 2200)

    return () => {
      clearTimeout(timerIntro)
      clearTimeout(timerContent)
      clearTimeout(timerUnmount)
    }
  }, [])

  // hide nav on scroll down (optimized with requestAnimationFrame for maximum smoothness)
  useEffect(() => {
    let prevY = window.scrollY
    let accumulatedDelta = 0
    const threshold = 15 // scroll delta threshold in pixels to prevent flickering
    let ticking = false

    const updateScroll = () => {
      const y = window.scrollY
      const delta = y - prevY

      // Only set state if value changes to avoid unnecessary React re-renders
      const shouldScroll = y > 50
      setNavScrolled(prev => (prev !== shouldScroll ? shouldScroll : prev))

      if (y <= 10) {
        setNavHidden(prev => (prev !== false ? false : prev))
        accumulatedDelta = 0
      } else if (delta > 0) {
        // Scrolling down
        if (accumulatedDelta < 0) accumulatedDelta = 0
        accumulatedDelta += delta
        if (accumulatedDelta > threshold && y > 64) {
          setNavHidden(prev => (prev !== true ? true : prev))
        }
      } else if (delta < 0) {
        // Scrolling up
        if (accumulatedDelta > 0) accumulatedDelta = 0
        accumulatedDelta += delta
        if (Math.abs(accumulatedDelta) > threshold) {
          setNavHidden(prev => (prev !== false ? false : prev))
        }
      }
      prevY = y
      ticking = false
    }

    const handler = () => {
      if (!ticking) {
        window.requestAnimationFrame(updateScroll)
        ticking = true
      }
    }

    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  // interactive mouse-glow tracking
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      document.documentElement.style.setProperty('--mouse-x', `${e.clientX}px`)
      document.documentElement.style.setProperty('--mouse-y', `${e.clientY}px`)
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  // Intersection Observer for scroll reveal elements (.sr)
  useEffect(() => {
    if (!contentVisible) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
          }
        })
      },
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    )

    const srElements = document.querySelectorAll('.sr')
    srElements.forEach((el) => observer.observe(el))

    return () => {
      srElements.forEach((el) => observer.unobserve(el))
    }
  }, [contentVisible])

  return (
    <main className="lp-page" id="top">
      <div aria-hidden="true" className="lp-ambient">
        <div className="lp-ambient-blob lp-blob-1" />
        <div className="lp-ambient-blob lp-blob-2" />
        <div className="lp-ambient-blob lp-blob-3" />
      </div>
      <div aria-hidden="true" className="lp-cursor-glow" />

      {/* 🌌 Starry Background */}
      <div aria-hidden="true" className="lp-stars">
        {stars.map((star) => (
          <div
            key={star.id}
            className="lp-star"
            style={{
              top: star.top,
              left: star.left,
              width: `${star.size}px`,
              height: `${star.size}px`,
              opacity: star.opacity,
              animation: `lp-twinkle ${star.duration} infinite ease-in-out`,
              animationDelay: star.delay,
              boxShadow: star.size > 1.2 ? '0 0 4px rgba(255, 255, 255, 0.8)' : 'none'
            }}
          />
        ))}
      </div>

      {/* ═══ INTRO CURTAIN LOADER ═══ */}
      {introRendered && (
        <div className={`lp-intro-curtain ${!introActive ? 'lp-intro-curtain-hidden' : ''}`}>
          <div className="lp-intro-center">
            <div className="flex items-center justify-center">
              <img className="h-16 w-auto object-contain" src={lumaLogo} alt="Luma Logo" />
            </div>
            <h2 className="lp-intro-title font-semibold tracking-wider text-white mt-6 text-xs">By APF Dev.</h2>
            <span className="lp-intro-subtitle mt-2 text-[9px] uppercase tracking-[0.2em] text-[#7dddb2]">Physiological Stress Monitor</span>
          </div>
        </div>
      )}

      <header className={`lp-nav ${navHidden ? 'lp-nav-hidden' : ''} ${contentVisible ? 'lp-revealed' : ''} ${navScrolled ? 'lp-nav-scrolled' : ''}`}>
        <div className="lp-nav-inner flex items-center justify-between gap-4 w-full">
          {/* Left: Brand Logo */}
          <div className="flex items-center gap-2.5">
            <div className="lp-nav-logo-container relative flex items-center">
              <img className="h-9 w-auto object-contain" src={lumaLogo} alt="Luma Logo" />
            </div>
          </div>

          {/* Center: Nav links */}
          <nav className="hidden md:flex items-center gap-2 relative py-1 px-1">
            <div className="lp-nav-hover-backdrop" style={hoverStyle} />
            <a 
              href="#about" 
              onClick={(e) => handleSmoothScroll(e, 'about')} 
              onMouseEnter={handleMouseEnterLink}
              onMouseLeave={handleMouseLeaveLink}
              className="lp-nav-link text-xs font-semibold uppercase tracking-wider text-[#9eb0c5] hover:text-white transition-colors relative px-3 py-1.5"
            >
              Tim Kami
            </a>
            <a 
              href="#" 
              onMouseEnter={handleMouseEnterLink}
              onMouseLeave={handleMouseLeaveLink}
              className="lp-nav-link text-xs font-semibold uppercase tracking-wider text-[#9eb0c5] hover:text-white transition-colors relative px-3 py-1.5"
            >
              Teknologi
            </a>
            <a 
              href="#" 
              onMouseEnter={handleMouseEnterLink}
              onMouseLeave={handleMouseLeaveLink}
              className="lp-nav-link text-xs font-semibold uppercase tracking-wider text-[#9eb0c5] hover:text-white transition-colors relative px-3 py-1.5"
            >
              Validasi
            </a>
          </nav>

          {/* Right: Quick Action CTA */}
          <div className="flex items-center gap-4">
            <Button className="btn-shimmer text-xs px-4 min-h-9" onClick={onStart} size="sm">
              Mulai Sesi
            </Button>
          </div>
        </div>
      </header>

      {/* 🌌 Combined Hero & Demo Section */}
      <section className="lp-hero-demo-combined-section relative overflow-hidden">
        <div className="lp-cloud-grid" aria-hidden="true" />
        <div className="lp-cloud-glow-hard" aria-hidden="true" />
        <div className="lp-cloud-glow-soft" aria-hidden="true" />
        <div className="lp-hero-orbit" aria-hidden="true" />
        <div className="lp-hero-beam lp-hero-beam-a" aria-hidden="true" />
        <div className="lp-hero-beam lp-hero-beam-b" aria-hidden="true" />

        {/* ═══ HERO CONTENT ═══ */}
        <div className="lp-hero">

        <div className="lp-particles" aria-hidden="true">
          {heroParticles.map((pos, i) => (
            <div className="lp-particle" key={i} style={pos} />
          ))}
        </div>

        <div className="lp-shell lp-hero-content relative">
          <div className="lp-title-container relative w-full flex flex-col items-center">
            <span className={`lp-badge lp-reveal-item ${contentVisible ? 'lp-revealed' : ''}`} style={{ transitionDelay: '0.2s' }}>Physiological Stress Estimation</span>

            <h1 className={`lp-hero-title lp-reveal-item ${contentVisible ? 'lp-revealed' : ''}`} style={{ position: 'relative', transitionDelay: '0.3s' }}>
              Transformasi video wajah menjadi insight kesehatan mental yang bermakna.
            </h1>

            <p className={`lp-hero-sub lp-reveal-item ${contentVisible ? 'lp-revealed' : ''}`} style={{ transitionDelay: '0.4s' }}>
              Dirancang dengan fondasi akademik yang kuat dan pengalaman pengguna yang modern, menghadirkan perjalanan analisis stres yang seamless dalam setiap interaksi.
            </p>

            {/* Floating Tech Flow Cards (Desktop only) placed in their absolute centered anchor */}
            <div className="lp-logos-container">
              {/* Python Card */}
              <div className={`lp-tech-card-floating lp-tc-python ${contentVisible ? 'lp-card-revealed' : ''}`} title="Python Backend Pipeline">
                <img className="size-12 object-contain" src="https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg" alt="Python Logo" />
              </div>

              {/* UBFC-Phys Card */}
              <div className={`lp-tech-card-floating lp-tc-ubfc ${contentVisible ? 'lp-card-revealed' : ''}`} title="UBFC-Phys Dataset Integration">
                <img className="size-16 object-contain" src="https://ieeexplore.ieee.org/assets/img/ieee_logo_white.svg" alt="UBFC IEEE Logo" />
              </div>

              {/* Vite Card */}
              <div className={`lp-tech-card-floating lp-tc-vite ${contentVisible ? 'lp-card-revealed' : ''}`} title="Vite Frontend Build System">
                <img className="size-12 object-contain" src="/favicon.svg" alt="Vite Logo" />
              </div>

              {/* React Card */}
              <div className={`lp-tech-card-floating lp-tc-react ${contentVisible ? 'lp-card-revealed' : ''}`} title="React Modern Interface">
                <img className="size-16 object-contain" src="https://upload.wikimedia.org/wikipedia/commons/a/a7/React-icon.svg" alt="React Logo" />
              </div>
            </div>
          </div>

          {/* Fallback Mobile Tech Stack Row */}
          <div className={`flex lg:hidden flex-wrap justify-center items-center gap-2 mt-2 py-1 px-3 rounded-full border border-white/5 bg-white/5 backdrop-blur-sm max-w-sm mx-auto lp-reveal-fade-item ${contentVisible ? 'lp-revealed' : ''}`} style={{ transitionDelay: '0.55s' }}>
            <span className="text-[10px] uppercase font-semibold text-white/50 tracking-wider mr-1">Stack:</span>
            <span className="text-[10px] font-bold text-sky-400">Python</span>
            <span className="text-[10px] font-bold text-indigo-400">React</span>
            <span className="text-[10px] font-bold text-pink-400">Vite</span>
            <span className="text-[10px] font-bold text-emerald-400">UBFC-Phys</span>
          </div>

          <div className={`lp-hero-actions flex flex-col sm:flex-row items-center justify-center gap-4 mt-3 lp-reveal-item ${contentVisible ? 'lp-revealed' : ''}`} style={{ transitionDelay: '0.65s' }}>
            {/* About Us Button with Stacked Profile Pictures */}
            <button 
              className="lp-about-us-btn" 
              onClick={(e) => handleSmoothScroll(e, 'about')}
              title="Tentang Tim Pengembang"
            >
              <div className="lp-avatar-stack">
                <img src="/images/dev1.png" alt="Arya" />
                <img src="/images/dev2.png" alt="Sari" />
                <img src="/images/dev3.png" alt="Budi" />
              </div>
              <div className="flex flex-col text-left leading-none justify-center">
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">Tim Kami</span>
                <span className="text-xs font-semibold text-white mt-0.5">About Us</span>
              </div>
            </button>

            <Button className="btn-shimmer cta-glow group flex items-center gap-2" onClick={onStart} size="lg">
              <span>Mulai Pengukuran</span>
              <ArrowRight className="size-4 transition-transform duration-300 group-hover:translate-x-1" />
            </Button>
          </div>

          <div className={`lp-proof-row lp-reveal-item ${contentVisible ? 'lp-revealed' : ''}`} style={{ marginTop: '0.5rem', transitionDelay: '0.75s' }}>
            <span className="lp-proof-pill"><ShieldCheck className="size-4 text-[#8affc4]" /> Bukan diagnosis medis</span>
            <span className="lp-proof-pill"><Clock3 className="size-4 text-sky-300" /> Pencahayaan stabil disarankan</span>
            <span className="lp-proof-pill"><Sparkles className="size-4 text-violet-300" /> UI tenang & modern</span>
          </div>
        </div>
      </div>

      {/* ═══ INTERACTIVE DEMO CONTENT ═══ */}
      <div className="lp-demo-section pt-0 pb-24 relative overflow-hidden">
        <div className="lp-shell relative z-20">

          {/* Interactive Player Mockup (Bright Glassmorphism Container) */}
          <div className={`lp-demo-player relative mx-1 max-w-[1280px] max-h-[1050px] rounded-xl overflow-visible lp-reveal-item ${contentVisible ? 'lp-revealed' : ''}`} style={{ transitionDelay: '0.85s' }}>
            
            {/* Player Titlebar (macOS Style + Tabbar) */}
            <div className="lp-demo-titlebar flex flex-col sm:flex-row items-center justify-between gap-4 px-1.5 py-2 rounded-t-xl">
              
              {/* Tabs */}
              <div className="flex items-center gap-1 bg-[#475569]/10 p-1 rounded-xl relative">
                {/* Interactive Demo Tab */}
                <button 
                  onClick={() => setDemoTab('demo')}
                  className={`text-[10px] sm:text-xs font-semibold px-4 py-2 rounded-xl transition-all duration-300 flex items-center gap-1.5 relative z-10 ${
                    demoTab === 'demo' ? 'bg-white text-slate-900 shadow-sm border border-black/5' : 'text-slate-600 hover:text-slate-950'
                  }`}
                >
                  <div className="size-4 rounded-full bg-[#4b68ff] flex items-center justify-center relative">
                    <svg className="size-2 text-white fill-white" viewBox="0 0 24 24">
                      <polygon points="6,4 20,12 6,20" />
                    </svg>
                  </div>
                  <span>Interactive Demo</span>
                </button>
                {/* Video Tab */}
                <button 
                  onClick={() => setDemoTab('video')}
                  className={`text-[10px] sm:text-xs font-semibold px-4 py-2 rounded-xl transition-all duration-300 flex items-center gap-1.5 relative z-10 ${
                    demoTab === 'video' ? 'bg-white text-slate-900 shadow-sm border border-black/5' : 'text-slate-600 hover:text-slate-950'
                  }`}
                >
                  <Film className="size-3.5" />
                  <span>Video</span>
                </button>
                {/* Visuals Tab */}
                <button 
                  onClick={() => setDemoTab('visuals')}
                  className={`text-[10px] sm:text-xs font-semibold px-4 py-2 rounded-xl transition-all duration-300 flex items-center gap-1.5 relative z-10 ${
                    demoTab === 'visuals' ? 'bg-white text-slate-900 shadow-sm border border-black/5' : 'text-slate-600 hover:text-slate-950'
                  }`}
                >
                  <User className="size-3.5" />
                  <span>Visuals</span>
                </button>
              </div>

              {/* Right tools (Figma, Notion, Webflow icons) */}
              <div className="hidden sm:flex items-center gap-2">
                {/* Figma Box */}
                <div className="size-8 rounded-lg bg-white border border-slate-200 shadow-sm flex items-center justify-center">
                  <svg className="size-5" viewBox="0 0 100 150" fill="none">
                    <path d="M25 37.5c0-13.8 11.2-25 25-25s25 11.2 25 25-11.2 25-25 25-25-11.2-25-25z" fill="#F24E1E"/>
                    <path d="M25 87.5c0-13.8 11.2-25 25-25s25 11.2 25 25-11.2 25-25 25-25-11.2-25-25z" fill="#A259FF"/>
                    <path d="M25 137.5c0-13.8 11.2-25 25-25v50c-13.8 0-25-11.2-25-25z" fill="#0ACF83"/>
                    <path d="M50 87.5c0 13.8 11.2 25 25 25s25-11.2 25-25-11.2-25-25-25-25 11.2-25 25z" fill="#1ABC9C"/>
                    <path d="M50 37.5c0 13.8 11.2 25 25 25s25-11.2 25-25-11.2-25-25-25-25 11.2-25 25z" fill="#FF7262"/>
                  </svg>
                </div>
                {/* Circle icon */}
                <div className="size-8 rounded-full bg-white/25 border border-white/40 shadow-sm flex items-center justify-center">
                  <span className="size-4 rounded-full bg-gradient-to-tr from-sky-400 to-indigo-500" />
                </div>
                {/* Notion Box */}
                <div className="size-8 rounded-lg bg-white border border-slate-200 shadow-sm flex items-center justify-center font-bold text-slate-800 text-sm">
                  N
                </div>
                {/* Webflow Box */}
                <div className="size-8 rounded-lg bg-white/10 border border-white/25 shadow-sm flex items-center justify-center">
                  <svg className="size-4 text-white fill-white" viewBox="0 0 100 100">
                    <path d="M92.7 20H73.3L61.6 57.1L50 20H30.6L42.2 57.1L30.5 94.3H49.9L61.6 57.2L73.3 94.3H92.7L81 57.2L92.7 20Z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Inner Wrapper to expose the Glassmorphic border */}
            <div className="p-1.5 pt-1.5 pb-1.5">
              {/* Main Content Window (light pastel cream/yellow box) */}
              <div className="lp-demo-content rounded-b-xl p-6 min-h-[760px] flex items-center justify-center transition-all duration-300 relative overflow-hidden">
                
                {/* Tab 1: Interactive Scan Demo */}
                {demoTab === 'demo' && !demoScanning && (
                  <div className="flex flex-col md:flex-row items-center justify-between w-full h-full relative z-10 px-4">
                    {/* Left graphic SVG */}
                    <div className="relative w-56 h-64 select-none pointer-events-none scale-90 sm:scale-105 transform origin-left flex-shrink-0">
                      {/* Arch shape with blue and magenta vertical stripes */}
                      <div 
                        className="absolute bottom-0 left-0 w-32 h-44 rounded-t-full overflow-hidden shadow-sm border border-slate-200/20" 
                        style={{
                          background: 'repeating-linear-gradient(90deg, #5551ff, #5551ff 12px, #ff007f 12px, #ff007f 24px)'
                        }} 
                      />
                      
                      {/* White box with Aa text */}
                      <div className="absolute top-16 left-12 w-28 h-28 bg-white rounded-xl shadow-lg border border-slate-100/80 flex items-center justify-center font-sans text-5xl font-bold tracking-tight">
                        <span className="text-[#b5a642]">A</span>
                        <span className="text-slate-400 -ml-0.5 mt-2.5 text-4xl">a</span>
                      </div>

                      {/* Orange box with black sprocket wheel */}
                      <div className="absolute top-6 left-6 w-16 h-16 bg-gradient-to-tr from-[#f97316] to-[#fb923c] rounded-xl shadow-md flex items-center justify-center">
                        <svg className="size-11 text-black fill-current" viewBox="0 0 100 100">
                          <path d="M50 15c-19.3 0-35 15.7-35 35s15.7 35 35 35 35-15.7 35-35-15.7-35-35-35zm0 58c-12.7 0-23-10.3-23-23s10.3-23 23-23 23 10.3 23 23-10.3 23-23 23z"/>
                          <path d="M50 35c-2.8 0-5 2.2-5 5v20c0 2.8 2.2 5 5 5s5-2.2 5-5V40c0-2.8-2.2-5-5-5z" transform="rotate(0 50 50)"/>
                          <path d="M50 35c-2.8 0-5 2.2-5 5v20c0 2.8 2.2 5 5 5s5-2.2 5-5V40c0-2.8-2.2-5-5-5z" transform="rotate(45 50 50)"/>
                          <path d="M50 35c-2.8 0-5 2.2-5 5v20c0 2.8 2.2 5 5 5s5-2.2 5-5V40c0-2.8-2.2-5-5-5z" transform="rotate(90 50 50)"/>
                          <path d="M50 35c-2.8 0-5 2.2-5 5v20c0 2.8 2.2 5 5 5s5-2.2 5-5V40c0-2.8-2.2-5-5-5z" transform="rotate(135 50 50)"/>
                        </svg>
                      </div>
                    </div>

                    {/* Center details */}
                    <div className="flex flex-col items-center text-center max-w-sm mx-auto my-6 md:my-0 relative z-20">
                      <h3 className="text-3xl font-extrabold text-slate-950 tracking-tight leading-tight">Explore Figma's Dev Mode</h3>
                      <p className="text-sm text-slate-600 leading-relaxed mt-2.5 max-w-[320px]">
                        Discover how to export code for seamless collaboration and handoff.
                      </p>
                      <button 
                        onClick={startDemoSimulation}
                        className="mt-6 px-6 py-3 bg-black text-white hover:bg-slate-900 hover:scale-[1.03] active:scale-[0.98] text-xs font-bold tracking-wide rounded-xl shadow-[0_4px_12px_rgba(0,0,0,0.15)] transition-all duration-200 cursor-pointer"
                      >
                        Get Started
                      </button>
                    </div>

                    {/* Right graphic stack */}
                    <div className="absolute bottom-0 right-0 flex items-end select-none pointer-events-none scale-75 sm:scale-110 transform origin-bottom-right">
                      {/* Orange checkerboard block */}
                      <div className="w-16 h-12 bg-[#ff7e33] relative overflow-hidden" style={{
                        backgroundImage: 'radial-gradient(circle, #5551ff 20%, transparent 20%), radial-gradient(circle, #5551ff 20%, transparent 20%)',
                        backgroundSize: '16px 16px',
                        backgroundPosition: '0 0, 8px 8px'
                      }} />

                      {/* Blue/purple block with staircase */}
                      <div className="w-16 h-20 bg-[#5551ff] relative overflow-hidden">
                        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 64 80" fill="none">
                          <path d="M0 80 L0 60 L16 60 L16 40 L32 40 L32 20 L48 20 L48 0 L64 0 L64 80 Z" fill="#9ba8ff" />
                          <path d="M0 80 L0 70 L8 70 L8 50 L24 50 L24 30 L40 30 L40 10 L56 10 L56 0 L64 0 L64 80 Z" fill="#c2cbff" opacity="0.4" />
                        </svg>
                      </div>

                      {/* Magenta block with spiral */}
                      <div className="w-16 h-24 bg-[#ff2a85] flex items-center justify-center relative overflow-hidden">
                        <svg className="size-12 text-black" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="6" strokeLinecap="round">
                          <path d="M50 50c10 0 15-5 15-10s-5-10-10-10-10 5-10 10 5 15 10 15 15-5 15-15-5-15-15-15-15 5-15 20c0 15 10 25 25 25s25-10 25-25" />
                        </svg>
                      </div>

                      {/* Green paperclip shape block */}
                      <div className="w-20 h-32 bg-[#a78bfa] rounded-t-2xl flex items-center justify-center relative overflow-hidden pr-3 pb-3">
                        <div className="w-10 h-22 rounded-full border-[10px] border-[#00c968] bg-transparent" />
                      </div>

                      {/* Coral pill with orange arrow */}
                      <div className="absolute bottom-2 right-1.5 px-3 py-1.5 bg-[#fda4af] rounded-full border border-rose-300 shadow-md flex items-center justify-center w-14 h-8">
                        <ArrowRight className="size-5 text-[#f97316] stroke-[3.5]" />
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab 1: Scanning Overlay (Interactive Scan Simulation) */}
                {demoTab === 'demo' && demoScanning && (
                  <div className="absolute inset-0 bg-[#0a0f1d] text-white flex flex-col items-center justify-center p-6 z-20 transition-all duration-500">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center w-full max-w-2xl my-auto">
                      {/* Left Column: Mock camera feed with scanner overlay */}
                      <div className="relative aspect-video rounded-xl bg-slate-900 overflow-hidden flex items-center justify-center border border-slate-800 shadow-inner group">
                        {/* Simulated Camera Video Placeholder */}
                        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-tr from-slate-950 via-slate-900 to-indigo-950">
                          {/* Face Mesh Contour */}
                          <svg className="size-32 text-emerald-400 scale-105 transition-transform duration-500" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M50,15 C28,15 28,50 28,70 C28,88 50,88 50,88 C50,88 72,88 72,70 C72,50 72,15 50,15 Z" strokeDasharray="3 3" />
                            <circle cx="40" cy="48" r="4" />
                            <circle cx="60" cy="48" r="4" />
                            <path d="M36,44 Q40,41 44,44" />
                            <path d="M56,44 Q60,41 64,44" />
                            <path d="M50,47 L50,62 L46,65 L50,66 L54,65 Z" />
                            <path d="M38,72 Q50,80 62,72" />
                          </svg>
                        </div>

                        {/* Scanner laser bar overlay */}
                        <div className="lp-scan-bar absolute left-0 right-0 h-0.5 bg-emerald-400 shadow-[0_0_12px_#34d399]" />

                        {/* Progress Badge */}
                        <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/60 backdrop-blur-sm px-2.5 py-1 rounded-md text-[10px] font-bold text-white border border-white/10 uppercase tracking-wider">
                          <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
                          <span>Memindai: {demoProgress}%</span>
                        </div>

                        {/* Camera Bracket corners */}
                        <div className="absolute top-4 left-4 size-3 border-t-2 border-l-2 border-slate-400/40" />
                        <div className="absolute top-4 right-4 size-3 border-t-2 border-r-2 border-slate-400/40" />
                        <div className="absolute bottom-4 left-4 size-3 border-b-2 border-l-2 border-slate-400/40" />
                        <div className="absolute bottom-4 right-4 size-3 border-b-2 border-r-2 border-slate-400/40" />
                      </div>

                      {/* Right Column: Interactive Heart Rate details */}
                      <div className="flex flex-col gap-4 text-left">
                        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Analisis Denyut Jantung (rPPG)</h3>
                        
                        {/* Simulated heart beat indicator */}
                        <div className="flex items-center gap-3 bg-white/5 p-4 rounded-xl border border-white/10 shadow-sm">
                          <div className="p-3 rounded-lg bg-rose-500/10 transition-colors duration-300">
                            <Heart className="size-6 text-rose-500 animate-heartbeat" />
                          </div>
                          <div className="flex flex-col leading-none">
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Detak Jantung</span>
                            <span className="text-2xl font-extrabold text-white mt-1">
                              {demoHeartRate}{" "}
                              <span className="text-xs font-semibold text-slate-450 uppercase tracking-normal">Bpm</span>
                            </span>
                          </div>
                        </div>

                        {/* Signal Stability progress */}
                        <div className="bg-white/5 p-4 rounded-xl border border-white/10 shadow-sm flex flex-col gap-2">
                          <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            <span>Stabilitas Sinyal</span>
                            <span className="text-emerald-400">Mengkalibrasi...</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-emerald-400 to-teal-500 transition-all duration-300"
                              style={{ width: `${demoProgress}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
              )}

              {/* Tab 2: Video Analisis */}
              {demoTab === 'video' && (
                <div className="flex flex-col gap-6 items-center justify-center my-auto w-full px-4">
                  <div className="text-center max-w-lg">
                    <h3 className="text-base font-bold text-slate-800 uppercase tracking-wide mb-2">Pemisahan Gelombang Spektrum Warna</h3>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      Kamera mendeteksi fluktuasi refleksi cahaya tipis pada kulit wajah akibat aliran darah setiap detak jantung. Algoritma memisahkan spektrum video menjadi 3 saluran warna utama:
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-2xl mt-2">
                    {/* Red */}
                    <div className="flex flex-col items-center gap-3 p-4 rounded-xl border border-red-100 bg-red-50/50 text-center shadow-sm">
                      <span className="size-4 rounded-full bg-red-500 border-2 border-white shadow-md" />
                      <div className="flex flex-col">
                        <span className="text-xs font-bold text-slate-800 uppercase">Red Channel</span>
                        <span className="text-[10px] text-slate-400 mt-1">Sinyal Fisiologis Lemah & Tidak Stabil</span>
                      </div>
                    </div>
                    {/* Green (Pulsing Winner) */}
                    <div className="flex flex-col items-center gap-3 p-4 rounded-xl border border-emerald-200 bg-emerald-50/70 text-center shadow-[0_4px_15px_rgba(16,185,129,0.1)] relative overflow-hidden">
                      <div className="absolute top-0 right-0 bg-emerald-400 text-white text-[8px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-bl-lg">Optimal</div>
                      <span className="size-4 rounded-full bg-emerald-500 border-2 border-white shadow-md animate-ping" />
                      <div className="flex flex-col">
                        <span className="text-xs font-bold text-emerald-800 uppercase">Green Channel</span>
                        <span className="text-[10px] text-emerald-600 font-semibold mt-1">Sinyal Paling Kuat & Stabil (Hemoglobin)</span>
                      </div>
                    </div>
                    {/* Blue */}
                    <div className="flex flex-col items-center gap-3 p-4 rounded-xl border border-sky-100 bg-sky-50/50 text-center shadow-sm">
                      <span className="size-4 rounded-full bg-sky-500 border-2 border-white shadow-md" />
                      <div className="flex flex-col">
                        <span className="text-xs font-bold text-slate-800 uppercase">Blue Channel</span>
                        <span className="text-[10px] text-slate-400 mt-1">Tinggi Distorsi Cahaya Ruangan</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 3: Visuals stress reports */}
              {demoTab === 'visuals' && (
                <div className="flex flex-col gap-6 w-full my-auto text-slate-900 px-4">
                  <div className="text-center">
                    <h3 className="text-base font-bold text-slate-800 uppercase tracking-wide mb-1">Laporan Hasil Pengukuran</h3>
                    <span className="text-[10px] font-bold text-[#82669e]/80 uppercase tracking-wider">Simulasi Sesi: 30 Detik</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-2xl mx-auto">
                    {/* Stress score capsule */}
                    <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-emerald-100 bg-emerald-50/50 shadow-sm text-center">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Skor Stres</span>
                      <span className="text-3xl font-extrabold text-emerald-600 mt-1">
                        {demoStress !== null ? `${demoStress}%` : "34%"}
                      </span>
                      <span className={`mt-1 rounded-full px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ${
                        demoStress !== null && demoStress > 70 
                          ? 'bg-rose-100 text-rose-700' 
                          : demoStress !== null && demoStress > 40 
                            ? 'bg-amber-100 text-amber-700' 
                            : 'bg-emerald-100 text-emerald-700'
                      }`}>
                        {demoStressLabel}
                      </span>
                    </div>

                    {/* SDNN HRV Metric */}
                    <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-slate-200 bg-white shadow-sm text-center">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">SDNN (HRV)</span>
                      <span className="text-2xl font-extrabold text-slate-800 mt-1">56 <span className="text-xs font-semibold text-slate-500">ms</span></span>
                      <span className="text-[9px] font-semibold text-slate-400 mt-1">Rentang Sehat / Normal</span>
                    </div>

                    {/* RMSSD HRV Metric */}
                    <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-slate-200 bg-white shadow-sm text-center">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">RMSSD (HRV)</span>
                      <span className="text-2xl font-extrabold text-slate-800 mt-1">48 <span className="text-xs font-semibold text-slate-500">ms</span></span>
                      <span className="text-[9px] font-semibold text-slate-400 mt-1">Aktivitas Parasimpatis Baik</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 📱 Floating Emoticon Cards next to macOS Player (LogoPoint Tech Card style) */}
          <div className="flex flex-wrap xl:block justify-center items-center gap-4 mt-8 xl:mt-0 w-full max-w-2xl mx-auto px-4">
            {moods.map((m) => (
              <div 
                key={m.id}
                onClick={() => selectMood(m.stress, m.hr, m.stressLabel)}
                className={`lp-emoticon-card lp-ec-${m.id} ${contentVisible ? 'lp-revealed' : ''}`}
                title={`Simulasi Mood: ${m.label}`}
              >
                {m.emoji}
                <span className="lp-mood-tooltip">
                  Mood: {m.label}
                </span>
              </div>
            ))}
          </div>

          {/* Floating Presenter Bubble (Bottom-Left overlap) */}
          <div className="lp-demo-presenter absolute -bottom-8 left-4 md:left-10 flex items-center gap-3.5 z-30 select-none pointer-events-none max-w-sm sm:max-w-md">
            {/* Presenter Avatar Arya */}
            <div className="relative flex-shrink-0">
              <img 
                className="size-16 md:size-20 rounded-full border-4 border-white shadow-xl object-cover bg-slate-900 shadow-slate-950/20" 
                src="/images/dev1.png" 
                alt="Arya Presenter" 
              />
              <span className="absolute bottom-0.5 right-0.5 size-3.5 rounded-full bg-emerald-500 border-2 border-white" />
            </div>
            
            {/* Speech balloon subtitel (translucent dark capsule) */}
            <div className="lp-demo-subtitle-balloon bg-[#334155]/95 text-white rounded-full px-5 py-2.5 shadow-[0_10px_25px_rgba(0,0,0,0.2)] border border-slate-600/30 text-left relative flex flex-col justify-center max-w-[18rem] sm:max-w-[24rem]">
              <p className="text-[11px] font-medium leading-tight">
                {presenterSubtitle}
              </p>
            </div>
          </div>
        </div>

        {/* 🌟 Logo Wall/Ticker Section (Lemni framer-11c01s0 Style) */}
        <div className="lp-lemni-ticker sr mt-28">
          <div className="lp-lemni-label">Supported Tech Stack</div>
          <div className="lp-lemni-sep" />
          <div className="lp-lemni-scroll-container">
            <div className="lp-lemni-track">
              {[1, 2, 3, 4, 5, 6].map((setIdx) => (
                <div key={setIdx} className="flex items-center gap-16 flex-shrink-0">
                  <div className="lp-lemni-item">
                    <img src={reactLogo} alt="React" className="h-5 w-auto" />
                    <span>React</span>
                  </div>
                  <div className="lp-lemni-item">
                    <img src={viteLogo} alt="Vite" className="h-5 w-auto" />
                    <span>Vite</span>
                  </div>
                  <div className="lp-lemni-item">
                    <img src={lumaLogo} alt="Luma Vulse" className="h-5 w-auto" />
                    <span>Luma Vulse</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
      </section>
      {/* ═══ ABOUT US SECTION ═══ */}
      <section id="about" className="lp-about-section py-28 relative overflow-hidden">
        {/* Glow ambient background element behind section */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[60rem] h-[34rem] bg-[#e3cde2]/5 blur-[130px] rounded-full pointer-events-none -z-10" />

        <div className="lp-shell relative z-20">
          <div className="text-center max-w-2xl mx-auto mb-10 sr">
            <span className="lp-badge">Tentang Kami</span>
            <h2 className="text-3xl md:text-4xl font-bold mt-4 tracking-tight">
              <span className="lp-gradient-text">Sinergi Sains Fisiologis, ML & Desain</span>
            </h2>
            <p className="text-sm text-[#9eb0c5] mt-3 leading-relaxed">
              Kami adalah tim pengembang yang membangun Luma Vulse untuk mempermudah monitoring tingkat stres secara otonom dan non-kontak dari rumah.
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row justify-center items-center gap-6 mt-8">
            <div className="glass-panel rounded-2xl p-5 border-white/8 bg-black/20 text-center max-w-xs w-full shadow-lg">
              <img src="/images/dev1.png" alt="Developer 1" className="size-16 rounded-full mx-auto border border-[#8affc4]/30 object-cover bg-slate-900" />
              <h4 className="text-sm font-bold text-white mt-3">Arya Pradana</h4>
              <p className="text-[10px] text-[#8affc4] uppercase tracking-wider font-semibold mt-0.5">Machine Learning Engineer</p>
            </div>
            <div className="glass-panel rounded-2xl p-5 border-white/8 bg-black/20 text-center max-w-xs w-full shadow-lg">
              <img src="/images/dev2.png" alt="Developer 2" className="size-16 rounded-full mx-auto border border-sky-400/30 object-cover bg-slate-900" />
              <h4 className="text-sm font-bold text-white mt-3">Sari Amalia</h4>
              <p className="text-[10px] text-sky-400 uppercase tracking-wider font-semibold mt-0.5">UI/UX Front-End Engineer</p>
            </div>
            <div className="glass-panel rounded-2xl p-5 border-white/8 bg-black/20 text-center max-w-xs w-full shadow-lg">
              <img src="/images/dev3.png" alt="Developer 3" className="size-16 rounded-full mx-auto border border-violet-400/30 object-cover bg-slate-900" />
              <h4 className="text-sm font-bold text-white mt-3">Budi Setiawan</h4>
              <p className="text-[10px] text-violet-400 uppercase tracking-wider font-semibold mt-0.5">Backend Infrastructure</p>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="lp-footer">
        <div className="lp-shell px-4">
          {/* Top part: Links Columns */}
          <div className="lp-footer-links-grid">
            {/* Column 1: Brand details */}
            <div className="lp-footer-brand-col flex flex-col items-start gap-4">
              <img className="h-7 w-auto object-contain lp-footer-brand-logo" src={lumaLogo} alt="Luma Logo" />
              <p className="text-xs text-slate-500 leading-relaxed max-w-[200px] text-left">
                Engine monitoring stres fisiologis otonom berbasis video wajah terkemuka.
              </p>
            </div>
            
            {/* Column 2: Product */}
            <div className="lp-footer-col flex flex-col items-start gap-3 text-left">
              <h4 className="lp-footer-col-title">Product</h4>
              <a href="#" className="lp-footer-link-item">Sesi Pengukuran</a>
              <a href="#" className="lp-footer-link-item">Estimasi Stres</a>
              <a href="#" className="lp-footer-link-item">Kalibrasi Sinyal</a>
              <a href="#" className="lp-footer-link-item">Integrasi API</a>
              <a href="#" className="lp-footer-link-item">Paket Harga</a>
            </div>

            {/* Column 3: Solutions */}
            <div className="lp-footer-col flex flex-col items-start gap-3 text-left">
              <h4 className="lp-footer-col-title">Solutions</h4>
              <a href="#" className="lp-footer-link-item">Riset Akademis</a>
              <a href="#" className="lp-footer-link-item">Kesehatan Karyawan</a>
              <a href="#" className="lp-footer-link-item">Telemedicine</a>
              <a href="#" className="lp-footer-link-item">Integrasi Game</a>
              <a href="#" className="lp-footer-link-item">Hubungi Ahli</a>
            </div>

            {/* Column 4: Resources */}
            <div className="lp-footer-col flex flex-col items-start gap-3 text-left">
              <h4 className="lp-footer-col-title">Resources</h4>
              <a href="#" className="lp-footer-link-item">Blog Medis</a>
              <a href="#" className="lp-footer-link-item">Pusat Bantuan</a>
              <a href="#" className="lp-footer-link-item">Log Perubahan</a>
              <a href="#" className="lp-footer-link-item">Dokumentasi</a>
              <a href="#" className="lp-footer-link-item">Panduan</a>
            </div>

            {/* Column 5: Company */}
            <div className="lp-footer-col flex flex-col items-start gap-3 text-left">
              <h4 className="lp-footer-col-title">Company</h4>
              <a href="#" className="lp-footer-link-item">Tim Pengembang</a>
              <a href="#" className="lp-footer-link-item">Karir</a>
              <a href="#" className="lp-footer-link-item">Aset Brand</a>
              <a href="#" className="lp-footer-link-item">Keamanan Data</a>
              <a href="#" className="lp-footer-link-item">Kebijakan Privasi</a>
            </div>
          </div>

          <div className="lp-footer-sep" />

          {/* Bottom part: Newsletter */}
          <div className="lp-footer-newsletter-row flex flex-col md:flex-row items-center justify-between gap-6 py-8">
            <h4 className="lp-footer-cta text-left">
              Smarter Stories, Every Month.
            </h4>
            <div className="lp-footer-form-container w-full md:w-auto">
              <form className="lp-footer-form mx-auto md:mx-0" onSubmit={(e) => e.preventDefault()}>
                <input 
                  type="email" 
                  placeholder="Enter your email" 
                  className="lp-footer-input" 
                  required 
                />
                <button type="submit" className="lp-footer-submit">
                  Subscribe
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="lp-footer-massive-logo-container">
          <img className="lp-footer-massive-logo" src={lumaLogo} alt="Luma Watermark" />
        </div>
      </footer>

      {/* ─── Floating Chat Widget ─── */}
      <div className="lp-chat-widget">
        {/* Panel */}
        <div className={`lp-chat-panel ${isChatOpen ? 'active' : ''}`}>
          <div className="lp-chat-header">
            <div className="lp-chat-avatar">
              <MessageSquare className="size-5 text-blue-600" />
            </div>
            <div className="flex-1 text-left">
              <h4 className="lp-chat-name">Luma Assistant</h4>
              <div className="lp-chat-status">
                <span className="lp-chat-status-dot" />
                <span>Online</span>
              </div>
            </div>
            <button className="text-white/60 hover:text-white transition-colors cursor-pointer" onClick={() => setIsChatOpen(false)}>
              <X className="size-4" />
            </button>
          </div>
          
          <div className="lp-chat-messages">
            {chatMessages.map(msg => (
              <div 
                key={msg.id} 
                className="lp-chat-message-bubble text-left"
                style={{
                  alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  background: msg.sender === 'user' ? 'rgba(29, 78, 216, 0.4)' : 'rgba(255, 255, 255, 0.06)',
                  border: msg.sender === 'user' ? '1px solid rgba(29, 78, 216, 0.3)' : '1px solid rgba(255, 255, 255, 0.04)',
                  borderRadius: msg.sender === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                }}
              >
                <div>{msg.text}</div>
                <div className="lp-chat-message-time">{msg.time}</div>
              </div>
            ))}
          </div>
          
          <form className="lp-chat-input-area" onSubmit={handleSendChat}>
            <input 
              type="text" 
              placeholder="Ketik pesan..." 
              value={chatInput} 
              onChange={(e) => setChatInput(e.target.value)} 
            />
            <button type="submit" className="lp-chat-send">
              <Send className="size-3.5" />
            </button>
          </form>
        </div>

        {/* Floating Button */}
        <button 
          className="lp-chat-button" 
          onClick={() => setIsChatOpen(!isChatOpen)}
          title="Tanya Luma Assistant"
        >
          <MessageSquare className="size-6" />
        </button>
      </div>
    </main>
  )
}
