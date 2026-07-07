"""Dataset-related API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ManifestRequest(BaseModel):
    dataset_root: str = Field(default="data/UBFC-Phys")
    output_csv: str = Field(default="data/ubfc_phys_manifest.csv")
    dataset_type: str = Field(default="ubfc_phys")
    strict: bool = Field(default=True)


class FeatureExtractionRequest(BaseModel):
    manifest_csv: str = Field(default="data/ubfc_phys_manifest.csv")
    output_csv: str = Field(default="data/features_pos.csv")
    config_path: str = Field(default="config/default.yaml")
