from __future__ import annotations

import json
import logging

from confluent_kafka import Consumer

from app.ai.anomaly_detection import SensorAnomalyDetector
from app.ai.classification import EventClassifier
from app.ai.dynamic_pricing import DynamicPricingEngine
from app.ai.prediction import OccupancyPredictor
from app.domain.schemas import NormalizedSensorReading, ParkingSummary
from app.logging_config import configure_logging
from app.services.feature_store_service import FeatureStoreService
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
            "group.id": "parking-ai-consumer",
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([settings.kafka_topic_ai])

    repository = ParkingRepository()
    occupancy_service = OccupancyService()
    predictor = OccupancyPredictor()
    anomaly_detector = SensorAnomalyDetector()
    classifier = EventClassifier()
    pricing_engine = DynamicPricingEngine()

    logger.info("Kafka AI consumer started on topic=%s", settings.kafka_topic_ai)

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

            current_rows = repository.get_current_spot_status(settings.parking_id)
            summary = occupancy_service.build_summary(settings.parking_id, current_rows)

            recent_events = repository.get_recent_events_for_spot(settings.parking_id, reading.spot_id, limit=10)
            feature_row = FeatureStoreService.build_feature_row(
                reading=reading,
                current_occupancy_rate=summary.occupancy_rate,
                recent_events=recent_events,
            )

            prediction_result = predictor.predict(settings.parking_id, feature_row)
            anomaly_result = anomaly_detector.detect(reading)
            classification_result = classifier.classify(reading, anomaly_result)
            pricing_result = pricing_engine.compute(
                occupancy_rate=summary.occupancy_rate,
                predicted_occupancy_rate=prediction_result.predicted_occupancy_rate,
            )

            repository.update_spot_ai_status(
                parking_id=settings.parking_id,
                spot_id=reading.spot_id,
                classification_label=classification_result.label,
                anomaly_label=anomaly_result.anomaly_label,
                anomaly_score=anomaly_result.anomaly_score,
            )

            repository.insert_ai_result(
                ai_type="prediction",
                entity_id=settings.parking_id,
                label=prediction_result.model_name,
                score=prediction_result.predicted_occupancy_rate,
                payload=prediction_result.model_dump(mode="json"),
                parking_id=settings.parking_id,
            )
            repository.insert_ai_result(
                ai_type="anomaly",
                entity_id=reading.spot_id,
                label=anomaly_result.anomaly_label,
                score=anomaly_result.anomaly_score,
                payload=anomaly_result.model_dump(mode="json"),
                parking_id=settings.parking_id,
            )
            repository.insert_ai_result(
                ai_type="classification",
                entity_id=reading.spot_id,
                label=classification_result.label,
                score=classification_result.confidence,
                payload=classification_result.model_dump(mode="json"),
                parking_id=settings.parking_id,
            )
            repository.insert_ai_result(
                ai_type="pricing",
                entity_id=settings.parking_id,
                label=pricing_result.price_tier,
                score=pricing_result.price_eur,
                payload=pricing_result.model_dump(mode="json"),
                parking_id=settings.parking_id,
            )

            enriched_summary = ParkingSummary(
                parking_id=summary.parking_id,
                generated_at=summary.generated_at,
                occupied_spots=summary.occupied_spots,
                free_spots=summary.free_spots,
                occupancy_rate=summary.occupancy_rate,
                predicted_occupancy_rate=prediction_result.predicted_occupancy_rate,
                price_eur=pricing_result.price_eur,
                price_tier=pricing_result.price_tier,
            )
            repository.insert_parking_summary(enriched_summary)

            logger.info(
                "AI pipeline processed | spot=%s anomaly=%s class=%s predicted=%.2f price=%.2f",
                reading.spot_id,
                anomaly_result.anomaly_label,
                classification_result.label,
                prediction_result.predicted_occupancy_rate,
                pricing_result.price_eur,
            )
    except KeyboardInterrupt:
        logger.info("AI consumer stopped by user")
    finally:
        consumer.close()
        repository.close()


if __name__ == "__main__":
    run()
