from __future__ import annotations

import json
from datetime import date

from cassandra.util import uuid_from_time

from app.domain.schemas import (
    AlertResult,
    AnomalyResult,
    ClassificationResult,
    NormalizedSensorReading,
    ParkingSummary,
    PredictionResult,
    PricingResult,
    SensorWindowMetric,
)
from app.storage.cassandra_client import CassandraConnection


class ParkingRepository:
    def __init__(self) -> None:
        self.connection = CassandraConnection()
        self.session = self.connection.connect()

    def insert_sensor_event(
        self,
        reading: NormalizedSensorReading,
        classification_label: str | None = None,
        anomaly_label: str | None = None,
        anomaly_score: float | None = None,
    ) -> None:
        query = """
        INSERT INTO sensor_events_by_spot (
            parking_id, spot_id, event_ts, event_id, zone_id, gateway_id, sensor_id,
            occupied, distance_cm, battery_level, signal_strength, event_type,
            classification_label, anomaly_label, anomaly_score, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.session.execute(
            query,
            (
                reading.parking_id,
                reading.spot_id,
                reading.timestamp,
                uuid_from_time(reading.timestamp),
                reading.zone_id,
                reading.gateway_id,
                reading.sensor_id,
                reading.occupied,
                reading.distance_cm,
                reading.battery_level,
                reading.signal_strength,
                reading.event_type,
                classification_label,
                anomaly_label,
                anomaly_score,
                json.dumps(reading.model_dump(mode="json"), default=str),
            ),
        )

    def upsert_sensor_metadata(self, reading: NormalizedSensorReading) -> None:
        query = """
        INSERT INTO sensor_metadata_by_id (
            parking_id, sensor_id, spot_id, zone_id, gateway_id, sensor_type, unit,
            installed_at, firmware_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.session.execute(
            query,
            (
                reading.parking_id,
                reading.sensor_id,
                reading.spot_id,
                reading.zone_id,
                reading.gateway_id,
                "ultrasonic",
                "cm",
                reading.timestamp,
                "sim-1.0",
                "online",
            ),
        )

    def upsert_current_status(
        self,
        reading: NormalizedSensorReading,
        classification_label: str | None = None,
        anomaly_label: str | None = None,
        anomaly_score: float | None = None,
    ) -> None:
        query = """
        INSERT INTO current_spot_status (
            parking_id, spot_id, zone_id, last_update, sensor_id, gateway_id, occupied,
            distance_cm, battery_level, signal_strength, event_type,
            classification_label, anomaly_label, anomaly_score, last_sequence_no
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.session.execute(
            query,
            (
                reading.parking_id,
                reading.spot_id,
                reading.zone_id,
                reading.timestamp,
                reading.sensor_id,
                reading.gateway_id,
                reading.occupied,
                reading.distance_cm,
                reading.battery_level,
                reading.signal_strength,
                reading.event_type,
                classification_label,
                anomaly_label,
                anomaly_score,
                reading.sequence_no,
            ),
        )

    def update_spot_ai_status(
        self,
        parking_id: str,
        spot_id: str,
        classification_label: str | None,
        anomaly_label: str | None,
        anomaly_score: float | None,
    ) -> None:
        query = """
        UPDATE current_spot_status
        SET classification_label = ?, anomaly_label = ?, anomaly_score = ?
        WHERE parking_id = ? AND spot_id = ?
        """
        self.session.execute(query, (classification_label, anomaly_label, anomaly_score, parking_id, spot_id))

    def get_current_spot_status(self, parking_id: str) -> list[dict]:
        query = "SELECT * FROM current_spot_status WHERE parking_id = ?"
        rows = self.session.execute(query, (parking_id,))
        return list(rows)

    def insert_parking_summary(self, summary: ParkingSummary) -> None:
        bucket_date = summary.generated_at.date()
        query = """
        INSERT INTO parking_summary_by_minute (
            parking_id, bucket_date, minute_ts, occupied_spots, free_spots, occupancy_rate,
            predicted_occupancy_rate, price_eur, price_tier
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.session.execute(
            query,
            (
                summary.parking_id,
                bucket_date,
                summary.generated_at,
                summary.occupied_spots,
                summary.free_spots,
                summary.occupancy_rate,
                summary.predicted_occupancy_rate,
                summary.price_eur,
                summary.price_tier,
            ),
        )

    def insert_window_metric(self, metric: SensorWindowMetric) -> None:
        bucket_date = metric.window_start.date()
        query = """
        INSERT INTO sensor_window_metrics_by_minute (
            parking_id, bucket_date, window_start, window_end, event_count,
            occupied_event_count, avg_distance_cm, avg_battery_level, weak_signal_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.session.execute(
            query,
            (
                metric.parking_id,
                bucket_date,
                metric.window_start,
                metric.window_end,
                metric.event_count,
                metric.occupied_event_count,
                metric.avg_distance_cm,
                metric.avg_battery_level,
                metric.weak_signal_count,
            ),
        )

    def insert_ai_result(self, ai_type: str, entity_id: str, label: str, score: float, payload: dict, parking_id: str) -> None:
        generated_at = payload.get("generated_at")
        if isinstance(generated_at, str):
            from datetime import datetime
            generated_at = datetime.fromisoformat(generated_at)
        bucket_date = generated_at.date() if generated_at else date.today()
        query = """
        INSERT INTO ai_results_by_time (
            parking_id, ai_type, bucket_date, generated_at, entity_id, label, score, json_payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.session.execute(
            query,
            (
                parking_id,
                ai_type,
                bucket_date,
                generated_at,
                entity_id,
                label,
                score,
                json.dumps(payload, default=str),
            ),
        )

    def get_latest_ai_results(self, parking_id: str, ai_type: str, day: date | None = None, limit: int = 20) -> list[dict]:
        bucket_date = day or date.today()
        query = """
        SELECT * FROM ai_results_by_time
        WHERE parking_id = ? AND ai_type = ? AND bucket_date = ?
        LIMIT ?
        """
        rows = self.session.execute(query, (parking_id, ai_type, bucket_date, limit))
        return list(rows)

    def insert_alert(self, alert: AlertResult) -> None:
        bucket_date = alert.generated_at.date()
        query = """
        INSERT INTO alerts_by_time (
            parking_id, bucket_date, generated_at, entity_id, alert_type, severity, message, score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.session.execute(
            query,
            (
                alert.parking_id,
                bucket_date,
                alert.generated_at,
                alert.entity_id,
                alert.alert_type,
                alert.severity,
                alert.message,
                alert.score,
            ),
        )

    def get_latest_alerts(self, parking_id: str, day: date | None = None, limit: int = 20) -> list[dict]:
        bucket_date = day or date.today()
        query = """
        SELECT * FROM alerts_by_time
        WHERE parking_id = ? AND bucket_date = ?
        LIMIT ?
        """
        rows = self.session.execute(query, (parking_id, bucket_date, limit))
        return list(rows)

    def get_recent_events_for_spot(self, parking_id: str, spot_id: str, limit: int = 20) -> list[dict]:
        query = """
        SELECT * FROM sensor_events_by_spot
        WHERE parking_id = ? AND spot_id = ?
        LIMIT ?
        """
        rows = self.session.execute(query, (parking_id, spot_id, limit))
        return list(rows)

    def close(self) -> None:
        self.connection.shutdown()
