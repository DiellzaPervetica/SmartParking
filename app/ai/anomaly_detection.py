from __future__ import annotations

import logging

import joblib
import numpy as np

from app.domain.enums import AnomalyLabel
from app.domain.schemas import AnomalyResult, NormalizedSensorReading
from app.settings import get_settings
from app.utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class SensorAnomalyDetector:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_path = settings.models_dir / "sensor_fault_classifier.joblib"
        self.model = None
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                logger.info("Loaded sensor fault classifier model from %s", self.model_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to load sensor fault classifier model: %s", exc)

    def detect(self, reading: NormalizedSensorReading) -> AnomalyResult:
        reasons: list[str] = []

        if reading.battery_level < 15:
            reasons.append("battery below 15%")
        if reading.signal_strength < -90:
            reasons.append("very weak signal")
        if reading.occupied and reading.distance_cm > 60:
            reasons.append("distance too large for occupied spot")
        if (not reading.occupied) and reading.distance_cm < 60:
            reasons.append("distance too small for free spot")

        score = 0.05
        label = AnomalyLabel.NORMAL.value

        if self.model is not None:
            features = np.array(
                [[reading.distance_cm, reading.battery_level, reading.signal_strength, int(reading.occupied)]]
            )
            prediction = str(self.model.predict(features)[0])
            if prediction != AnomalyLabel.NORMAL.value:
                reasons.append(f"DecisionTreeClassifier predicted {prediction}")
                label = prediction

        if reasons:
            score = min(0.95, 0.25 + (0.18 * len(reasons)))
            if label != AnomalyLabel.NORMAL.value:
                pass
            elif "battery below 15%" in reasons:
                label = AnomalyLabel.LOW_BATTERY.value
            elif "very weak signal" in reasons:
                label = AnomalyLabel.SIGNAL_WEAK.value
            else:
                label = AnomalyLabel.DISTANCE_OUTLIER.value

        return AnomalyResult(
            parking_id=reading.parking_id,
            generated_at=utc_now(),
            spot_id=reading.spot_id,
            anomaly_label=label,
            anomaly_score=round(score, 4),
            reasons=reasons or ["normal telemetry"],
        )
