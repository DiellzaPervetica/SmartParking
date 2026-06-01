from __future__ import annotations

import math
import random
from typing import Any

from app.ai.dynamic_pricing import DynamicPricingEngine
from app.services.health_service import HealthService
from app.settings import get_settings
from app.simulator.parking_layout import build_default_parking_layout
from app.utils.helpers import clamp
from app.utils.time_utils import utc_now


class SimulationSnapshotService:
    """Builds a light, presentation-ready parking state without external services."""

    SCENARIO_HOURS = {
        "auto": None,
        "morning_peak": 8,
        "afternoon_peak": 16,
        "evening_relief": 20,
        "maintenance": 12,
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pricing = DynamicPricingEngine()

    def generate(self, scenario: str = "auto") -> dict[str, Any]:
        scenario_key = scenario if scenario in self.SCENARIO_HOURS else "auto"
        now = utc_now()
        effective_hour = self.SCENARIO_HOURS[scenario_key] or now.hour
        seed = self._seed(now, scenario_key)
        occupancy_rate = self._target_occupancy_rate(effective_hour, now.weekday(), now.minute, scenario_key)
        spots = self._build_spots(now, occupancy_rate, seed, scenario_key)
        summary = self._build_summary(spots)
        predicted_rate = self._predict_occupancy_rate(summary["occupancy_rate"], effective_hour)
        pricing_time = now.replace(hour=effective_hour)
        pricing = self.pricing.compute(
            occupancy_rate=summary["occupancy_rate"],
            predicted_occupancy_rate=predicted_rate,
            generated_at=pricing_time,
        )
        zones = self._build_zones(spots)
        health = HealthService.summarize_sensor_health(spots)
        health["online_spots"] = len(spots) - health["stale_spots"]
        health["health_score"] = self._health_score(health, len(spots))

        summary.update(
            {
                "predicted_occupancy_rate": predicted_rate,
                "price_eur": pricing.price_eur,
                "price_tier": pricing.price_tier,
                "total_spots": len(spots),
            }
        )

        return {
            "parking_id": self.settings.parking_id,
            "parking_name": self.settings.parking_name,
            "generated_at": now,
            "scenario": scenario_key,
            "source": "lightweight_simulation",
            "summary": summary,
            "pricing": pricing.model_dump(mode="json"),
            "zones": zones,
            "spots": spots,
            "health": health,
            "digital_signs": self._build_digital_signs(summary, zones, pricing.price_tier),
            "gateway": self._build_gateway_status(),
            "ai": {
                "prediction": {
                    "horizon_minutes": 30,
                    "predicted_occupancy_rate": predicted_rate,
                    "model_name": "lightweight_temporal_heuristic",
                },
                "anomalies": [spot for spot in spots if spot["anomaly_label"] != "normal"],
            },
        }

    def _build_spots(
        self,
        now,
        occupancy_rate: float,
        seed: int,
        scenario: str,
    ) -> list[dict[str, Any]]:
        layout = build_default_parking_layout()
        total = len(layout)
        rng = random.Random(seed)
        occupied_count = int(clamp(round(total * occupancy_rate + rng.uniform(-1.0, 1.0)), 0, total))
        columns = min(5, max(2, math.ceil(math.sqrt(total))))

        weighted_spots = []
        for idx, spot in enumerate(layout, start=1):
            entrance_bias = 0.10 if idx % columns in {1, 2} else 0.0
            zone_bias = 0.06 if spot.zone_id == "A" else -0.03
            weighted_spots.append((rng.random() + entrance_bias + zone_bias, spot.spot_id))

        occupied_ids = {spot_id for _, spot_id in sorted(weighted_spots, reverse=True)[:occupied_count]}
        spots: list[dict[str, Any]] = []

        for idx, spot in enumerate(layout, start=1):
            occupied = spot.spot_id in occupied_ids
            distance_cm = self._distance_cm(rng, occupied)
            battery_level = self._battery_level(rng, idx, seed, scenario)
            signal_strength = self._signal_strength(rng, idx, seed, scenario)
            anomaly_label, anomaly_score = self._classify_sensor_health(
                occupied=occupied,
                distance_cm=distance_cm,
                battery_level=battery_level,
                signal_strength=signal_strength,
            )
            classification_label = "sensor_fault" if anomaly_label != "normal" else "occupied" if occupied else "free"

            spots.append(
                {
                    "parking_id": spot.parking_id,
                    "zone_id": spot.zone_id,
                    "spot_id": spot.spot_id,
                    "sensor_id": spot.sensor_id,
                    "gateway_id": spot.gateway_id,
                    "last_update": now,
                    "occupied": occupied,
                    "distance_cm": distance_cm,
                    "battery_level": battery_level,
                    "signal_strength": signal_strength,
                    "event_type": "state_change" if rng.random() < 0.24 else "heartbeat",
                    "classification_label": classification_label,
                    "anomaly_label": anomaly_label,
                    "anomaly_score": anomaly_score,
                    "last_sequence_no": 9000 + seed % 1000 + idx,
                    "row": math.ceil(idx / columns),
                    "column": ((idx - 1) % columns) + 1,
                }
            )

        return spots

    def _build_summary(self, spots: list[dict[str, Any]]) -> dict[str, Any]:
        occupied = sum(1 for spot in spots if spot["occupied"])
        total = len(spots)
        free = total - occupied
        return {
            "occupied_spots": occupied,
            "free_spots": free,
            "occupancy_rate": round(occupied / total, 4) if total else 0.0,
        }

    def _build_zones(self, spots: list[dict[str, Any]]) -> list[dict[str, Any]]:
        zones: list[dict[str, Any]] = []
        for zone_id in sorted({spot["zone_id"] for spot in spots}):
            zone_spots = [spot for spot in spots if spot["zone_id"] == zone_id]
            occupied = sum(1 for spot in zone_spots if spot["occupied"])
            total = len(zone_spots)
            zones.append(
                {
                    "zone_id": zone_id,
                    "total_spots": total,
                    "occupied_spots": occupied,
                    "free_spots": total - occupied,
                    "occupancy_rate": round(occupied / total, 4) if total else 0.0,
                    "spots": [spot["spot_id"] for spot in zone_spots],
                }
            )
        return zones

    def _build_digital_signs(
        self,
        summary: dict[str, Any],
        zones: list[dict[str, Any]],
        price_tier: str,
    ) -> list[dict[str, Any]]:
        best_zone = max(zones, key=lambda zone: zone["free_spots"]) if zones else None
        price_message = {
            "low": "Tarife e ulet",
            "medium": "Tarife normale",
            "high": "Tarife peak",
        }.get(price_tier, "Tarife aktive")

        signs = [
            {
                "id": "entry",
                "title": "Tabela hyrese",
                "primary": f"{summary['free_spots']} vende te lira",
                "secondary": f"Cmimi dinamik {summary['price_eur']:.2f} EUR/ore",
                "tone": "good" if summary["free_spots"] >= 6 else "warn",
            },
            {
                "id": "pricing",
                "title": "Tabela e cmimit",
                "primary": price_message,
                "secondary": f"Forecast 30 min: {summary['predicted_occupancy_rate'] * 100:.0f}% okupim",
                "tone": price_tier,
            },
        ]

        if best_zone:
            signs.append(
                {
                    "id": "guidance",
                    "title": "Orientimi",
                    "primary": f"Zona {best_zone['zone_id']}",
                    "secondary": f"{best_zone['free_spots']} vende te lira ne kete zone",
                    "tone": "good" if best_zone["free_spots"] else "full",
                }
            )

        return signs

    def _build_gateway_status(self) -> list[dict[str, str]]:
        return [
            {"name": "Gateway", "status": "online", "detail": "normalizim lokal"},
            {"name": "Kafka", "status": "ready", "detail": "event streaming"},
            {"name": "Spark", "status": "ready", "detail": "stream processing"},
            {"name": "Cassandra", "status": "ready", "detail": "ruajtje historike"},
            {"name": "AI/API", "status": "online", "detail": "prediction + pricing"},
        ]

    def _target_occupancy_rate(self, hour: int, weekday: int, minute: int, scenario: str) -> float:
        if scenario == "morning_peak":
            base = 0.82
        elif scenario == "afternoon_peak":
            base = 0.76
        elif scenario == "evening_relief":
            base = 0.42
        elif scenario == "maintenance":
            base = 0.58
        elif weekday >= 5:
            base = 0.52 if 10 <= hour <= 20 else 0.36
        elif 7 <= hour <= 9:
            base = 0.78
        elif 10 <= hour <= 14:
            base = 0.62
        elif 15 <= hour <= 18:
            base = 0.74
        elif 19 <= hour <= 22:
            base = 0.46
        else:
            base = 0.30

        minute_wave = math.sin((minute / 60) * math.tau) * 0.035
        return round(clamp(base + minute_wave, 0.10, 0.95), 4)

    def _predict_occupancy_rate(self, current_rate: float, hour: int) -> float:
        if 7 <= hour <= 9:
            bias = 0.12
        elif 10 <= hour <= 14:
            bias = 0.06
        elif 15 <= hour <= 18:
            bias = 0.09
        elif 19 <= hour <= 22:
            bias = -0.08
        else:
            bias = -0.04
        return round(clamp(current_rate + bias, 0.02, 0.98), 4)

    def _health_score(self, health: dict[str, int], total: int) -> int:
        if total == 0:
            return 100
        penalties = health["low_battery_spots"] * 10 + health["weak_signal_spots"] * 7 + health["stale_spots"] * 12
        return int(clamp(100 - penalties, 0, 100))

    def _seed(self, now, scenario: str) -> int:
        time_bucket = int(now.timestamp()) // 30
        scenario_offset = sum(ord(character) for character in scenario)
        return (time_bucket + scenario_offset + self.settings.total_spots * 17) % 1_000_000

    @staticmethod
    def _distance_cm(rng: random.Random, occupied: bool) -> float:
        if occupied:
            return round(max(5.0, rng.uniform(14.0, 32.0) + rng.uniform(-2.0, 2.0)), 2)
        return round(max(50.0, rng.uniform(155.0, 230.0) + rng.uniform(-5.0, 5.0)), 2)

    @staticmethod
    def _battery_level(rng: random.Random, index: int, seed: int, scenario: str) -> float:
        if scenario == "maintenance" and index in {4, 11}:
            return round(rng.uniform(11.0, 14.5), 2)
        base = 91.0 - ((index * 3.1 + seed % 29) % 38)
        return round(clamp(base + rng.uniform(-2.5, 2.5), 16.0, 99.0), 2)

    @staticmethod
    def _signal_strength(rng: random.Random, index: int, seed: int, scenario: str) -> int:
        if scenario == "maintenance" and index in {7, 16}:
            return int(rng.uniform(-94, -91))
        base = -50 - ((index * 4 + seed) % 31)
        return int(clamp(base + rng.uniform(-3, 3), -96, -45))

    @staticmethod
    def _classify_sensor_health(
        occupied: bool,
        distance_cm: float,
        battery_level: float,
        signal_strength: int,
    ) -> tuple[str, float]:
        if battery_level < 15:
            return "low_battery", 0.78
        if signal_strength < -90:
            return "signal_weak", 0.72
        if occupied and distance_cm > 60:
            return "distance_outlier", 0.74
        if not occupied and distance_cm < 60:
            return "distance_outlier", 0.74
        return "normal", 0.05
