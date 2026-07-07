"""Training-related API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrainingRequest(BaseModel):
    features_csv: str = Field(default="data/features_pos.csv")
    model_output: str = Field(default="models/stress_model.joblib")
    metrics_output: str = Field(default="results/train_metrics.json")
    feature_importance_output: str = Field(default="results/feature_importance_random_forest.csv")
    config_path: str = Field(default="config/default.yaml")
