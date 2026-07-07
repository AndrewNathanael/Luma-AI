from __future__ import annotations

import numpy as np

from rppg_stress.signal_processing import estimate_hr_from_signal
from rppg_stress.features import extract_features_single_window


def test_estimate_hr_from_synthetic_signal():
    fs = 30.0
    duration = 60.0
    t = np.arange(0, duration, 1 / fs)
    bpm = 72.0
    x = np.sin(2 * np.pi * (bpm / 60.0) * t)
    estimate = estimate_hr_from_signal(x, fs)
    assert abs(estimate.bpm - bpm) < 5.0


def test_feature_extraction_returns_expected_keys():
    fs = 30.0
    t = np.arange(0, 60.0, 1 / fs)
    x = np.sin(2 * np.pi * 1.2 * t)
    features = extract_features_single_window(x, fs, min_valid_beats=5)
    assert "mean_hr_bpm" in features
    assert "rmssd_ms" in features
    assert "snr_proxy" in features
