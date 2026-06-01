from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from app.domain.models import RuntimeStatus
from app.domain.schemas import NormalizedSensorReading


@dataclass
class RuntimeAnomaly:
    label: str
    score: float
    message: str


class StatusMonitor:
    def __init__(self) -> None:
        self._state: Dict[str, RuntimeStatus] = {}

    def process(self, reading: NormalizedSensorReading) -> list[RuntimeAnomaly]:
        status = self._state.setdefault(reading.sensor_id, RuntimeStatus())
        anomalies: list[RuntimeAnomaly] = []

        if status.last_sequence_no is not None and reading.sequence_no > status.last_sequence_no + 1:
            anomalies.append(
                RuntimeAnomaly(
                    label="sequence_gap",
                    score=0.80,
                    message=f"Sequence gap detected: last={status.last_sequence_no}, current={reading.sequence_no}",
                )
            )

        if status.last_occupied is not None and status.last_occupied == reading.occupied:
            status.repeated_state_count += 1
        else:
            status.repeated_state_count = 0

        if status.repeated_state_count >= 15:
            anomalies.append(
                RuntimeAnomaly(
                    label="stuck_sensor",
                    score=0.60,
                    message="Sensor stayed in the same state for a long time",
                )
            )

        status.last_sequence_no = reading.sequence_no
        status.last_seen_ts = reading.ingest_ts
        status.last_occupied = reading.occupied
        return anomalies
