"""Evaluation service layer."""

from __future__ import annotations

from backend.schemas.evaluation import LosoEvaluationRequest


def build_loso_command(payload: LosoEvaluationRequest) -> str:
    return (
        "python scripts/04_evaluate_model.py "
        f"--features {payload.features_csv} "
        f"--output {payload.output_json} "
        "--loso "
        f"--config {payload.config_path}"
    )
