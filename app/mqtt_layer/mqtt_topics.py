from __future__ import annotations

from app.settings import get_settings


def sensor_topic(spot_id: str) -> str:
    settings = get_settings()
    return f"{settings.mqtt_topic_root}/sensors/{spot_id}"


def wildcard_topic() -> str:
    settings = get_settings()
    return f"{settings.mqtt_topic_root}/sensors/+"
