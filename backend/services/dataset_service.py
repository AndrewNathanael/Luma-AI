"""Dataset service layer."""

from __future__ import annotations

from backend.schemas.dataset import ManifestRequest


def build_manifest_command(payload: ManifestRequest) -> str:
    command = [
        "python",
        "scripts/00_make_manifest.py",
        "--root",
        payload.dataset_root,
        "--output",
        payload.output_csv,
        "--dataset",
        payload.dataset_type,
    ]
    if payload.strict:
        command.append("--strict")
    return " ".join(command)
