"""Feature extraction for pulse rate variability and stress classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd
from scipy import signal

from .signal_processing import EPS, compute_snr_proxy, detect_pulse_peaks, estimate_hr_from_signal


@dataclass
class FeatureConfig:
    window_seconds: float = 60.0
    step_seconds: float = 10.0
    interpolate_rate_hz: float = 4.0
    min_valid_beats: int = 10
    low_hz: float = 0.7
    high_hz: float = 4.0


def extract_windowed_features(
    bvp: np.ndarray,
    fs: float,
    config: FeatureConfig | None = None,
) -> pd.DataFrame:
    """Extract PRV/HRV-like features from rPPG BVP in sliding windows."""
    if config is None:
        config = FeatureConfig()

    bvp = np.asarray(bvp, dtype=float)
    n = len(bvp)
    win = max(1, int(round(config.window_seconds * fs)))
    step = max(1, int(round(config.step_seconds * fs)))
    rows: List[Dict[str, float]] = []

    if n < win:
        start_indices = [0]
        win = n
    else:
        start_indices = list(range(0, n - win + 1, step))

    for start in start_indices:
        end = min(start + win, n)
        segment = bvp[start:end]
        features = extract_features_single_window(
            segment,
            fs=fs,
            interpolate_rate_hz=config.interpolate_rate_hz,
            min_valid_beats=config.min_valid_beats,
            low_hz=config.low_hz,
            high_hz=config.high_hz,
        )
        features["window_start_sec"] = start / fs
        features["window_end_sec"] = end / fs
        features["window_duration_sec"] = (end - start) / fs
        rows.append(features)

    return pd.DataFrame(rows)


def extract_features_single_window(
    segment: np.ndarray,
    fs: float,
    interpolate_rate_hz: float = 4.0,
    min_valid_beats: int = 10,
    low_hz: float = 0.7,
    high_hz: float = 4.0,
) -> Dict[str, float]:
    """Compute HR, time-domain PRV, frequency-domain PRV, and quality features."""
    segment = np.asarray(segment, dtype=float)
    hr_est = estimate_hr_from_signal(segment, fs, low_hz, high_hz)
    peaks = detect_pulse_peaks(segment, fs, low_hz, high_hz)

    out: Dict[str, float] = {
        "mean_hr_bpm": float(hr_est.bpm),
        "hr_psd_quality": float(hr_est.quality),
        "snr_proxy": float(compute_snr_proxy(segment, fs, low_hz, high_hz)),
        "n_peaks": float(len(peaks)),
        "peak_rate_per_sec": float(len(peaks) / max(len(segment) / fs, EPS)),
    }

    if len(peaks) < min_valid_beats:
        out.update(_nan_prv_features())
        return out

    peak_times = peaks / fs
    ibi_all = np.diff(peak_times)  # seconds
    valid = (ibi_all >= 0.30) & (ibi_all <= 2.00)
    ibi = ibi_all[valid]
    ibi_times = peak_times[1:][valid]
    if len(ibi) < max(3, min_valid_beats - 1):
        out.update(_nan_prv_features())
        return out

    ibi_ms = ibi * 1000.0
    diff_ms = np.diff(ibi_ms)
    out.update(
        {
            "ibi_mean_ms": float(np.mean(ibi_ms)),
            "ibi_median_ms": float(np.median(ibi_ms)),
            "ibi_std_ms": float(np.std(ibi_ms, ddof=1)) if len(ibi_ms) > 1 else np.nan,
            "sdnn_ms": float(np.std(ibi_ms, ddof=1)) if len(ibi_ms) > 1 else np.nan,
            "rmssd_ms": float(np.sqrt(np.mean(diff_ms**2))) if len(diff_ms) > 0 else np.nan,
            "pnn50": float(np.mean(np.abs(diff_ms) > 50.0)) if len(diff_ms) > 0 else np.nan,
            "prv_mean_hr_bpm": float(60.0 / (np.mean(ibi) + EPS)),
            "prv_min_hr_bpm": float(60.0 / (np.max(ibi) + EPS)),
            "prv_max_hr_bpm": float(60.0 / (np.min(ibi) + EPS)),
        }
    )
    out.update(_frequency_domain_features(ibi_times, ibi, interpolate_rate_hz))
    out.update(_poincare_features(ibi_ms))
    return out


def _nan_prv_features() -> Dict[str, float]:
    keys = [
        "ibi_mean_ms",
        "ibi_median_ms",
        "ibi_std_ms",
        "sdnn_ms",
        "rmssd_ms",
        "pnn50",
        "prv_mean_hr_bpm",
        "prv_min_hr_bpm",
        "prv_max_hr_bpm",
        "lf_power",
        "hf_power",
        "lf_hf_ratio",
        "total_power",
        "sd1_ms",
        "sd2_ms",
        "sd1_sd2_ratio",
    ]
    return {k: np.nan for k in keys}


def _frequency_domain_features(
    ibi_times: np.ndarray,
    ibi: np.ndarray,
    interpolate_rate_hz: float,
) -> Dict[str, float]:
    """Estimate LF/HF PRV features by interpolating tachogram."""
    # IBI values are associated with timestamps between consecutive beats.
    if len(ibi) < 4:
        return {"lf_power": np.nan, "hf_power": np.nan, "lf_hf_ratio": np.nan, "total_power": np.nan}

    if len(ibi_times) != len(ibi) or len(ibi_times) < 4:
        return {"lf_power": np.nan, "hf_power": np.nan, "lf_hf_ratio": np.nan, "total_power": np.nan}

    duration = float(ibi_times[-1] - ibi_times[0])
    if duration < 20.0:
        return {"lf_power": np.nan, "hf_power": np.nan, "lf_hf_ratio": np.nan, "total_power": np.nan}

    interp_times = np.arange(ibi_times[0], ibi_times[-1], 1.0 / interpolate_rate_hz)
    if len(interp_times) < 16:
        return {"lf_power": np.nan, "hf_power": np.nan, "lf_hf_ratio": np.nan, "total_power": np.nan}

    tachogram = np.interp(interp_times, ibi_times, ibi)
    tachogram = signal.detrend(tachogram - np.mean(tachogram))
    nperseg = min(len(tachogram), int(interpolate_rate_hz * 64))
    freqs, psd = signal.welch(tachogram, fs=interpolate_rate_hz, nperseg=nperseg)

    lf_mask = (freqs >= 0.04) & (freqs < 0.15)
    hf_mask = (freqs >= 0.15) & (freqs < 0.40)
    lf = _band_power(freqs, psd, lf_mask)
    hf = _band_power(freqs, psd, hf_mask)
    total = _band_power(freqs, psd, (freqs >= 0.04) & (freqs < 0.40))
    return {
        "lf_power": float(lf),
        "hf_power": float(hf),
        "lf_hf_ratio": float(lf / (hf + EPS)),
        "total_power": float(total),
    }


def _band_power(freqs: np.ndarray, psd: np.ndarray, mask: np.ndarray) -> float:
    if mask.sum() < 2:
        return float(np.nan)
    return float(np.trapezoid(psd[mask], freqs[mask]))


def _poincare_features(ibi_ms: np.ndarray) -> Dict[str, float]:
    if len(ibi_ms) < 3:
        return {"sd1_ms": np.nan, "sd2_ms": np.nan, "sd1_sd2_ratio": np.nan}
    diff = np.diff(ibi_ms)
    sd1 = np.sqrt(np.var(diff, ddof=1) / 2.0) if len(diff) > 1 else np.nan
    sdnn = np.std(ibi_ms, ddof=1)
    sd2_sq = max(0.0, 2.0 * sdnn**2 - sd1**2) if np.isfinite(sd1) else np.nan
    sd2 = np.sqrt(sd2_sq) if np.isfinite(sd2_sq) else np.nan
    return {
        "sd1_ms": float(sd1),
        "sd2_ms": float(sd2),
        "sd1_sd2_ratio": float(sd1 / (sd2 + EPS)) if np.isfinite(sd1) and np.isfinite(sd2) else np.nan,
    }


def feature_columns(df: pd.DataFrame) -> list[str]:
    """Return numerical model feature columns, excluding metadata and labels."""
    excluded = {
        "subject_id",
        "video_path",
        "condition",
        "label",
        "window_start_sec",
        "window_end_sec",
        "window_duration_sec",
    }
    return [c for c in df.columns if c not in excluded and pd.api.types.is_numeric_dtype(df[c])]
