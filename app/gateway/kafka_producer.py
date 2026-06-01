from __future__ import annotations

import json
import logging
from typing import Any

from confluent_kafka import Producer

from app.settings import get_settings

logger = logging.getLogger(__name__)


class KafkaEventProducer:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})

    def send(self, topic: str, payload: dict[str, Any], key: str | None = None) -> None:
        self.producer.produce(
            topic=topic,
            key=key.encode("utf-8") if key else None,
            value=json.dumps(payload, default=str).encode("utf-8"),
        )
        self.producer.poll(0)

    def flush(self) -> None:
        self.producer.flush()
        logger.info("Kafka producer flushed")

    def send_reading(self, payload: dict[str, Any]) -> None:
        spot_id = payload.get("spot_id", "unknown")
        self.send(self.settings.kafka_topic_raw, payload, key=spot_id)

    def send_alert(self, alert_payload: dict[str, Any]) -> None:
        self.send(self.settings.kafka_topic_alerts, alert_payload, key=alert_payload.get("sensor_id", "unknown"))
