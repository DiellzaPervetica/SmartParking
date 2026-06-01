from __future__ import annotations

from app.domain.enums import ClassificationLabel
from app.domain.schemas import AnomalyResult, ClassificationResult, NormalizedSensorReading
from app.utils.time_utils import utc_now


class EventClassifier:
    def classify(self, reading: NormalizedSensorReading, anomaly_result: AnomalyResult) -> ClassificationResult:
        if anomaly_result.anomaly_label != "normal" and anomaly_result.anomaly_score >= 0.65:
            label = ClassificationLabel.SENSOR_FAULT.value
            confidence = 0.85
        elif anomaly_result.anomaly_label != "normal":
            label = ClassificationLabel.SUSPICIOUS.value
            confidence = 0.75
        elif reading.occupied:
            label = ClassificationLabel.OCCUPIED.value
            confidence = 0.98
        else:
            label = ClassificationLabel.FREE.value
            confidence = 0.98

        return ClassificationResult(
            parking_id=reading.parking_id,
            generated_at=utc_now(),
            spot_id=reading.spot_id,
            label=label,
            confidence=confidence,
        )
