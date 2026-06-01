from __future__ import annotations

import json
import math
from typing import Any

from app.ai.dynamic_pricing import DynamicPricingEngine
from app.services.health_service import HealthService
from app.services.occupancy_service import OccupancyService
from app.services.simulation_snapshot_service import SimulationSnapshotService
from app.settings import get_settings
from app.storage.repositories import ParkingRepository


class DashboardService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.simulation = SimulationSnapshotService()
        self.pricing = DynamicPricingEngine()

    def build(self, scenario: str = "auto") -> dict[str, Any]:
        try:
            repository = ParkingRepository()
            try:
                rows = repository.get_current_spot_status(self.settings.parking_id)
                if not rows:
                    fallback = self.simulation.generate(scenario=scenario)
                    fallback["source"] = "simulation_until_cassandra_has_rows"
                    return fallback

                predictions = repository.get_latest_ai_results(self.settings.parking_id, "prediction", limit=1)
                pricing_rows = repository.get_latest_ai_results(self.settings.parking_id, "pricing", limit=1)
                alerts = repository.get_latest_alerts(self.settings.parking_id, limit=10)
                return self._from_cassandra(rows, predictions, pricing_rows, alerts)
            finally:
                repository.close()
        except Exception as exc:  # noqa: BLE001
            fallback = self.simulation.generate(scenario=scenario)
            fallback["source"] = "simulation_fallback"
            fallback["fallback_reason"] = str(exc)
            return fallback

    def _from_cassandra(
        self,
        rows: list[dict],
        predictions: list[dict],
        pricing_rows: list[dict],
        alerts: list[dict],
    ) -> dict[str, Any]:
        ordered_rows = sorted(rows, key=lambda row: row.get("spot_id", ""))
        summary_model = OccupancyService.build_summary(self.settings.parking_id, ordered_rows)
        prediction_payload = self._json_payload(predictions[0]) if predictions else {}
        pricing_payload = self._json_payload(pricing_rows[0]) if pricing_rows else {}

        predicted_rate = float(
            prediction_payload.get("predicted_occupancy_rate")
            or summary_model.predicted_occupancy_rate
            or summary_model.occupancy_rate
        )
        price_eur = pricing_payload.get("price_eur")
        price_tier = pricing_payload.get("price_tier")
        if price_eur is None or price_tier is None:
            pricing = self.pricing.compute(summary_model.occupancy_rate, predicted_rate)
            price_eur = pricing.price_eur
            price_tier = pricing.price_tier

        spots = self._shape_spots(ordered_rows)
        zones = self.simulation._build_zones(spots)
        health = HealthService.summarize_sensor_health(ordered_rows)
        health["online_spots"] = len(spots) - health["stale_spots"]
        health["health_score"] = self.simulation._health_score(health, len(spots))

        summary = summary_model.model_dump(mode="json")
        summary.update(
            {
                "total_spots": len(spots),
                "predicted_occupancy_rate": round(predicted_rate, 4),
                "price_eur": float(price_eur),
                "price_tier": str(price_tier),
            }
        )

        anomalies = [spot for spot in spots if spot.get("anomaly_label") not in {None, "normal"}]
        return {
            "parking_id": self.settings.parking_id,
            "parking_name": self.settings.parking_name,
            "generated_at": summary_model.generated_at,
            "scenario": "live",
            "source": "cassandra_spark_streaming",
            "summary": summary,
            "pricing": pricing_payload or self.pricing.compute(summary_model.occupancy_rate, predicted_rate).model_dump(mode="json"),
            "zones": zones,
            "spots": spots,
            "health": health,
            "digital_signs": self.simulation._build_digital_signs(summary, zones, str(price_tier)),
            "gateway": self.simulation._build_gateway_status(),
            "ai": {
                "prediction": prediction_payload,
                "anomalies": anomalies,
                "alerts": alerts,
            },
        }

    def _shape_spots(self, rows: list[dict]) -> list[dict[str, Any]]:
        total = max(len(rows), 1)
        columns = min(5, max(2, math.ceil(math.sqrt(total))))
        spots: list[dict[str, Any]] = []
        for idx, row in enumerate(rows, start=1):
            spots.append(
                {
                    "parking_id": row.get("parking_id"),
                    "zone_id": row.get("zone_id"),
                    "spot_id": row.get("spot_id"),
                    "sensor_id": row.get("sensor_id"),
                    "gateway_id": row.get("gateway_id"),
                    "last_update": row.get("last_update"),
                    "occupied": bool(row.get("occupied")),
                    "distance_cm": float(row.get("distance_cm") or 0.0),
                    "battery_level": float(row.get("battery_level") or 0.0),
                    "signal_strength": int(row.get("signal_strength") or -120),
                    "event_type": row.get("event_type") or "heartbeat",
                    "classification_label": row.get("classification_label") or ("occupied" if row.get("occupied") else "free"),
                    "anomaly_label": row.get("anomaly_label") or "normal",
                    "anomaly_score": float(row.get("anomaly_score") or 0.0),
                    "last_sequence_no": row.get("last_sequence_no"),
                    "row": math.ceil(idx / columns),
                    "column": ((idx - 1) % columns) + 1,
                }
            )
        return spots

    @staticmethod
    def _json_payload(row: dict) -> dict[str, Any]:
        raw_payload = row.get("json_payload")
        if not raw_payload:
            return {}
        if isinstance(raw_payload, dict):
            return raw_payload
        return json.loads(raw_payload)
