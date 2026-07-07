"""Dataset and manifest endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.schemas.dataset import ManifestRequest
from backend.services.dataset_service import build_manifest_command


router = APIRouter(prefix="/dataset", tags=["dataset"])


@router.post("/manifest-command")
def manifest_command(payload: ManifestRequest) -> dict[str, str]:
    return {"command": build_manifest_command(payload)}
