from __future__ import annotations

import requests

from app.mqtt_layer.mqtt_publisher import MqttPublisher
from app.mqtt_layer.mqtt_topics import sensor_topic
from app.settings import get_settings


def main() -> None:
    settings = get_settings()
    publisher = MqttPublisher()
    publisher.connect()
    publisher.publish_json(
        sensor_topic("P01"),
        {
            "event_id": "manual-smoke-test",
            "parking_id": "prishtina_center_01",
            "parking_name": settings.parking_name,
            "zone_id": "A",
            "spot_id": "P01",
            "sensor_id": "ultra-p01",
            "gateway_id": "gateway-prishtina-01",
            "sequence_no": 999999,
            "timestamp": "2026-04-03T12:00:00+00:00",
            "occupied": True,
            "distance_cm": 18.0,
            "battery_level": 88.2,
            "signal_strength": -56,
            "event_type": "state_change",
        },
    )
    publisher.close()

    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=3)
        print("API health:", response.status_code, response.json())
    except Exception as exc:  # noqa: BLE001
        print("API check failed:", exc)


if __name__ == "__main__":
    main()
