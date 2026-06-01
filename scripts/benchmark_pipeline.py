from __future__ import annotations

import time

from app.ai.anomaly_detection import SensorAnomalyDetector
from app.ai.classification import EventClassifier
from app.ai.prediction import OccupancyPredictor
from app.domain.enums import EventType
from app.domain.schemas import NormalizedSensorReading
from app.gateway.normalizer import normalize_payload
from app.gateway.validator import validate_sensor_payload
from app.mqtt_layer.payload_builder import build_sensor_payload
from app.services.feature_store_service import FeatureStoreService
from app.simulator.parking_layout import build_default_parking_layout
from app.simulator.ultrasonic_sensor_simulator import UltrasonicSensorSimulator
from app.utils.time_utils import utc_now


def main(iterations: int = 500) -> None:
    spots = build_default_parking_layout()
    sensor = UltrasonicSensorSimulator(seed=3030)
    anomaly_detector = SensorAnomalyDetector()
    classifier = EventClassifier()
    predictor = OccupancyPredictor()
    processed = 0
    started = time.perf_counter()

    for index in range(iterations):
        spot = spots[index % len(spots)]
        occupied = index % 3 != 0
        payload = build_sensor_payload(
            spot=spot,
            occupied=occupied,
            distance_cm=sensor.simulate_distance_cm(occupied),
            battery_level=sensor.simulate_battery_level(92.0),
            signal_strength=sensor.simulate_signal_strength(),
            event_type=EventType.STATE_CHANGE,
            timestamp=utc_now(),
        )
        ok, validated, error = validate_sensor_payload(payload)
        if not ok or validated is None:
            raise RuntimeError(error)

        reading = normalize_payload(validated)
        normalized = NormalizedSensorReading(**reading.model_dump())
        anomaly = anomaly_detector.detect(normalized)
        classifier.classify(normalized, anomaly)
        features = FeatureStoreService.build_feature_row(
            reading=normalized,
            current_occupancy_rate=0.62,
            recent_events=[],
        )
        predictor.predict(normalized.parking_id, features)
        processed += 1

    elapsed = time.perf_counter() - started
    throughput = processed / elapsed if elapsed else 0.0
    print(f"Processed {processed} synthetic events in {elapsed:.3f}s")
    print(f"Local validation + ML throughput: {throughput:.1f} events/second")
    print("This benchmark excludes network, Kafka, Spark and Cassandra I/O.")


if __name__ == "__main__":
    main()
