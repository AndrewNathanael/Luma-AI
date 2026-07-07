"""Training endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.schemas.training import TrainingRequest
from backend.services.training_service import build_training_command


router = APIRouter(prefix="/training", tags=["training"])


@router.post("/train-command")
def train_command(payload: TrainingRequest) -> dict[str, str]:
    return {"command": build_training_command(payload)}
