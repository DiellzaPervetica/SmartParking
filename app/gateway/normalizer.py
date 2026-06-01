from __future__ import annotations

from app.domain.schemas import NormalizedSensorReading, SensorPayload
from app.utils.time_utils import utc_now


def normalize_payload(payload: SensorPayload) -> NormalizedSensorReading:
    return NormalizedSensorReading(**payload.model_dump(), ingest_ts=utc_now())
