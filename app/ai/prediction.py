from __future__ import annotations

import logging

import joblib

from app.ai.features import to_dataframe
from app.domain.schemas import PredictionResult
from app.settings import get_settings
from app.utils.helpers import clamp
from app.utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class OccupancyPredictor:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_path = settings.models_dir / "occupancy_predictor.joblib"
        self.model = None
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                logger.info("Loaded occupancy predictor model from %s", self.model_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to load predictor model: %s", exc)

    def predict(self, parking_id: str, feature_row: dict) -> PredictionResult:
        if self.model is not None:
            df = to_dataframe(feature_row)
            predicted = float(self.model.predict(df)[0])
            model_name = "random_forest_regressor"
        else:
            predicted = self._heuristic_predict(feature_row)
            model_name = "heuristic_baseline"

        predicted = clamp(round(predicted, 4), 0.0, 1.0)
        return PredictionResult(
            parking_id=parking_id,
            generated_at=utc_now(),
            horizon_minutes=30,
            predicted_occupancy_rate=predicted,
            model_name=model_name,
            features=feature_row,
        )

    @staticmethod
    def _heuristic_predict(feature_row: dict) -> float:
        current = feature_row["current_occupancy_rate"]
        hour = feature_row["hour"]

        if 7 <= hour <= 9:
            bias = 0.16
        elif 10 <= hour <= 14:
            bias = 0.08
        elif 15 <= hour <= 18:
            bias = 0.12
        elif 19 <= hour <= 22:
            bias = -0.10
        else:
            bias = -0.05

        return current + bias
