from __future__ import annotations

from datetime import datetime

from app.domain.enums import EventType
from app.domain.models import ParkingSpot
from app.utils.ids import new_event_id


def build_sensor_payload(
    spot: ParkingSpot,
    occupied: bool,
    distance_cm: float,
    battery_level: float,
    signal_strength: int,
    event_type: EventType,
    timestamp: datetime,
) -> dict:
    spot.sequence_no += 1
    return {
        "event_id": new_event_id(),
        "parking_id": spot.parking_id,
        "parking_name": "Qendra Parking Prishtine",
        "zone_id": spot.zone_id,
        "spot_id": spot.spot_id,
        "sensor_id": spot.sensor_id,
        "gateway_id": spot.gateway_id,
        "sequence_no": spot.sequence_no,
        "timestamp": timestamp.isoformat(),
        "occupied": occupied,
        "distance_cm": distance_cm,
        "battery_level": battery_level,
        "signal_strength": signal_strength,
        "event_type": event_type.value,
    }
