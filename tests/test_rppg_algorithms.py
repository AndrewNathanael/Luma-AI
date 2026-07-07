from __future__ import annotations

import numpy as np

from rppg_stress.rppg_algorithms import extract_rppg


def test_rppg_methods_output_shape():
    fs = 30.0
    n = 300
    t = np.arange(n) / fs
    pulse = 0.01 * np.sin(2 * np.pi * 1.2 * t)
    rgb = np.column_stack([
        100 + 0.3 * pulse,
        110 + 1.0 * pulse,
        120 + 0.2 * pulse,
    ])
    for method in ["green", "chrom", "pos"]:
        y = extract_rppg(rgb, fs, method=method)
        assert y.shape == (n,)
        assert np.isfinite(y).all()
