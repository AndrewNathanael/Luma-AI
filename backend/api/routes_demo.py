"""Realtime demo endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.schemas.demo import RealtimeDemoRequest
from backend.services.demo_service import build_demo_command


router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/realtime-command")
def realtime_command(payload: RealtimeDemoRequest) -> dict[str, str]:
    return {"command": build_demo_command(payload)}
