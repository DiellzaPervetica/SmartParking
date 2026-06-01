from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParkingSpot:
    parking_id: str
    zone_id: str
    spot_id: str
    sensor_id: str
    gateway_id: str
    occupied: bool = False
    distance_cm: float = 180.0
    last_sent_at: datetime | None = None
    last_heartbeat_at: datetime | None = None
    sequence_no: int = 0


@dataclass
class RuntimeStatus:
    last_sequence_no: int | None = None
    last_seen_ts: datetime | None = None
    repeated_state_count: int = 0
    last_occupied: bool | None = None
