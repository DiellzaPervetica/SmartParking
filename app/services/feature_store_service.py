from __future__ import annotations

from datetime import datetime

from app.domain.schemas import NormalizedSensorReading


class FeatureStoreService:
    @staticmethod
    def build_feature_row(
        reading: NormalizedSensorReading,
        current_occupancy_rate: float,
        recent_events: list[dict],
    ) -> dict:
        timestamp = reading.timestamp
        last_distances = [row.get("distance_cm", 0.0) for row in recent_events[:5]]
        avg_recent_distance = sum(last_distances) / len(last_distances) if last_distances else reading.distance_cm

        return {
            "hour": timestamp.hour,
            "day_of_week": timestamp.weekday(),
            "is_weekend": 1 if timestamp.weekday() >= 5 else 0,
            "current_occupancy_rate": current_occupancy_rate,
            "distance_cm": reading.distance_cm,
            "battery_level": reading.battery_level,
            "signal_strength": reading.signal_strength,
            "recent_event_count": len(recent_events),
            "avg_recent_distance": round(avg_recent_distance, 2),
        }
