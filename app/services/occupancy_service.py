from __future__ import annotations

from app.domain.schemas import ParkingSummary
from app.utils.time_utils import floor_to_minute, utc_now


class OccupancyService:
    @staticmethod
    def build_summary(parking_id: str, spot_rows: list[dict]) -> ParkingSummary:
        occupied_spots = sum(1 for row in spot_rows if row.get("occupied"))
        free_spots = len(spot_rows) - occupied_spots
        occupancy_rate = occupied_spots / len(spot_rows) if spot_rows else 0.0

        return ParkingSummary(
            parking_id=parking_id,
            generated_at=floor_to_minute(utc_now()),
            occupied_spots=occupied_spots,
            free_spots=free_spots,
            occupancy_rate=round(occupancy_rate, 4),
        )
