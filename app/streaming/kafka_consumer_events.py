from __future__ import annotations

import json
import logging

from confluent_kafka import Consumer

from app.domain.schemas import NormalizedSensorReading
from app.logging_config import configure_logging
from app.services.occupancy_service import OccupancyService
from app.settings import get_settings
from app.storage.repositories import ParkingRepository

logger = logging.getLogger(__name__)


def run() -> None:
    configure_logging()
    settings = get_settings()
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": "parking-storage-consumer",
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([settings.kafka_topic_raw])

    repository = ParkingRepository()
    occupancy_service = OccupancyService()

    logger.info("Kafka storage consumer started on topic=%s", settings.kafka_topic_raw)

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("Kafka consumer error: %s", msg.error())
                continue

            payload = json.loads(msg.value().decode("utf-8"))
            reading = NormalizedSensorReading(**payload)

            repository.insert_sensor_event(reading)
            repository.upsert_current_status(reading)

            current_rows = repository.get_current_spot_status(settings.parking_id)
            summary = occupancy_service.build_summary(settings.parking_id, current_rows)
            repository.insert_parking_summary(summary)

            logger.info(
                "Stored event and updated summary | spot=%s occupied=%s occupancy_rate=%.2f",
                reading.spot_id,
                reading.occupied,
                summary.occupancy_rate,
            )
    except KeyboardInterrupt:
        logger.info("Storage consumer stopped by user")
    finally:
        consumer.close()
        repository.close()


if __name__ == "__main__":
    run()
