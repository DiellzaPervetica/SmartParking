from __future__ import annotations

from fastapi import APIRouter

from app.settings import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


@router.get("/ready")
def ready() -> dict:
    return {"status": "ready"}
