import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import {
  AlertCircle,
  Camera,
  Home,
  RotateCcw,
  AlertTriangle,
  Heart,
  Sparkles,
  UserCheck,
  CheckCircle2,
  TrendingUp,
} from 'lucide-react'

import { MetricCard } from '../components/MetricCard'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { ProgressBar } from '../components/ui/ProgressBar'
import { StatusBadge } from '../components/ui/StatusBadge'
import { DisclaimerBox } from '../components/ui/DisclaimerBox'
import {
  startMeasurement,
  stopMeasurement,
  getLiveMeasurementSnapshot,
  getMeasurementResult,
  getSignalDetails,
  type MeasurementResult,
  type MeasurementSession,
  type SignalQuality,
  type StressLevel,
  type SignalDetails,
} from '../services/measurementService'
import lumaLogo from '../assets/Luma. logo.svg'

type MeasurementPageProps = {
  duration?: number
  onBack: () => void
}

type MeasurementPhase = 'instructions' | 'measuring' | 'result'

const instructions = [
  { text: 'Duduk diam rileks', desc: 'Pertahankan postur tegak selama 60 detik.' },
  { text: 'Wajah terlihat jelas', desc: 'Hindari masker atau penutup wajah lainnya.' },
  { text: 'Pencahayaan stabil', desc: 'Cahaya yang rata menghindari bayangan tajam.' },
  { text: 'Kurangi gerakan & bicara', desc: 'Gerakan berlebih mengaburkan pembacaan sinyal.' },
]

const stressLabel: Record<StressLevel | 'Measuring', string> = {
  Low: 'Rendah',
  Moderate: 'Sedang',
  High: 'Tinggi',
  Measuring: 'Mengukur',
}

const qualityLabel: Record<SignalQuality, string> = {
  Good: 'Baik',
  Moderate: 'Sedang',
  Poor: 'Kurang',
}

const featureLabels: Record<keyof SignalDetails['features'], string> = {
  meanHr: 'Mean HR',
  sdnn: 'SDNN',
  rmssd: 'RMSSD',
  pnn50: 'pNN50',
  lfPower: 'LF Power',
  hfPower: 'HF Power',
  lfHfRatio: 'LF/HF Ratio',
  snrProxy: 'SNR Proxy',
  detectionRate: 'Detection Rate',
}

function qualityTone(quality: SignalQuality) {
  if (quality === 'Good') return 'success'
  if (quality === 'Moderate') return 'warning'
  return 'danger'
}

function stressTone(stress: StressLevel) {
  if (stress === 'Low') return 'success'
  if (stress === 'Moderate') return 'warning'
  return 'danger'
}

function describeCameraError(error: unknown) {
  if (!(error instanceof DOMException)) {
    return 'Tidak dapat mengakses kamera. Silakan coba lagi atau periksa pengaturan browser.'
  }

  if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
    return 'Izin kamera ditolak. Berikan izin kamera di browser untuk memulai pengukuran.'
  }

  if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
    return 'Kamera tidak ditemukan. Hubungkan kamera atau gunakan perangkat dengan kamera aktif.'
  }

  if (error.name === 'NotReadableError') {
    return 'Kamera sedang digunakan oleh aplikasi lain. Tutup aplikasi tersebut lalu coba lagi.'
  }

  return 'Tidak dapat mengakses kamera. Silakan coba lagi dengan perangkat dan browser yang mendukung kamera.'
}

function formatTimestamp(timestamp: string) {
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(timestamp))
}

function ChartCard({
  color,
  data,
  title,
  unit,
  glowFilterId,
  glowColor,
}: {
  color: string
  data: Array<{ second: number; value: number }>
  title: string
  unit: string
  glowFilterId: string
  glowColor: string
}) {
  return (
    <Card className="glass-card border-white/8 bg-black/25">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-xs font-bold text-white uppercase tracking-wider">{title}</h2>
        <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-[10px] font-bold text-[#94a3b8] tracking-wide uppercase">{unit}</span>
      </div>
      <div className="mt-4 h-64">
        <ResponsiveContainer height="100%" width="100%">
          <LineChart data={data} margin={{ bottom: 8, left: -20, right: 12, top: 12 }}>
            <defs>
              <filter id={glowFilterId} x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor={glowColor} floodOpacity="0.7" />
              </filter>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis dataKey="second" stroke="#64748b" tickLine={false} tick={{ fontSize: 10 }} />
            <YAxis stroke="#64748b" tickLine={false} tick={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                background: 'rgba(11, 15, 25, 0.85)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255,255,255,0.18)',
                borderRadius: 12,
                boxShadow: '0 12px 28px rgba(0,0,0,0.3)',
                color: '#f0f6fc',
                fontSize: '11px',
              }}
            />
            <Line
              dataKey="value"
              dot={false}
              stroke={color}
              strokeWidth={3}
              type="monotone"
              filter={`url(#${glowFilterId})`}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

export function MeasurementPage({ duration = 60, onBack }: MeasurementPageProps) {
  const [phase, setPhase] = useState<MeasurementPhase>('instructions')
  
  // Camera & Session State
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [session, setSession] = useState<MeasurementSession | null>(null)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [isRequestingCamera, setIsRequestingCamera] = useState(false)

  // Live measurement & result state
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [isFinishing, setIsFinishing] = useState(false)
  const [measurementResult, setMeasurementResult] = useState<MeasurementResult | null>(null)
  const [signalDetails, setSignalDetails] = useState<SignalDetails | null>(null)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)

  // Fast tick for smooth running wave simulator (10 updates per second)
  const [tick, setTick] = useState(0)
  // Radial score drawer state
  const [animatedScore, setAnimatedScore] = useState(0)

  const snapshot = useMemo(() => getLiveMeasurementSnapshot(elapsed), [elapsed])

  // Mouse cursor glow tracking inside measurement page
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      document.documentElement.style.setProperty('--mouse-x', `${e.clientX}px`)
      document.documentElement.style.setProperty('--mouse-y', `${e.clientY}px`)
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  // Live wave smooth scroller interval
  useEffect(() => {
    if (phase !== 'measuring') return
    const id = setInterval(() => {
      setTick((t) => t + 1)
    }, 100)
    return () => clearInterval(id)
  }, [phase])

  // Radial score animation draw effect
  useEffect(() => {
    if (phase === 'result' && measurementResult) {
      setAnimatedScore(0)
      const timer = setTimeout(() => {
        setAnimatedScore(measurementResult.stressScore)
      }, 150)
      return () => clearTimeout(timer)
    }
  }, [phase, measurementResult])

  // Dynamic Scrolling PPG/ECG Wave Simulator Data (40 points)
  const liveWaveData = useMemo(() => {
    return Array.from({ length: 40 }, (_, index) => {
      // time value shifts as tick increments
      const t = (tick / 10) + index / 8
      
      // Simulate PPG peak + dicrotic notch
      const baseSine = Math.sin(t * 2 * Math.PI)
      const dicroticNotch = Math.sin(t * 4 * Math.PI) * 0.28
      const noise = Math.sin(t * 0.35) * 0.02
      
      return {
        second: index + 1,
        value: Number((0.5 + baseSine * 0.15 + dicroticNotch * 0.05 + noise).toFixed(3)),
      }
    })
  }, [tick])

  const stopStream = useCallback((activeStream: MediaStream | null) => {
    if (activeStream) {
      activeStream.getTracks().forEach((track) => track.stop())
    }
  }, [])

  // Clean up camera stream on unmount
  useEffect(() => {
    return () => {
      stopStream(stream)
    }
  }, [stream, stopStream])

  // Bind stream to video element when it becomes available
  useEffect(() => {
    if (phase === 'measuring' && videoRef.current && stream) {
      videoRef.current.srcObject = stream
    }
  }, [phase, stream])

  // Finish Measurement handler
  const finishMeasurement = useCallback(
    async (actualDuration: number, activeSession: MeasurementSession | null) => {
      if (!activeSession || isFinishing) return

      setIsFinishing(true)
      try {
        const result = await getMeasurementResult(activeSession.id, actualDuration)
        const details = await getSignalDetails()
        await stopMeasurement(activeSession.id)
        stopStream(stream)
        setStream(null)
        setSession(null)
        setMeasurementResult(result)
        setSignalDetails(details)
        setPhase('result')
      } catch (err) {
        console.error(err)
      } finally {
        setIsFinishing(false)
      }
    },
    [isFinishing, stream, stopStream],
  )

  // Timer countdown effect during measuring
  useEffect(() => {
    if (phase !== 'measuring' || !stream || !session || isFinishing) return

    const intervalId = window.setInterval(() => {
      setElapsed((current) => {
        const next = Math.min(duration, current + 1)

        if (next >= duration) {
          window.clearInterval(intervalId)
          void finishMeasurement(duration, session)
        }

        return next
      })
    }, 1000)

    return () => window.clearInterval(intervalId)
  }, [phase, duration, finishMeasurement, isFinishing, session, stream])

  // Handle request camera & start measurement
  const handleEnableCamera = async () => {
    setCameraError(null)

    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError('Browser ini belum mendukung akses kamera. Gunakan browser modern seperti Chrome, Edge, atau Firefox.')
      return
    }

    setIsRequestingCamera(true)
    let requestedStream: MediaStream | null = null
    try {
      requestedStream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: 'user',
          height: { ideal: 720 },
          width: { ideal: 1280 },
        },
      })
      const nextSession = await startMeasurement()
      setStream(requestedStream)
      setSession(nextSession)
      setElapsed(0)
      setMeasurementResult(null)
      setSignalDetails(null)
      setSaveMessage(null)
      setPhase('measuring')
      setIsFinishing(false)
    } catch (err) {
      if (requestedStream) {
        stopStream(requestedStream)
      }
      setCameraError(describeCameraError(err))
    } finally {
      setIsRequestingCamera(false)
    }
  }

  // Handle Stop measurement early
  const handleStop = () => {
    void finishMeasurement(Math.max(1, elapsed), session)
  }

  // Handle Restart measurement
  const handleRestart = async () => {
    if (session) {
      await stopMeasurement(session.id)
    }
    setElapsed(0)
    setIsFinishing(false)
    const nextSession = await startMeasurement()
    setSession(nextSession)
  }

  // Handle Back to Instructions (closes camera)
  const handleBackToInstructions = () => {
    stopStream(stream)
    setStream(null)
    setSession(null)
    setPhase('instructions')
    setElapsed(0)
  }

  // Handle Cancel / Back button
  const handleBackAction = () => {
    stopStream(stream)
    onBack()
  }

  // Radial progress ring geometry offsets
  const radius = 52
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (animatedScore / 100) * circumference

  // Dynamic drop shadows based on results/measurements
  const stressCategoryColor = measurementResult?.stressLevel ?? 'Low'
  const stressGlowClass = 
    stressCategoryColor === 'Low'
      ? 'border-[#8affc4]/30 shadow-[0_0_30px_rgba(138,255,196,0.18)]'
      : stressCategoryColor === 'Moderate'
      ? 'border-amber-400/30 shadow-[0_0_30px_rgba(245,158,11,0.18)]'
      : 'border-rose-400/30 shadow-[0_0_30px_rgba(244,63,94,0.18)]'

  return (
    <main className="lp-page min-h-screen pb-16">
      {/* Background Orbs & Glow */}
      <div aria-hidden="true" className="lp-ambient">
        <div className="lp-ambient-blob lp-blob-1" />
        <div className="lp-ambient-blob lp-blob-2" />
        <div className="lp-ambient-blob lp-blob-3" />
      </div>
      <div aria-hidden="true" className="lp-cursor-glow" />

      {/* Mini Glassmorphic Navbar */}
      <div className="pt-5 px-4 sm:px-6 lg:px-8">
        <header className="glass-panel mx-auto max-w-[1280px] flex items-center justify-between rounded-full border border-white/15 bg-white/4 px-5 py-3 shadow-2xl backdrop-blur-xl">
          {/* Left: Brand */}
          <div className="flex items-center gap-2.5">
            <div className="lp-nav-logo-container relative flex items-center">
              <img className="h-8 w-auto object-contain" src={lumaLogo} alt="Luma Logo" />
            </div>
            <div className="flex flex-col justify-center leading-none ml-1">
              <span className="text-xs font-bold tracking-wide text-white">Vulse</span>
              <span className="mt-0.5 text-[8px] font-semibold uppercase tracking-[0.18em] text-[#7dddb2]">rPPG Engine</span>
            </div>
          </div>

          {/* Center: Stepper */}
          <div className="flex items-center gap-1.5 sm:gap-3 px-2 py-1 rounded-full bg-white/4 border border-white/5">
            <span className={`text-[11px] font-bold px-3 py-1 rounded-full border transition-all duration-300 ${phase === 'instructions' ? 'border-[#8affc4]/25 bg-[#8affc4]/15 text-[#8affc4] shadow-[0_0_12px_rgba(138,255,196,0.15)]' : 'border-transparent text-white/40'}`}>
              ① Persiapan
            </span>
            <span className="text-white/20 text-xs font-bold select-none">···</span>
            <span className={`text-[11px] font-bold px-3 py-1 rounded-full border transition-all duration-300 ${phase === 'measuring' ? 'border-[#8affc4]/25 bg-[#8affc4]/15 text-[#8affc4] shadow-[0_0_12px_rgba(138,255,196,0.15)]' : 'border-transparent text-white/40'}`}>
              ② Pengukuran
            </span>
            <span className="text-white/20 text-xs font-bold select-none">···</span>
            <span className={`text-[11px] font-bold px-3 py-1 rounded-full border transition-all duration-300 ${phase === 'result' ? 'border-[#8affc4]/25 bg-[#8affc4]/15 text-[#8affc4] shadow-[0_0_12px_rgba(138,255,196,0.15)]' : 'border-transparent text-white/40'}`}>
              ③ Hasil
            </span>
          </div>

          {/* Right: Navigation Action */}
          <div className="flex items-center gap-2">
            <Button
              className="min-h-8 text-[11px] px-3.5 font-bold hover:scale-[1.03]"
              variant="secondary"
              size="sm"
              onClick={handleBackAction}
            >
              <Home className="mr-1.5 size-3.5" />
              Ke Home
            </Button>
          </div>
        </header>
      </div>

      {/* Main Content Area */}
      <div className="bento-shell max-w-[1280px] mt-10 px-4 sm:px-6 lg:px-8">
        {phase === 'instructions' && (
          /* ========================================================
             PHASE 1: INSTRUCTIONS VIEW
             ======================================================== */
          <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
            <Card className="glass-card flex flex-col justify-between p-6 sm:p-8 border-white/10 hover:translate-y-0">
              <div>
                <div className="flex items-start gap-4">
                  <div className="grid size-12 shrink-0 place-items-center rounded-2xl bg-[#8affc4]/10 text-[#8affc4] border border-[#8affc4]/20 shadow-[0_0_15px_rgba(138,255,196,0.1)]">
                    <Camera className="size-5" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">Kamera & Kalibrasi Sinyal</h2>
                    <p className="mt-1.5 text-xs text-[#9eb0c5] leading-relaxed">
                      Sistem menggunakan feed kamera depan untuk mendeteksi variasi fluks hemoglobin wajah yang sangat halus. Mohon posisikan diri Anda sebelum memulai.
                    </p>
                  </div>
                </div>

                {/* Grid of Instruction Cards */}
                <div className="mt-8 grid gap-4 sm:grid-cols-2">
                  {instructions.map((item, index) => (
                    <div
                      key={index}
                      className="group flex flex-col justify-between p-4 rounded-2xl border border-white/6 bg-white/3 hover:bg-white/5 hover:border-white/12 transition-all duration-300"
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-[#8affc4]/10 border border-[#8affc4]/20 group-hover:scale-110 transition-transform">
                          <span className="text-[10px] font-bold text-[#8affc4]">{index + 1}</span>
                        </div>
                        <div>
                          <h3 className="text-xs font-bold text-white leading-normal">{item.text}</h3>
                          <p className="mt-1 text-[11px] leading-relaxed text-[#94a3b8]">{item.desc}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {cameraError ? (
                  <div className="mt-6 flex items-start gap-3 rounded-2xl border border-[#fb7185]/20 bg-[#fb7185]/8 p-4 text-xs leading-relaxed text-[#fecdd3]">
                    <AlertCircle className="mt-0.5 size-4.5 shrink-0 text-[#fb7185]" />
                    <div>
                      <span className="font-bold">Akses Kamera Gagal:</span> {cameraError}
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="mt-10 flex flex-col gap-3 sm:flex-row">
                <Button
                  className="btn-shimmer cta-glow min-h-12 px-6 text-sm font-bold tracking-wide transition-transform hover:scale-[1.02]"
                  disabled={isRequestingCamera}
                  onClick={handleEnableCamera}
                >
                  {isRequestingCamera ? 'Mengaktifkan Lensa Kamera...' : 'Aktifkan Kamera & Mulai'}
                </Button>
                <Button className="min-h-12" onClick={handleBackAction} variant="secondary">
                  Batal
                </Button>
              </div>
            </Card>

            <div className="grid gap-5">
              <DisclaimerBox>
                <div className="flex items-start gap-2.5">
                  <AlertTriangle className="size-4 shrink-0 text-orange-400 mt-0.5" />
                  <p className="text-xs leading-relaxed text-orange-200/90 font-medium">
                    <span className="font-bold text-white">Disclaimer:</span> Luma Vulse merupakan sensor kebugaran fisiologis dan bukan alat medis diagnostik formal.
                  </p>
                </div>
              </DisclaimerBox>
              <Card className="glass-card p-6 border-white/6 hover:translate-y-0">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Sparkles className="size-4 text-[#8affc4]" />
                  Tips Kalibrasi
                </h2>
                <div className="mt-4 space-y-4">
                  <div className="flex gap-3">
                    <div className="size-8 rounded-lg bg-sky-500/10 border border-sky-500/20 grid place-items-center text-sky-400 shrink-0 font-bold text-xs">A</div>
                    <p className="text-xs leading-relaxed text-[#9eb0c5]">
                      <span className="font-semibold text-white">Cahaya Depan:</span> Pastikan sumber cahaya utama berada di depan wajah Anda, bukan di belakang (backlight).
                    </p>
                  </div>
                  <div className="flex gap-3">
                    <div className="size-8 rounded-lg bg-violet-500/10 border border-violet-500/20 grid place-items-center text-violet-400 shrink-0 font-bold text-xs">B</div>
                    <p className="text-xs leading-relaxed text-[#9eb0c5]">
                      <span className="font-semibold text-white">Stabilitas Perangkat:</span> Sandarkan telepon genggam atau laptop pada tempat datar agar ROI deteksi tidak bergeser.
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {phase === 'measuring' && (
          /* ========================================================
             PHASE 2: MEASURING VIEW WITH TELEMETRY OVERLAYS
             ======================================================== */
          <div>
            <header className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
              <div>
                <p className="bento-badge">PPG Telemetry Session</p>
                <h1 className="mt-3 text-3xl font-extrabold text-white tracking-tight">Sinyal Fisiologis Sedang Direkam</h1>
                <p className="mt-2 text-xs text-[#9eb0c5] max-w-2xl leading-relaxed">
                  Harap tetap rileks, kurangi kedipan mata berlebih, dan hadapkan wajah lurus ke depan lensa kamera.
                </p>
              </div>
              <div className="rounded-full border border-[#8affc4]/25 bg-black/45 shadow-[0_0_15px_rgba(138,255,196,0.1)] px-4 py-2 text-xs font-bold text-[#b8ffd9] tracking-wider flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
                </span>
                SYS_REC ACTIVE: {elapsed}s / {duration}s
              </div>
            </header>

            <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
              {/* High-fidelity camera frame with scanline & HUD overlays */}
              <Card className="glass-card p-4 border-[#8affc4]/15 bg-black/35 shadow-[0_0_50px_rgba(138,255,196,0.06)] hover:translate-y-0 relative overflow-hidden">
                <div className="relative aspect-video overflow-hidden rounded-xl bg-slate-950 border border-white/5">
                  <video
                    aria-label="Pratinjau kamera langsung"
                    autoPlay
                    className="h-full w-full scale-x-[-1] object-cover opacity-85"
                    muted
                    playsInline
                    ref={videoRef}
                  />

                  {/* High-tech overlays */}
                  <div className="scanner-scanline" />
                  
                  {/* Digital Brackets */}
                  <div className="camera-bracket camera-bracket-tl" />
                  <div className="camera-bracket camera-bracket-tr" />
                  <div className="camera-bracket camera-bracket-bl" />
                  <div className="camera-bracket camera-bracket-br" />

                  {/* Diagnostic telemetry text overlays */}
                  <div className="absolute top-4 left-4 font-mono text-[9px] tracking-wider text-[#8affc4]/80 bg-black/50 px-2 py-1 rounded border border-white/5 leading-normal">
                    <p className="flex items-center gap-1.5">
                      <span className="inline-block w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                      SYS_STATUS: OPTICAL_LOCK
                    </p>
                    <p className="mt-0.5">EXPOSURE: AUTO_BALANCED</p>
                  </div>

                  <div className="absolute top-4 right-4 font-mono text-[9px] tracking-wider text-[#8affc4]/80 bg-black/50 px-2 py-1 rounded border border-white/5 text-right">
                    <p>FRAME_RATE: 30 FPS</p>
                    <p className="mt-0.5 text-sky-400">QUALITY_SNR: 14.8 dB</p>
                  </div>

                  <div className="pointer-events-none absolute inset-[12%] rounded-[45%] border border-[#8affc4]/40 bg-radial-[circle_at_center,transparent_40%,rgba(138,255,196,0.05)_100%] shadow-[0_0_30px_rgba(138,255,196,0.15)] animate-pulse" />
                  <div className="pointer-events-none absolute left-1/2 top-[22%] h-[12%] w-[22%] -translate-x-1/2 rounded-lg border border-sky-300/60 bg-sky-300/5 shadow-[0_0_12px_rgba(0,165,239,0.15)]" />
                  
                  <div className="absolute bottom-4 left-4 rounded-lg bg-black/80 border border-white/10 px-3 py-1.5 text-[9px] font-bold text-[#b8ffd9] tracking-wider backdrop-blur-md uppercase flex items-center gap-1.5">
                    <UserCheck className="size-3 text-[#8affc4]" />
                    ROI: Cheeks + Forehead Lock
                  </div>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <StatusBadge label="Wajah Terdeteksi" tone={snapshot.faceDetected ? 'success' : 'warning'} value={snapshot.faceDetected ? 'Ya' : 'Mencari...'} />
                  <StatusBadge label="Pencahayaan" tone={qualityTone(snapshot.lighting)} value={qualityLabel[snapshot.lighting]} />
                  <StatusBadge label="Gerakan Wajah" tone={snapshot.motion === 'Low' ? 'success' : 'warning'} value={snapshot.motion === 'Low' ? 'Minimal' : 'Tinggi'} />
                  <StatusBadge label="Kualitas Sinyal" tone={qualityTone(snapshot.signalQuality)} value={qualityLabel[snapshot.signalQuality]} />
                </div>
              </Card>

              {/* Glowing metrics sidepanel cards */}
              <div className="grid gap-4">
                {/* Heart Rate Card with glowing pulses */}
                <div className="relative group overflow-hidden rounded-[20px] border border-sky-500/30 bg-sky-500/10 p-5 shadow-[0_0_25px_rgba(14,165,233,0.15)] backdrop-blur-md animate-[pulse_3s_infinite]">
                  <div className="absolute top-0 right-0 p-3.5 opacity-20">
                    <Heart className="size-10 text-sky-400 animate-[pulse_1s_infinite]" />
                  </div>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-sky-300">Detak Jantung (PPG)</p>
                  <p className="mt-2 text-4xl font-extrabold text-white tracking-tight">{snapshot.heartRate} <span className="text-xs font-semibold text-sky-300">BPM</span></p>
                  <p className="mt-2 text-[10px] text-sky-200/60 leading-normal">Membaca modulasi mikrosirkulasi wajah...</p>
                </div>

                {/* Stress Level Card */}
                <div className="relative group overflow-hidden rounded-[20px] border border-orange-500/20 bg-orange-500/10 p-5 shadow-[0_0_20px_rgba(249,115,22,0.1)] backdrop-blur-md">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-orange-300">Estimasi Stres</p>
                  <p className="mt-2 text-4xl font-extrabold text-white tracking-tight">{stressLabel[snapshot.stressLevel]}</p>
                  <p className="mt-2 text-[10px] text-orange-200/60 leading-normal">Mengkalibrasi fluktuasi interval detak (HRV).</p>
                </div>

                <MetricCard label="Confidence Level" value={`${Math.round(snapshot.confidence * 100)}%`} />
                <MetricCard label="Kualitas Sinyal" tone={qualityTone(snapshot.signalQuality)} value={qualityLabel[snapshot.signalQuality]} />
              </div>
            </div>

            {/* Smooth live scrolling Waveform Simulator below */}
            <Card className="glass-card border-white/8 bg-black/25 p-5 md:p-6 mt-6 hover:translate-y-0">
              <div className="flex items-center justify-between gap-4 border-b border-white/6 pb-3 mb-4">
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">Feed Telemetri Gelombang PPG (Live)</h3>
                  <p className="text-[10px] text-[#9eb0c5] mt-0.5">Gelombang pulsa kapiler terdeteksi secara non-kontak.</p>
                </div>
                <span className="rounded-full bg-[#8affc4]/10 border border-[#8affc4]/20 px-2.5 py-0.5 text-[9px] font-bold text-[#8affc4] tracking-wide uppercase">
                  Telemetry Streaming
                </span>
              </div>
              <div className="h-44">
                <ResponsiveContainer height="100%" width="100%">
                  <LineChart data={liveWaveData} margin={{ bottom: 0, left: -20, right: 12, top: 12 }}>
                    <defs>
                      <filter id="live-glow-filter" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="0" dy="0" stdDeviation="3.5" floodColor="#8affc4" floodOpacity="0.8" />
                      </filter>
                    </defs>
                    <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                    <XAxis dataKey="second" stroke="#475569" tickLine={false} tick={{ fontSize: 9 }} />
                    <YAxis stroke="#475569" tickLine={false} tick={{ fontSize: 9 }} domain={[0.2, 0.8]} />
                    <Line
                      dataKey="value"
                      dot={false}
                      stroke="#8affc4"
                      strokeWidth={2.5}
                      type="monotone"
                      filter="url(#live-glow-filter)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card className="glass-card mt-6 border-white/8 bg-black/30 hover:translate-y-0">
              <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-center">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between text-xs font-semibold text-[#94a3b8] mb-2">
                    <span>Progres Pengukuran Fisiologis</span>
                    <span className="font-bold text-white">{Math.round((elapsed / duration) * 100)}% Selesai</span>
                  </div>
                  <ProgressBar label="Progress pengukuran" max={duration} value={elapsed} />
                  {snapshot.signalQuality === 'Poor' ? (
                    <div className="mt-3 flex items-start gap-2 text-xs leading-relaxed text-[#fb7185]/90">
                      <AlertTriangle className="size-4 shrink-0 text-[#fb7185] mt-0.5" />
                      <p>Sinyal terganggu karena bayangan atau gerakan wajah. Harap tetap tegak dan rileks.</p>
                    </div>
                  ) : null}
                </div>
                <div className="flex flex-col gap-3 sm:flex-row shrink-0">
                  <Button disabled={isFinishing} onClick={handleStop} variant="danger" className="min-h-12 hover:scale-[1.03]">
                    Stop & Dapatkan Hasil
                  </Button>
                  <Button disabled={isFinishing} onClick={handleRestart} variant="secondary" className="min-h-12 hover:scale-[1.03]">
                    <RotateCcw className="mr-1.5 size-3.5" />
                    Ulangi
                  </Button>
                  <Button disabled={isFinishing} onClick={handleBackToInstructions} variant="ghost" className="min-h-12 text-white/50 hover:text-white">
                    Batal
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        )}

        {phase === 'result' && measurementResult && (
          /* ========================================================
             PHASE 3: RESULT VIEW WITH RADIAL PROGRESS RING
             ======================================================== */
          <div>
            <header className="mb-8 text-center max-w-3xl mx-auto">
              <span className="lp-badge">Report Summary</span>
              <h1 className="mx-auto mt-4 max-w-4xl bg-gradient-to-b from-white via-white to-[#94a3b8] bg-clip-text text-3xl font-extrabold leading-tight text-transparent sm:text-4xl tracking-tight">
                Laporan Estimasi Stres Fisiologis
              </h1>
              <p className="mx-auto mt-2.5 text-xs leading-relaxed text-[#9eb0c5]">
                Informasi analisis biometrik laju denyut jantung dan fluktuasi indeks stress sistem saraf otonom.
              </p>
            </header>

            <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
              {/* Glowing Dynamic Border card based on final stress category */}
              <Card className={`glass-card p-6 sm:p-8 border flex flex-col justify-between hover:translate-y-0 transition-all duration-700 ${stressGlowClass}`}>
                <div className="flex flex-col gap-6 sm:flex-row sm:items-center justify-between">
                  <div className="max-w-md">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-[#8affc4]">Kategori Tingkat Stres</p>
                    <h2 className="mt-2 text-4xl font-extrabold text-white tracking-tight">{stressLabel[measurementResult.stressLevel]}</h2>
                    <p className="mt-4 text-xs leading-relaxed text-[#d4d4d8] font-medium">{measurementResult.physiologicalMessage}</p>
                  </div>
                  
                  {/* Glowing Circular Radial Gauge with Draw Animation */}
                  <div className="relative flex items-center justify-center shrink-0 p-2 border border-white/5 bg-white/3 rounded-3xl shadow-lg">
                    <svg className="w-32 h-32 transform -rotate-90">
                      <circle
                        cx="64"
                        cy="64"
                        r={radius}
                        className="text-white/5"
                        strokeWidth="8"
                        stroke="currentColor"
                        fill="transparent"
                      />
                      <circle
                        cx="64"
                        cy="64"
                        r={radius}
                        className="text-[#8affc4] drop-shadow-[0_0_8px_rgba(138,255,196,0.6)]"
                        strokeWidth="8"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        strokeLinecap="round"
                        stroke="currentColor"
                        fill="transparent"
                        style={{ transition: 'stroke-dashoffset 1.6s cubic-bezier(0.16, 1, 0.3, 1)' }}
                      />
                    </svg>
                    <div className="absolute flex flex-col items-center justify-center text-center">
                      <span className="text-3xl font-extrabold text-white tracking-tighter leading-none">{animatedScore}</span>
                      <span className="text-[9px] font-bold text-[#94a3b8] uppercase tracking-wider mt-1">Stress Score</span>
                    </div>
                  </div>
                </div>

                <div className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  <MetricCard label="Heart Rate Average" tone="info" value={`${measurementResult.heartRate} BPM`} />
                  <MetricCard label="Confidence Level" value={`${Math.round(measurementResult.confidence * 100)}%`} />
                  <MetricCard label="Signal Quality" tone={qualityTone(measurementResult.signalQuality)} value={qualityLabel[measurementResult.signalQuality]} />
                  <MetricCard label="Durasi Perekaman" value={`${measurementResult.duration} detik`} />
                  <MetricCard label="Timestamp Sesi" helper={formatTimestamp(measurementResult.timestamp)} value="Selesai" />
                  <MetricCard label="Stress Kategori" tone={stressTone(measurementResult.stressLevel)} value={stressLabel[measurementResult.stressLevel]} />
                </div>

                {measurementResult.signalQuality === 'Poor' ? (
                  <div className="mt-6 rounded-xl border border-orange-400/25 bg-orange-400/10 p-4 text-xs leading-relaxed text-orange-200">
                    Kualitas sinyal selama pengukuran dinilai kurang stabil. Silakan ulangi dengan memastikan ruangan terang benderang dan hadapkan wajah lurus tenang ke depan.
                  </div>
                ) : null}
              </Card>

              {/* Sidebar Action Guidelines */}
              <div className="grid gap-5">
                <DisclaimerBox>
                  <p className="text-xs leading-relaxed text-orange-200/90 font-medium">
                    <span className="font-bold text-white">Catatan:</span> Variabilitas Denyut Jantung (HRV) dipengaruhi banyak faktor eksternal seperti kafein, kecukupan tidur, hidrasi, suhu, dan aktivitas fisik terbaru.
                  </p>
                </DisclaimerBox>
                
                <Card className="glass-card p-6 border-white/6 hover:translate-y-0">
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <TrendingUp className="size-4 text-[#8affc4]" />
                    Aksi Pengukuran
                  </h2>
                  <div className="mt-4 grid gap-3">
                    <Button className="btn-shimmer cta-glow min-h-11 font-bold" onClick={handleEnableCamera}>
                      Ulangi Pengukuran
                    </Button>
                    <Button
                      onClick={() => setSaveMessage('Penyimpanan lokal atau cloud dinonaktifkan dalam mode pratinjau akademik.')}
                      variant="secondary"
                      className="min-h-11 font-bold"
                    >
                      Simpan File Laporan
                    </Button>
                    <Button
                      onClick={handleBackToInstructions}
                      variant="ghost"
                      className="min-h-11 text-white/50 hover:text-white"
                    >
                      Kembali ke Persiapan
                    </Button>
                  </div>
                  {saveMessage ? <p className="mt-4 text-[11px] leading-relaxed text-[#9eb0c5] text-center">{saveMessage}</p> : null}
                </Card>
              </div>
            </div>

            {/* Glowing Neon Recharts Grid (Loaded below summary in result phase) */}
            {signalDetails && (
              <div className="mt-8 grid gap-6 md:grid-cols-3">
                <ChartCard
                  color="#8affc4"
                  glowColor="rgba(138, 255, 196, 0.8)"
                  glowFilterId="glow-rppg-neon"
                  data={signalDetails.rppgSignal}
                  title="rPPG Signal Waveform"
                  unit="Normalized"
                />
                <ChartCard
                  color="#00a5ef"
                  glowColor="rgba(0, 165, 239, 0.8)"
                  glowFilterId="glow-hr-neon"
                  data={signalDetails.heartRateTrend}
                  title="Heart Rate Trendline"
                  unit="BPM"
                />
                <ChartCard
                  color="#4f39f6"
                  glowColor="rgba(79, 57, 246, 0.8)"
                  glowFilterId="glow-quality-neon"
                  data={signalDetails.qualityTrend}
                  title="Signal Quality Index"
                  unit="Confidence"
                />
              </div>
            )}

            {/* Glassmorphic Feature Table */}
            {signalDetails && (
              <Card className="glass-card mt-8 border-white/8 bg-black/25 hover:translate-y-0">
                <h2 className="text-base font-bold text-white uppercase tracking-wider">Matriks Deteksi HRV</h2>
                <p className="mt-1 text-xs text-[#9eb0c5]">Fitur konvolusi spektral domain waktu dan frekuensi hasil sesi.</p>
                
                <div className="mt-6 overflow-x-auto rounded-xl border border-white/6 bg-white/2">
                  <table className="w-full min-w-[720px] border-collapse text-left text-xs leading-normal">
                    <thead>
                      <tr className="border-b border-white/8 bg-white/4 text-[#94a3b8] uppercase font-bold tracking-wider">
                        <th className="px-5 py-3.5">Metrik Fisiologis</th>
                        <th className="px-5 py-3.5">Nilai Sensor</th>
                        <th className="px-5 py-3.5">Status Deteksi</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(Object.entries(signalDetails.features) as Array<[keyof SignalDetails['features'], number]>).map(([key, value]) => (
                        <tr className="border-b border-white/5 hover:bg-white/3 transition-colors last:border-b-0" key={key}>
                          <td className="px-5 py-4 font-bold text-white flex items-center gap-2">
                            <CheckCircle2 className="size-4 text-[#8affc4]/80" />
                            {featureLabels[key]}
                          </td>
                          <td className="px-5 py-4 text-[#d4d4d8] font-mono font-semibold text-xs">{value}</td>
                          <td className="px-5 py-4 text-[#9eb0c5] italic">Mock telemetry payload, siap dihubungkan dengan integrasi backend.</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </main>
  )
}
