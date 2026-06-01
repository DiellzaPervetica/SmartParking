from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.domain.schemas import SensorPayload


def validate_sensor_payload(raw_data: dict[str, Any]) -> tuple[bool, SensorPayload | None, str | None]:
    try:
        payload = SensorPayload(**raw_data)
        return True, payload, None
    except ValidationError as exc:
        return False, None, str(exc)
