from __future__ import annotations

from fastapi import APIRouter

from app.settings import get_settings
from app.storage.repositories import ParkingRepository

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/predictions/latest")
def latest_predictions(limit: int = 10) -> dict:
    settings = get_settings()
    repository = ParkingRepository()
    rows = repository.get_latest_ai_results(settings.parking_id, ai_type="prediction", limit=limit)
    repository.close()
    return {"count": len(rows), "items": rows}


@router.get("/anomalies/latest")
def latest_anomalies(limit: int = 20) -> dict:
    settings = get_settings()
    repository = ParkingRepository()
    rows = repository.get_latest_ai_results(settings.parking_id, ai_type="anomaly", limit=limit)
    repository.close()
    return {"count": len(rows), "items": rows}


@router.get("/pricing/latest")
def latest_pricing(limit: int = 10) -> dict:
    settings = get_settings()
    repository = ParkingRepository()
    rows = repository.get_latest_ai_results(settings.parking_id, ai_type="pricing", limit=limit)
    repository.close()
    return {"count": len(rows), "items": rows}


@router.get("/alerts/latest")
def latest_alerts(limit: int = 20) -> dict:
    settings = get_settings()
    repository = ParkingRepository()
    rows = repository.get_latest_alerts(settings.parking_id, limit=limit)
    repository.close()
    return {"count": len(rows), "items": rows}
