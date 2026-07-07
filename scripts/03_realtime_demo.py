#!/usr/bin/env python
"""Real-time webcam demo for rPPG stress estimation."""

from __future__ import annotations

import argparse
import time
from collections import deque
from typing import Optional

import cv2
import numpy as np
import pandas as pd

from rppg_stress.features import extract_features_single_window
from rppg_stress.ml import ModelBundle, load_model_bundle, predict_from_features
from rppg_stress.roi import FaceRoiExtractor, draw_roi_overlay
from rppg_stress.rppg_algorithms import extract_rppg
from rppg_stress.signal_processing import estimate_hr_from_signal
from rppg_stress.utils import deep_get, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="Optional saved joblib model")
    parser.add_argument("--config", default="config/default.yaml", help="YAML config path")
    parser.add_argument("--camera", type=int, default=0, help="Webcam index")
    parser.add_argument("--width", type=int, default=None, help="Camera frame width (default: None - use camera native resolution)")
    parser.add_argument("--height", type=int, default=None, help="Camera frame height (default: None - use camera native resolution)")
    parser.add_argument("--display-scale", type=float, default=1.0, help="Resize display window")
    parser.add_argument("--min-quality", type=float, default=0.60, help="Minimum signal quality before prediction")
    parser.add_argument("--min-detection", type=float, default=0.90, help="Minimum face detection rate before prediction")
    parser.add_argument(
        "--camera-flip",
        choices=["none", "horizontal", "vertical", "both"],
        default=None,
        help="Correct webcam orientation when the image appears mirrored or upside down",
    )
    return parser.parse_args()


def label_to_text(label: int) -> str:
    mapping = {
        0: "Normal",
        1: "Moderate arousal",
        2: "High arousal",
    }
    return mapping.get(int(label), f"Class {label}")


def get_prediction_confidence(score: Optional[np.ndarray]) -> float:
    if score is None:
        return float("nan")
    score = np.asarray(score)
    if score.ndim == 2 and score.shape[0] > 0:
        return float(np.nanmax(score[0]))
    if score.ndim == 1 and len(score) > 0:
        # Decision function fallback; not calibrated.
        return float(1.0 / (1.0 + np.exp(-abs(score[0]))))
    return float("nan")


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    bundle: Optional[ModelBundle] = load_model_bundle(args.model) if args.model else None

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {args.camera}")

    # Set resolusi kamera untuk mencegah aspect ratio 4:3 default yang menyebapkan sensor terpotong (zoom-in)
    if args.width is not None and args.width > 0:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    if args.height is not None and args.height > 0:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    if fps <= 1 or fps > 120:
        fps = 30.0

    roi_regions = tuple(deep_get(config, "video.roi_regions", ["forehead", "left_cheek", "right_cheek"]))
    extractor = FaceRoiExtractor(
        backend=str(deep_get(config, "video.roi_backend", "mediapipe")),
        regions=roi_regions,
    )

    window_seconds = float(deep_get(config, "features.window_seconds", 60.0))
    max_len = max(30, int(round(window_seconds * fps)))
    rgb_buffer: deque[np.ndarray] = deque(maxlen=max_len)
    detect_buffer: deque[int] = deque(maxlen=max_len)
    time_buffer: deque[float] = deque(maxlen=max_len)

    method = str(deep_get(config, "rppg.method", "pos"))
    low_hz = float(deep_get(config, "rppg.bandpass_low_hz", 0.7))
    high_hz = float(deep_get(config, "rppg.bandpass_high_hz", 4.0))
    pos_window = float(deep_get(config, "rppg.pos_window_seconds", 1.6))
    chrom_window = float(deep_get(config, "rppg.chrom_window_seconds", 1.6))
    camera_flip = args.camera_flip or str(deep_get(config, "video.camera_flip", "none"))

    last_update = 0.0
    update_interval = 2.0
    status = {
        "hr": np.nan,
        "stress": "Collecting signal",
        "confidence": np.nan,
        "quality": 0.0,
        "detection_rate": 0.0,
        "rmssd_ms": np.nan,
        "sdnn_ms": np.nan,
        "pnn50": np.nan,
    }

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            time_buffer.append(time.time())

            # Downscale otomatis jika frame terlalu besar (seperti 4K) agar visualisasi pas di layar dan jalannya ringan
            h_orig, w_orig = frame.shape[:2]
            max_w = 1280
            if w_orig > max_w:
                scale_factor = max_w / w_orig
                frame = cv2.resize(frame, (max_w, int(round(h_orig * scale_factor))), interpolation=cv2.INTER_AREA)

            frame = apply_camera_flip(frame, camera_flip)

            roi_result = extractor.extract(frame)
            rgb_buffer.append(roi_result.rgb)
            detect_buffer.append(int(roi_result.detected))
            overlay = draw_roi_overlay(frame, roi_result)

            now = time.time()
            if len(rgb_buffer) >= max(30, int(0.5 * max_len)) and now - last_update >= update_interval:
                last_update = now
                
                # Hitung actual FPS dari data waktu kedatangan frame untuk mencegah frequency shift pada rPPG & HRV
                if len(time_buffer) > 1:
                    actual_fps = (len(time_buffer) - 1) / max(0.01, time_buffer[-1] - time_buffer[0])
                else:
                    actual_fps = fps
                if actual_fps < 5.0 or actual_fps > 120.0:
                    actual_fps = fps
                    
                status = update_status(
                    rgb=np.vstack(rgb_buffer),
                    fs=actual_fps,
                    seconds_collected=len(rgb_buffer) / actual_fps,
                    required_seconds=window_seconds,
                    detection_rate=float(np.mean(detect_buffer)) if detect_buffer else 0.0,
                    method=method,
                    low_hz=low_hz,
                    high_hz=high_hz,
                    pos_window=pos_window,
                    chrom_window=chrom_window,
                    bundle=bundle,
                    min_quality=args.min_quality,
                    min_detection=args.min_detection,
                )

            # Hitung estimasi waktu terkumpul menggunakan FPS aktual saat ini
            if len(time_buffer) > 1:
                current_fps = (len(time_buffer) - 1) / max(0.01, time_buffer[-1] - time_buffer[0])
            else:
                current_fps = fps
            if current_fps < 5.0 or current_fps > 120.0:
                current_fps = fps
                
            draw_status(overlay, status, len(rgb_buffer) / current_fps, window_seconds, bundle is not None)
            if args.display_scale != 1.0:
                overlay = cv2.resize(overlay, None, fx=args.display_scale, fy=args.display_scale)
            cv2.imshow("rPPG Stress Demo - press q to quit", overlay)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
    finally:
        extractor.close()
        cap.release()
        cv2.destroyAllWindows()


def apply_camera_flip(frame: np.ndarray, mode: str) -> np.ndarray:
    """Apply optional webcam orientation correction."""
    mode = str(mode).lower().strip()
    if mode == "horizontal":
        return cv2.flip(frame, 1)
    if mode == "vertical":
        return cv2.flip(frame, 0)
    if mode == "both":
        return cv2.flip(frame, -1)
    return frame


def update_status(
    rgb: np.ndarray,
    fs: float,
    seconds_collected: float,
    required_seconds: float,
    detection_rate: float,
    method: str,
    low_hz: float,
    high_hz: float,
    pos_window: float,
    chrom_window: float,
    bundle: Optional[ModelBundle],
    min_quality: float = 0.60,
    min_detection: float = 0.90,
) -> dict:
    try:
        bvp = extract_rppg(
            rgb=rgb,
            fs=fs,
            method=method,
            low_hz=low_hz,
            high_hz=high_hz,
            pos_window_seconds=pos_window,
            chrom_window_seconds=chrom_window,
        )
        hr = estimate_hr_from_signal(bvp, fs, low_hz, high_hz)
        features = extract_features_single_window(bvp, fs, low_hz=low_hz, high_hz=high_hz)
        features["fps"] = float(fs)
        features["detection_rate"] = float(detection_rate)
        quality = float(min(1.0, 0.5 * hr.quality + 0.5 * detection_rate))

        if seconds_collected < (required_seconds - 0.5):
            stress = "Collecting signal"
            confidence = np.nan
        elif detection_rate < min_detection:
            stress = "Face not stable"
            confidence = np.nan
        elif quality < min_quality:
            stress = "Poor signal"
            confidence = np.nan
        elif bundle is None:
            stress = "No model loaded"
            confidence = np.nan
        else:
            df = pd.DataFrame([features])
            y_pred, y_score = predict_from_features(bundle, df)
            stress = label_to_text(int(y_pred[0]))
            confidence = get_prediction_confidence(y_score)
            if quality < 0.70 or not np.isfinite(confidence) or confidence < 0.60:
                stress = f"Uncertain ({stress})"

        return {
            "hr": float(hr.bpm),
            "stress": stress,
            "confidence": float(confidence),
            "quality": quality,
            "detection_rate": float(detection_rate),
            "rmssd_ms": float(features.get("rmssd_ms", np.nan)),
            "sdnn_ms": float(features.get("sdnn_ms", np.nan)),
            "pnn50": float(features.get("pnn50", np.nan)),
        }
    except Exception as exc:
        return {
            "hr": np.nan,
            "stress": f"Error: {str(exc)[:40]}",
            "confidence": np.nan,
            "quality": 0.0,
            "detection_rate": float(detection_rate),
            "rmssd_ms": np.nan,
            "sdnn_ms": np.nan,
            "pnn50": np.nan,
        }


def draw_status(frame: np.ndarray, status: dict, seconds_collected: float, window_seconds: float, has_model: bool) -> None:
    lines = [
        f"Collected: {seconds_collected:.1f}/{window_seconds:.0f}s",
        f"HR: {_fmt(status.get('hr'))} BPM",
        f"State: {status.get('stress', '-')}",
        f"Confidence: {_fmt(status.get('confidence'))}",
        f"Quality: {_fmt(status.get('quality'))}",
        f"Face detection: {_fmt(status.get('detection_rate'))}",
        f"RMSSD: {_fmt(status.get('rmssd_ms'))} ms",
        f"SDNN: {_fmt(status.get('sdnn_ms'))} ms",
        f"pNN50: {_fmt(status.get('pnn50'))}",
    ]
    if not has_model:
        lines.append("Load --model to predict stress")
    x, y = 20, 30
    for line in lines:
        cv2.putText(frame, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        y += 26


def _fmt(value) -> str:
    try:
        value = float(value)
    except Exception:
        return "-"
    if not np.isfinite(value):
        return "-"
    return f"{value:.2f}"


if __name__ == "__main__":
    main()
