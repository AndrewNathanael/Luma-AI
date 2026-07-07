"""Evaluation endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.schemas.evaluation import LosoEvaluationRequest
from backend.services.evaluation_service import build_loso_command


router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/loso-command")
def loso_command(payload: LosoEvaluationRequest) -> dict[str, str]:
    return {"command": build_loso_command(payload)}
