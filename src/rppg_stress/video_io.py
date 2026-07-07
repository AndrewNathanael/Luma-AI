"""Video reading and RGB time-series extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm

from .roi import FaceRoiExtractor


@dataclass
class VideoRgbResult:
    rgb: np.ndarray
    timestamps: np.ndarray
    fps: float
    dataframe: pd.DataFrame
    detection_rate: float


def read_video_rgb_timeseries(
    video_path: str | Path,
    roi_backend: str = "mediapipe",
    roi_regions: tuple[str, ...] = ("forehead", "left_cheek", "right_cheek"),
    fps_override: Optional[float] = None,
    max_frames: Optional[int] = None,
    use_opencl: bool = False,
    show_progress: bool = True,
) -> VideoRgbResult:
    """Read a video and return mean RGB values from face ROIs per frame."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # CPU-only processing is more reproducible and avoids OpenCL allocation
    # failures on large UBFC-Phys videos.
    cv2.ocl.setUseOpenCL(bool(use_opencl))

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = float(fps_override or cap.get(cv2.CAP_PROP_FPS) or 30.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if max_frames is not None:
        frame_count = min(frame_count, max_frames) if frame_count > 0 else max_frames

    extractor = FaceRoiExtractor(backend=roi_backend, regions=roi_regions)
    rows = []
    frame_idx = 0
    detected_count = 0

    iterator = range(frame_count) if frame_count > 0 else iter(int, 1)
    if show_progress and frame_count > 0:
        iterator = tqdm(iterator, desc=f"RGB {video_path.name}")

    try:
        for _ in iterator:
            if max_frames is not None and frame_idx >= max_frames:
                break
            ok, frame = cap.read()
            if not ok:
                break
            result = extractor.extract(frame)
            detected_count += int(result.detected)
            rows.append(
                {
                    "frame": frame_idx,
                    "timestamp": frame_idx / fps,
                    "r": result.rgb[0],
                    "g": result.rgb[1],
                    "b": result.rgb[2],
                    "face_area_ratio": result.face_area_ratio,
                    "face_detected": int(result.detected),
                }
            )
            frame_idx += 1
    finally:
        extractor.close()
        cap.release()

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError(f"No frames could be read from video: {video_path}")

    rgb = df[["r", "g", "b"]].to_numpy(dtype=float)
    timestamps = df["timestamp"].to_numpy(dtype=float)
    detection_rate = float(detected_count / max(1, len(df)))
    return VideoRgbResult(
        rgb=rgb,
        timestamps=timestamps,
        fps=fps,
        dataframe=df,
        detection_rate=detection_rate,
    )
