from __future__ import annotations

import sys
import time
from typing import Any

import requests

from app.mqtt_layer.mqtt_publisher import MqttPublisher
from app.mqtt_layer.mqtt_topics import sensor_topic
from app.settings import get_settings
from app.storage.repositories import ParkingRepository
from app.utils.ids import new_event_id
from app.utils.time_utils import utc_now


TIMEOUT_SECONDS = 60
POLL_SECONDS = 3
PROBE_SPOT_ID = "P01"


def ok(message: str) -> None:
    print(f"[OK] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def publish_probe_event(sequence_no: int) -> dict[str, Any]:
    settings = get_settings()

    payload = {
        "event_id": new_event_id(),
        "parking_id": settings.parking_id,
        "parking_name": settings.parking_name,
        "zone_id": "A",
        "spot_id": PROBE_SPOT_ID,
        "sensor_id": "ultra-p01",
        "gateway_id": "gateway-prishtina-01",
        "sequence_no": sequence_no,
        "timestamp": utc_now().isoformat(),
        "occupied": True,
        "distance_cm": 18.0,
        "battery_level": 92.5,
        "signal_strength": -55,
        "event_type": "state_change",
    }

    publisher = MqttPublisher()
    try:
        publisher.connect()
        publisher.publish_json(sensor_topic(PROBE_SPOT_ID), payload)
    finally:
        publisher.close()

    ok(f"Probe event u dërgua në MQTT për {PROBE_SPOT_ID}, sequence_no={sequence_no}")
    return payload


def wait_until_cassandra_has_probe(sequence_no: int) -> dict[str, Any]:
    settings = get_settings()
    start = time.time()
    last_error: str | None = None

    while time.time() - start < TIMEOUT_SECONDS:
        repository = ParkingRepository()
        try:
            rows = repository.get_current_spot_status(settings.parking_id)
            probe_row = next(
                (row for row in rows if row.get("spot_id") == PROBE_SPOT_ID),
                None,
            )

            if probe_row and probe_row.get("last_sequence_no") == sequence_no:
                ok("Cassandra e pranoi eventin e procesuar nga Spark Streaming")
                return probe_row

        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)

        finally:
            repository.close()

        time.sleep(POLL_SECONDS)

    fail(
        "Eventi nuk u gjet në Cassandra brenda afatit. "
        "Kontrollo a janë ndezur: MQTT Gateway, Spark Streaming, Kafka, Cassandra. "
        f"Gabimi i fundit: {last_error}"
    )
    return {}


def check_dashboard_reads_live_source() -> None:
    settings = get_settings()
    url = f"http://{settings.api_host}:{settings.api_port}/parking/dashboard-data"

    response = requests.get(url, timeout=5)
    response.raise_for_status()

    data = response.json()
    source = data.get("source")

    if source != "cassandra_spark_streaming":
        fail(
            "Dashboard-i nuk po lexon nga pipeline-i live. "
            f"Burimi aktual: {source}. "
            "Prit disa sekonda ose kontrollo nëse Spark ka shkruar rreshta në Cassandra."
        )

    ok("Dashboard-i po lexon nga Cassandra/Spark Streaming, jo nga fallback")


def main() -> None:
    sequence_no = int(time.time())

    print("\n=== SMART PARKING LIVE PIPELINE CHECK ===")
    print("Ky test provon rrjedhën: MQTT → Gateway → Kafka → Spark → Cassandra → Dashboard\n")

    publish_probe_event(sequence_no)
    row = wait_until_cassandra_has_probe(sequence_no)
    check_dashboard_reads_live_source()

    print("\nRreshti i verifikuar në Cassandra:")
    print(
        {
            "spot_id": row.get("spot_id"),
            "occupied": row.get("occupied"),
            "distance_cm": row.get("distance_cm"),
            "battery_level": row.get("battery_level"),
            "signal_strength": row.get("signal_strength"),
            "last_sequence_no": row.get("last_sequence_no"),
            "classification_label": row.get("classification_label"),
            "anomaly_label": row.get("anomaly_label"),
        }
    )

    print("\n[READY] Pipeline live është verifikuar me sukses.")


if __name__ == "__main__":
    main()
