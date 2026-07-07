"""Feature extraction service layer."""

from __future__ import annotations

from backend.schemas.dataset import FeatureExtractionRequest


def build_feature_command(payload: FeatureExtractionRequest) -> str:
    return (
        "python scripts/01_extract_features.py "
        f"--manifest {payload.manifest_csv} "
        f"--output {payload.output_csv} "
        f"--config {payload.config_path}"
    )
