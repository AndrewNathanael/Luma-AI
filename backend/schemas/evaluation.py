"""Evaluation-related API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LosoEvaluationRequest(BaseModel):
    features_csv: str = Field(default="data/features_pos.csv")
    output_json: str = Field(default="results/loso_metrics.json")
    config_path: str = Field(default="config/default.yaml")
