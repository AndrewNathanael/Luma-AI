"""Feature extraction endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.schemas.dataset import FeatureExtractionRequest
from backend.services.feature_service import build_feature_command


router = APIRouter(prefix="/features", tags=["features"])


@router.post("/extract-command")
def extract_command(payload: FeatureExtractionRequest) -> dict[str, str]:
    return {"command": build_feature_command(payload)}
