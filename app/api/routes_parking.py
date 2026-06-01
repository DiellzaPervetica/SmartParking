from __future__ import annotations

from fastapi import APIRouter

from app.services.dashboard_service import DashboardService
from app.services.health_service import HealthService
from app.services.occupancy_service import OccupancyService
from app.services.simulation_snapshot_service import SimulationSnapshotService
from app.settings import get_settings
from app.storage.repositories import ParkingRepository

router = APIRouter(prefix="/parking", tags=["parking"])


@router.get("/status")
def parking_status() -> dict:
    settings = get_settings()
    repository = ParkingRepository()
    rows = repository.get_current_spot_status(settings.parking_id)
    summary = OccupancyService.build_summary(settings.parking_id, rows)
    health = HealthService.summarize_sensor_health(rows)
    repository.close()

    return {
        "parking_id": settings.parking_id,
        "parking_name": settings.parking_name,
        "summary": summary.model_dump(mode="json"),
        "health": health,
    }


@router.get("/spots")
def parking_spots() -> dict:
    settings = get_settings()
    repository = ParkingRepository()
    rows = repository.get_current_spot_status(settings.parking_id)
    repository.close()
    return {"count": len(rows), "spots": rows}


@router.get("/summary")
def parking_summary() -> dict:
    settings = get_settings()
    repository = ParkingRepository()
    rows = repository.get_current_spot_status(settings.parking_id)
    summary = OccupancyService.build_summary(settings.parking_id, rows)
    repository.close()
    return summary.model_dump(mode="json")


@router.get("/simulation")
def parking_simulation(scenario: str = "auto") -> dict:
    return SimulationSnapshotService().generate(scenario=scenario)


@router.get("/dashboard-data")
def parking_dashboard_data(scenario: str = "auto") -> dict:
    return DashboardService().build(scenario=scenario)
