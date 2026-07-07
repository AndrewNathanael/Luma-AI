"""Realtime demo API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RealtimeDemoRequest(BaseModel):
    model_path: str = Field(default="models/stress_model.joblib")
    config_path: str = Field(default="config/default.yaml")
    camera_index: int = Field(default=0, ge=0)
