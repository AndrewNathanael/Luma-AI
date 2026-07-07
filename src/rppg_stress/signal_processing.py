"""Signal processing functions for rPPG and PRV/HRV analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from scipy import signal


EPS = 1e-8


@dataclass
class HeartRateEstimate:
    bpm: float
    peak_frequency_hz: float
    quality: float
    n_samples: int


def fill_nan_linear(x: np.ndarray) -> np.ndarray:
    # Fill NaN values using linear interpolation.
    x = np.asarray(x, dtype=float).copy()
    if x.ndim != 1:
        raise ValueError("fill_nan_linear expects a 1D array")
    n = len(x)
    if n == 0:
        return x
    idx = np.arange(n)
    finite = np.isfinite(x)
    if finite.all():
        return x
    if finite.sum() == 0:
        return np.zeros_like(x)
    x[~finite] = np.interp(idx[~finite], idx[finite], x[finite])
    return x


def standardize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return (x - np.nanmean(x)) / (np.nanstd(x) + EPS)


def detrend_signal(x: np.ndarray) -> np.ndarray:
    x = fill_nan_linear(np.asarray(x, dtype=float))
    if len(x) < 3:
        return x - np.mean(x)
    return signal.detrend(x, type="linear")


def bandpass_filter(
    x: np.ndarray,
    fs: float,
    low_hz: float = 0.7,
    high_hz: float = 4.0,
    order: int = 4,
) -> np.ndarray:
    # Zero-phase Butterworth bandpass filter using second-order sections
    x = detrend_signal(x)
    if fs <= 0:
        raise ValueError("Sampling frequency fs must be positive")
    nyquist = 0.5 * fs
    low = max(low_hz / nyquist, 1e-5)
    high = min(high_hz / nyquist, 0.99999)
    if not 0 < low < high < 1:
        raise ValueError(
            f"Invalid bandpass range: low={low_hz} Hz, high={high_hz} Hz, fs={fs} Hz"
        )
    sos = signal.butter(order, [low, high], btype="bandpass", output="sos")
    padlen = min(max(0, len(x) - 1), 3 * (2 * len(sos) + 1))
    if len(x) < 8:
        return x - np.mean(x)
    return signal.sosfiltfilt(sos, x, padlen=padlen)


def power_spectral_density(
    x: np.ndarray,
    fs: float,
    nperseg: int | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    x = fill_nan_linear(np.asarray(x, dtype=float))
    if nperseg is None:
        nperseg = min(len(x), int(round(fs * 16)))
    nperseg = max(8, min(nperseg, len(x)))
    freqs, power = signal.welch(x, fs=fs, nperseg=nperseg, detrend="constant")
    return freqs, power


def estimate_hr_from_signal(
    bvp: np.ndarray,
    fs: float,
    low_hz: float = 0.7,
    high_hz: float = 4.0,
) -> HeartRateEstimate:
    """Estimate heart rate by choosing the strongest PSD peak in the HR band."""
    if len(bvp) < max(8, int(fs * 4)):
        return HeartRateEstimate(np.nan, np.nan, 0.0, len(bvp))

    filtered = bandpass_filter(bvp, fs, low_hz, high_hz)
    freqs, power = power_spectral_density(filtered, fs)
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    if mask.sum() == 0:
        return HeartRateEstimate(np.nan, np.nan, 0.0, len(bvp))

    band_freqs = freqs[mask]
    band_power = power[mask]
    peak_idx = int(np.argmax(band_power))
    peak_freq = float(band_freqs[peak_idx])
    bpm = peak_freq * 60.0

    total_power = float(np.sum(band_power) + EPS)
    peak_power = float(band_power[peak_idx])
    quality = peak_power / total_power
    return HeartRateEstimate(bpm=bpm, peak_frequency_hz=peak_freq, quality=quality, n_samples=len(bvp))


def detect_pulse_peaks(
    bvp: np.ndarray,
    fs: float,
    low_hz: float = 0.7,
    high_hz: float = 4.0,
) -> np.ndarray:
    """Detect pulse peaks from a filtered BVP/rPPG signal."""
    if len(bvp) < int(fs * 4):
        return np.array([], dtype=int)
    x = bandpass_filter(bvp, fs, low_hz, high_hz)
    x = standardize(x)
    min_distance = max(1, int(round(fs * 0.30)))  # about 200 BPM maximum
    prominence = max(0.15, 0.35 * float(np.nanstd(x)))
    peaks, _ = signal.find_peaks(x, distance=min_distance, prominence=prominence)
    return peaks.astype(int)


def compute_snr_proxy(
    bvp: np.ndarray,
    fs: float,
    low_hz: float = 0.7,
    high_hz: float = 4.0,
) -> float:
    """Return a simple signal-quality proxy based on PSD peak dominance."""
    hr = estimate_hr_from_signal(bvp, fs, low_hz, high_hz)
    if not np.isfinite(hr.quality):
        return 0.0
    return float(np.clip(hr.quality, 0.0, 1.0))
