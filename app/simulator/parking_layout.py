from __future__ import annotations

from app.domain.models import ParkingSpot
from app.settings import get_settings


def build_default_parking_layout() -> list[ParkingSpot]:
    settings = get_settings()
    spots: list[ParkingSpot] = []
    gateway_id = "gateway-prishtina-01"

    for idx in range(1, settings.total_spots + 1):
        zone = "A" if idx <= settings.total_spots // 2 else "B"
        spot_id = f"P{idx:02d}"
        sensor_id = f"ultra-{spot_id.lower()}"
        spots.append(
            ParkingSpot(
                parking_id=settings.parking_id,
                zone_id=zone,
                spot_id=spot_id,
                sensor_id=sensor_id,
                gateway_id=gateway_id,
            )
        )
    return spots
