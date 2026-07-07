"""Training service layer."""

from __future__ import annotations

from backend.schemas.training import TrainingRequest


def build_training_command(payload: TrainingRequest) -> str:
    return (
        "python scripts/02_train_stress_classifier.py "
        f"--features {payload.features_csv} "
        f"--model-out {payload.model_output} "
        f"--metrics-out {payload.metrics_output} "
        f"--feature-importance-out {payload.feature_importance_output} "
        f"--config {payload.config_path}"
    )
