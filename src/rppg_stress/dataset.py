"""Dataset helpers for manifest-based video processing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable

import pandas as pd
from tqdm import tqdm

from .features import FeatureConfig, extract_windowed_features
from .rppg_algorithms import extract_rppg
from .utils import deep_get, ensure_parent
from .video_io import read_video_rgb_timeseries


REQUIRED_MANIFEST_COLUMNS = {"subject_id", "video_path", "condition"}
VIDEO_EXTENSIONS = (".avi", ".mp4", ".mov", ".mkv", ".m4v")
UBFC_PHYS_TASK_CONDITIONS = {
    "T1": "rest",
    "T2": "speech",
    "T3": "arithmetic",
}
_UBFC_SUBJECT_RE = re.compile(r"^s(?P<number>\d+)$", re.IGNORECASE)
_UBFC_VIDEO_RE = re.compile(r"^vid_(?P<subject>s\d+)_?(?P<task>T[123])$", re.IGNORECASE)


def load_manifest(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    df = pd.read_csv(path)
    missing = REQUIRED_MANIFEST_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Manifest is missing columns: {sorted(missing)}")
    df = df.copy()
    df["subject_id"] = df["subject_id"].astype(str)
    df["condition"] = df["condition"].astype(str).str.lower().str.strip()
    df["video_path"] = df["video_path"].astype(str)
    return df


def map_condition_to_label(condition: str, config: Dict[str, Any]) -> int:
    mode = str(deep_get(config, "labels.mode", "binary")).lower().strip()
    mapping = deep_get(config, f"labels.{mode}", {}) or {}
    key = str(condition).lower().strip()
    if key not in mapping:
        raise KeyError(
            f"Condition '{condition}' is not in labels.{mode}. "
            "Edit config/default.yaml or normalize manifest condition names."
        )
    return int(mapping[key])


def process_manifest_to_features(
    manifest_path: str | Path,
    config: Dict[str, Any],
    strict: bool = False,
) -> pd.DataFrame:
    """Process all videos from manifest and return one feature table."""
    manifest = load_manifest(manifest_path)
    all_features = []
    errors = []

    for row in tqdm(list(manifest.itertuples(index=False)), desc="Videos"):
        subject_id = str(row.subject_id)
        video_path = str(row.video_path)
        condition = str(row.condition).lower().strip()
        try:
            label = map_condition_to_label(condition, config)
            features = process_single_video(
                video_path=video_path,
                subject_id=subject_id,
                condition=condition,
                label=label,
                config=config,
            )
            all_features.append(features)
        except Exception as exc:
            if strict:
                raise
            errors.append({"subject_id": subject_id, "video_path": video_path, "condition": condition, "error": str(exc)})
            print(f"[WARN] Failed video {video_path}: {exc}")

    if not all_features:
        raise RuntimeError("No features were extracted. Check manifest paths, videos, and ROI detection.")

    out = pd.concat(all_features, ignore_index=True)
    if errors:
        out.attrs["errors"] = errors
    return out


def process_single_video(
    video_path: str | Path,
    subject_id: str,
    condition: str,
    label: int,
    config: Dict[str, Any],
) -> pd.DataFrame:
    """Extract rPPG and features from one video."""
    roi_regions = tuple(deep_get(config, "video.roi_regions", ["forehead", "left_cheek", "right_cheek"]))
    rgb_result = read_video_rgb_timeseries(
        video_path=video_path,
        roi_backend=str(deep_get(config, "video.roi_backend", "mediapipe")),
        roi_regions=roi_regions,
        fps_override=deep_get(config, "video.fps_override", None),
        max_frames=deep_get(config, "video.max_frames", None),
        use_opencl=bool(deep_get(config, "video.use_opencl", False)),
        show_progress=False,
    )

    method = str(deep_get(config, "rppg.method", "pos"))
    low_hz = float(deep_get(config, "rppg.bandpass_low_hz", 0.7))
    high_hz = float(deep_get(config, "rppg.bandpass_high_hz", 4.0))
    bvp = extract_rppg(
        rgb=rgb_result.rgb,
        fs=rgb_result.fps,
        method=method,
        low_hz=low_hz,
        high_hz=high_hz,
        pos_window_seconds=float(deep_get(config, "rppg.pos_window_seconds", 1.6)),
        chrom_window_seconds=float(deep_get(config, "rppg.chrom_window_seconds", 1.6)),
    )

    feature_config = FeatureConfig(
        window_seconds=float(deep_get(config, "features.window_seconds", 60.0)),
        step_seconds=float(deep_get(config, "features.step_seconds", 10.0)),
        interpolate_rate_hz=float(deep_get(config, "features.interpolate_rate_hz", 4.0)),
        min_valid_beats=int(deep_get(config, "features.min_valid_beats", 10)),
        low_hz=low_hz,
        high_hz=high_hz,
    )
    features = extract_windowed_features(bvp, rgb_result.fps, feature_config)
    features.insert(0, "subject_id", subject_id)
    features.insert(1, "video_path", str(video_path))
    features.insert(2, "condition", condition)
    features.insert(3, "label", int(label))
    features["fps"] = float(rgb_result.fps)
    features["detection_rate"] = float(rgb_result.detection_rate)
    features["rppg_method"] = method
    return features


def make_manifest_from_directory(
    root: str | Path,
    output_csv: str | Path,
    pattern: str = "*.mp4",
    dataset: str = "auto",
    strict: bool = False,
) -> pd.DataFrame:
    """Create a starter manifest by scanning videos.

    For ``dataset="auto"``, a UBFC-Phys layout is detected when folders named
    ``s<number>`` contain videos named ``vid_s<number>_T1/T2/T3.avi``. In that
    case, conditions are assigned as T1=rest, T2=speech, and T3=arithmetic.

    The generic fallback scans ``pattern`` and tries to infer condition from
    filename tokens: T1/rest, T2/speech, T3/arithmetic. Review the output
    manually before training.
    """
    dataset = str(dataset).lower().replace("-", "_").strip()
    if dataset in {"auto", "ubfc_phys"} and _looks_like_ubfc_phys(root):
        return make_ubfc_phys_manifest(root=root, output_csv=output_csv, strict=strict)
    if dataset == "ubfc_phys":
        return make_ubfc_phys_manifest(root=root, output_csv=output_csv, strict=strict)
    if dataset not in {"auto", "generic"}:
        raise ValueError("dataset must be auto, generic, or ubfc_phys")

    root = Path(root)
    files = sorted(root.rglob(pattern))
    rows = []
    for path in files:
        name = path.stem.lower()
        condition = _infer_condition_from_name(name)
        subject_id = _infer_subject_from_name(path)
        rows.append({"subject_id": subject_id, "video_path": str(path), "condition": condition})
    df = pd.DataFrame(rows)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    return df


def make_ubfc_phys_manifest(
    root: str | Path,
    output_csv: str | Path | None = None,
    strict: bool = False,
    video_extensions: Iterable[str] = VIDEO_EXTENSIONS,
) -> pd.DataFrame:
    """Create a UBFC-Phys manifest from the extracted dataset root.

    UBFC-Phys stores each participant in a folder named ``s<number>`` and each
    task video as ``vid_s<number>_T1.avi``, ``vid_s<number>_T2.avi``, or
    ``vid_s<number>_T3.avi``. The output keeps the common manifest contract and
    adds ``task`` and ``dataset`` metadata columns.
    """
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"Dataset root not found: {root}")

    extensions = tuple(ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in video_extensions)
    subject_dirs = _find_ubfc_subject_dirs(root)
    if not subject_dirs:
        raise ValueError(f"No UBFC-Phys subject folders like s1, s2, ... found under {root}")

    rows = []
    missing = []
    for subject_dir in subject_dirs:
        subject_id = _normalize_ubfc_subject_id(subject_dir.name)
        videos = _index_ubfc_videos(subject_dir, subject_id, extensions)
        for task, condition in UBFC_PHYS_TASK_CONDITIONS.items():
            video_path = videos.get(task)
            if video_path is None:
                missing.append({"subject_id": subject_id, "task": task, "subject_dir": str(subject_dir)})
                continue
            rows.append(
                {
                    "subject_id": subject_id,
                    "video_path": str(video_path.resolve()),
                    "condition": condition,
                    "task": task,
                    "dataset": "UBFC-Phys",
                }
            )

    if strict and missing:
        preview = ", ".join(f"{m['subject_id']}:{m['task']}" for m in missing[:10])
        suffix = "..." if len(missing) > 10 else ""
        raise ValueError(f"Missing UBFC-Phys task videos: {preview}{suffix}")
    if not rows:
        raise ValueError(f"No UBFC-Phys T1/T2/T3 videos found under {root}")

    df = pd.DataFrame(rows).sort_values(["subject_id", "task"], key=_subject_task_sort_key).reset_index(drop=True)
    if missing:
        df.attrs["missing_videos"] = missing

    if output_csv is not None:
        output_csv = ensure_parent(output_csv)
        df.to_csv(output_csv, index=False)
    return df


def _looks_like_ubfc_phys(root: str | Path) -> bool:
    root = Path(root)
    if not root.exists():
        return False
    for subject_dir in _find_ubfc_subject_dirs(root):
        subject_id = _normalize_ubfc_subject_id(subject_dir.name)
        if _index_ubfc_videos(subject_dir, subject_id, VIDEO_EXTENSIONS):
            return True
    return False


def _find_ubfc_subject_dirs(root: Path) -> list[Path]:
    candidates = []
    if root.is_dir() and _UBFC_SUBJECT_RE.match(root.name):
        candidates.append(root)
    if root.is_dir():
        candidates.extend(path for path in root.rglob("*") if path.is_dir() and _UBFC_SUBJECT_RE.match(path.name))
    unique = {path.resolve(): path for path in candidates}
    return sorted(unique.values(), key=lambda path: _subject_sort_value(path.name))


def _index_ubfc_videos(subject_dir: Path, subject_id: str, extensions: tuple[str, ...]) -> dict[str, Path]:
    videos: dict[str, Path] = {}
    for path in sorted(subject_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        match = _UBFC_VIDEO_RE.match(path.stem)
        if match is None:
            continue
        file_subject = _normalize_ubfc_subject_id(match.group("subject"))
        task = match.group("task").upper()
        if file_subject == subject_id and task in UBFC_PHYS_TASK_CONDITIONS:
            videos.setdefault(task, path)
    return videos


def _normalize_ubfc_subject_id(value: str) -> str:
    match = _UBFC_SUBJECT_RE.match(str(value).strip())
    if match is None:
        return str(value).strip().lower()
    return f"s{int(match.group('number'))}"


def _subject_sort_value(value: str) -> tuple[int, str]:
    match = _UBFC_SUBJECT_RE.match(str(value).strip())
    if match is None:
        return (10**9, str(value))
    return (int(match.group("number")), str(value))


def _subject_task_sort_key(columns: pd.Series) -> pd.Series:
    if columns.name == "subject_id":
        return columns.map(lambda value: _subject_sort_value(str(value))[0])
    if columns.name == "task":
        return columns.map(lambda value: {"T1": 1, "T2": 2, "T3": 3}.get(str(value).upper(), 99))
    return columns


def _infer_condition_from_name(name: str) -> str:
    name = name.lower()
    if "t1" in name or "rest" in name or "baseline" in name:
        return "rest"
    if "t2" in name or "speech" in name:
        return "speech"
    if "t3" in name or "arith" in name or "math" in name:
        return "arithmetic"
    return "unknown"


def _infer_subject_from_name(path: Path) -> str:
    for part in reversed(path.parts):
        lower = part.lower()
        if lower.startswith("s") and any(ch.isdigit() for ch in lower):
            return part
    return path.parent.name
