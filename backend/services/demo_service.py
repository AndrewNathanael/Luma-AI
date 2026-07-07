"""Realtime demo service layer."""

from __future__ import annotations

from backend.schemas.demo import RealtimeDemoRequest


def build_demo_command(payload: RealtimeDemoRequest) -> str:
    return (
        "python scripts/03_realtime_demo.py "
        f"--model {payload.model_path} "
        f"--config {payload.config_path} "
        f"--camera {payload.camera_index}"
    )
