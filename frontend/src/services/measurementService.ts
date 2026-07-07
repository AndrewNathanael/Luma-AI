export type StressLevel = 'Low' | 'Moderate' | 'High'
export type SignalQuality = 'Good' | 'Moderate' | 'Poor'
export type LightingQuality = 'Good' | 'Moderate' | 'Poor'
export type MotionLevel = 'Low' | 'High'

export type MeasurementFeatures = {
  meanHr: number
  sdnn: number
  rmssd: number
  pnn50: number
  lfPower: number
  hfPower: number
  lfHfRatio: number
  snrProxy: number
  detectionRate: number
}

export type MeasurementResult = {
  heartRate: number
  stressLevel: StressLevel
  stressScore: number
  confidence: number
  signalQuality: SignalQuality
  duration: number
  timestamp: string
  physiologicalMessage: string
  features: MeasurementFeatures
}

export type LiveMeasurementSnapshot = {
  heartRate: number
  stressLevel: StressLevel | 'Measuring'
  confidence: number
  signalQuality: SignalQuality
  lighting: LightingQuality
  motion: MotionLevel
  faceDetected: boolean
}

export type MeasurementSession = {
  id: string
  startedAt: string
}

export type SignalPoint = {
  second: number
  value: number
}

export type SignalDetails = {
  rppgSignal: SignalPoint[]
  heartRateTrend: SignalPoint[]
  qualityTrend: SignalPoint[]
  features: MeasurementFeatures
}

const defaultFeatures: MeasurementFeatures = {
  meanHr: 84,
  sdnn: 42,
  rmssd: 28,
  pnn50: 12,
  lfPower: 0.42,
  hfPower: 0.31,
  lfHfRatio: 1.35,
  snrProxy: 0.72,
  detectionRate: 0.94,
}

const messages: Record<StressLevel, string> = {
  Low: 'Indikator fisiologis menunjukkan kemungkinan stres rendah.',
  Moderate: 'Indikator fisiologis menunjukkan kemungkinan stres sedang.',
  High: 'Indikator fisiologis menunjukkan kemungkinan stres tinggi. Pertimbangkan untuk mengulang pengukuran setelah kondisi lebih stabil.',
}

function bounded(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function inferStressLevel(score: number): StressLevel {
  if (score >= 72) return 'High'
  if (score >= 45) return 'Moderate'
  return 'Low'
}

function inferSignalQuality(confidence: number): SignalQuality {
  if (confidence >= 0.78) return 'Good'
  if (confidence >= 0.56) return 'Moderate'
  return 'Poor'
}

export async function startMeasurement(): Promise<MeasurementSession> {
  // TODO: Replace this mock session with a backend call such as POST /measurements/start.
  return {
    id: crypto.randomUUID(),
    startedAt: new Date().toISOString(),
  }
}

export async function stopMeasurement(sessionId?: string): Promise<void> {
  // TODO: Replace this mock stop with a backend call such as POST /measurements/{id}/stop.
  void sessionId
  return Promise.resolve()
}

export function getLiveMeasurementSnapshot(elapsedSeconds: number): LiveMeasurementSnapshot {
  const signalWarmup = bounded(elapsedSeconds / 12, 0, 1)
  const heartRate = Math.round(78 + Math.sin(elapsedSeconds / 5) * 5 + signalWarmup * 4)
  const confidence = bounded(0.48 + signalWarmup * 0.34 + Math.sin(elapsedSeconds / 9) * 0.04, 0.42, 0.9)
  const signalQuality = inferSignalQuality(confidence)
  const stressScore = bounded(58 + Math.sin(elapsedSeconds / 8) * 10 + signalWarmup * 5, 35, 82)

  return {
    heartRate,
    stressLevel: elapsedSeconds < 3 ? 'Measuring' : inferStressLevel(stressScore),
    confidence,
    signalQuality,
    lighting: elapsedSeconds < 4 ? 'Moderate' : signalQuality === 'Poor' ? 'Poor' : 'Good',
    motion: elapsedSeconds > 0 && elapsedSeconds % 19 > 15 ? 'High' : 'Low',
    faceDetected: elapsedSeconds >= 2,
  }
}

export async function getMeasurementResult(_sessionId?: string, duration = 60): Promise<MeasurementResult> {
  // TODO: Replace this mock result with GET /measurements/{id}/result once the backend is ready.
  const confidence = 0.78
  const stressScore = 67
  const stressLevel = inferStressLevel(stressScore)

  return {
    heartRate: 84,
    stressLevel,
    stressScore,
    confidence,
    signalQuality: inferSignalQuality(confidence),
    duration,
    timestamp: new Date().toISOString(),
    physiologicalMessage: messages[stressLevel],
    features: defaultFeatures,
  }
}

export async function getSignalDetails(): Promise<SignalDetails> {
  // TODO: Replace sample chart data with backend rPPG signal and HRV feature payloads.
  const rppgSignal = Array.from({ length: 60 }, (_, index) => ({
    second: index + 1,
    value: Number((0.52 + Math.sin(index / 2.8) * 0.12 + Math.sin(index / 7) * 0.04).toFixed(3)),
  }))

  const heartRateTrend = Array.from({ length: 12 }, (_, index) => ({
    second: (index + 1) * 5,
    value: Math.round(80 + Math.sin(index / 1.8) * 5 + index * 0.3),
  }))

  const qualityTrend = Array.from({ length: 12 }, (_, index) => ({
    second: (index + 1) * 5,
    value: Number((0.64 + Math.sin(index / 2.4) * 0.08 + index * 0.012).toFixed(2)),
  }))

  return {
    rppgSignal,
    heartRateTrend,
    qualityTrend,
    features: defaultFeatures,
  }
}
