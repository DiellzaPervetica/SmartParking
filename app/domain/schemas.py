from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SensorPayload(BaseModel):
    event_id: str
    parking_id: str
    parking_name: str
    zone_id: str
    spot_id: str
    sensor_id: str
    gateway_id: str
    sequence_no: int
    timestamp: datetime
    occupied: bool
    distance_cm: float = Field(ge=0, le=500)
    battery_level: float = Field(ge=0, le=100)
    signal_strength: int = Field(ge=-120, le=0)
    event_type: str


class NormalizedSensorReading(SensorPayload):
    ingest_ts: datetime


class SpotStatus(BaseModel):
    parking_id: str
    zone_id: str
    spot_id: str
    sensor_id: str
    gateway_id: str
    last_update: datetime
    occupied: bool
    distance_cm: float
    battery_level: float
    signal_strength: int
    event_type: str
    classification_label: str | None = None
    anomaly_label: str | None = None
    anomaly_score: float | None = None
    last_sequence_no: int | None = None


class ParkingSummary(BaseModel):
    parking_id: str
    generated_at: datetime
    occupied_spots: int
    free_spots: int
    occupancy_rate: float
    predicted_occupancy_rate: float | None = None
    price_eur: float | None = None
    price_tier: str | None = None


class PredictionResult(BaseModel):
    parking_id: str
    generated_at: datetime
    horizon_minutes: int
    predicted_occupancy_rate: float
    model_name: str
    features: dict[str, Any]


class AnomalyResult(BaseModel):
    parking_id: str
    generated_at: datetime
    spot_id: str
    anomaly_label: str
    anomaly_score: float
    reasons: list[str]


class ClassificationResult(BaseModel):
    parking_id: str
    generated_at: datetime
    spot_id: str
    label: str
    confidence: float


class PricingResult(BaseModel):
    parking_id: str
    generated_at: datetime
    price_eur: float
    price_tier: str
    rationale: dict[str, Any]


class AlertResult(BaseModel):
    parking_id: str
    generated_at: datetime
    entity_id: str
    alert_type: str
    severity: str
    message: str
    score: float


class SensorWindowMetric(BaseModel):
    parking_id: str
    window_start: datetime
    window_end: datetime
    event_count: int
    occupied_event_count: int
    avg_distance_cm: float
    avg_battery_level: float
    weak_signal_count: int
