"""Classical rPPG algorithms: GREEN, CHROM, and POS."""

from __future__ import annotations

from typing import Literal

import numpy as np

from .signal_processing import EPS, bandpass_filter, fill_nan_linear, standardize


RPPGMethod = Literal["green", "chrom", "pos"]


def _validate_rgb(rgb: np.ndarray) -> np.ndarray:
    rgb = np.asarray(rgb, dtype=float)
    if rgb.ndim != 2 or rgb.shape[1] != 3:
        raise ValueError("rgb must have shape (n_frames, 3) in RGB channel order")
    out = np.empty_like(rgb, dtype=float)
    for c in range(3):
        out[:, c] = fill_nan_linear(rgb[:, c])
    return out


def _sliding_window_indices(n: int, window: int, step: int = 1):
    if window <= 1 or n < window:
        yield 0, n
        return
    for start in range(0, n - window + 1, step):
        yield start, start + window


def green_rppg(
    rgb: np.ndarray,
    fs: float,
    low_hz: float = 0.7,
    high_hz: float = 4.0,
) -> np.ndarray:
    """Simple green-channel baseline."""
    rgb = _validate_rgb(rgb)
    green = rgb[:, 1]
    green = standardize(green)
    return bandpass_filter(green, fs, low_hz, high_hz)


def chrom_rppg(
    rgb: np.ndarray,
    fs: float,
    low_hz: float = 0.7,
    high_hz: float = 4.0,
    window_seconds: float = 1.6,
) -> np.ndarray:
    """Chrominance-based rPPG using overlap-add windows."""
    rgb = _validate_rgb(rgb)
    n = rgb.shape[0]
    window = max(8, int(round(window_seconds * fs)))
    if n < window:
        window = n

    h = np.zeros(n, dtype=float)
    weights = np.zeros(n, dtype=float)

    for start, end in _sliding_window_indices(n, window, step=1):
        c = rgb[start:end].copy()
        c = c / (np.mean(c, axis=0, keepdims=True) + EPS) - 1.0
        r, g, b = c[:, 0], c[:, 1], c[:, 2]
        x = 3.0 * r - 2.0 * g
        y = 1.5 * r + g - 1.5 * b
        alpha = np.std(x) / (np.std(y) + EPS)
        s = x - alpha * y
        s = s - np.mean(s)
        h[start:end] += s
        weights[start:end] += 1.0

    h = h / (weights + EPS)
    return bandpass_filter(h, fs, low_hz, high_hz)


def pos_rppg(
    rgb: np.ndarray,
    fs: float,
    low_hz: float = 0.7,
    high_hz: float = 4.0,
    window_seconds: float = 1.6,
) -> np.ndarray:
    """Plane-Orthogonal-to-Skin (POS) rPPG using overlap-add windows."""
    rgb = _validate_rgb(rgb)
    n = rgb.shape[0]
    window = max(8, int(round(window_seconds * fs)))
    if n < window:
        window = n

    h = np.zeros(n, dtype=float)
    weights = np.zeros(n, dtype=float)

    # Projection matrix used in the POS method.
    projection = np.array([[0.0, 1.0, -1.0], [-2.0, 1.0, 1.0]])

    for start, end in _sliding_window_indices(n, window, step=1):
        c = rgb[start:end].copy()
        c = c / (np.mean(c, axis=0, keepdims=True) + EPS) - 1.0
        s = projection @ c.T  # shape: (2, window)
        alpha = np.std(s[0]) / (np.std(s[1]) + EPS)
        pulse = s[0] + alpha * s[1]
        pulse = pulse - np.mean(pulse)
        h[start:end] += pulse
        weights[start:end] += 1.0

    h = h / (weights + EPS)
    return bandpass_filter(h, fs, low_hz, high_hz)


def extract_rppg(
    rgb: np.ndarray,
    fs: float,
    method: RPPGMethod = "pos",
    low_hz: float = 0.7,
    high_hz: float = 4.0,
    pos_window_seconds: float = 1.6,
    chrom_window_seconds: float = 1.6,
) -> np.ndarray:
    """Dispatch function for rPPG extraction."""
    method = method.lower().strip()
    if method == "green":
        return green_rppg(rgb, fs, low_hz, high_hz)
    if method == "chrom":
        return chrom_rppg(rgb, fs, low_hz, high_hz, chrom_window_seconds)
    if method == "pos":
        return pos_rppg(rgb, fs, low_hz, high_hz, pos_window_seconds)
    raise ValueError(f"Unknown rPPG method: {method}")
