from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier

from app.ai.features import PREDICTION_FEATURE_COLUMNS
from app.logging_config import configure_logging
from app.settings import get_settings

logger = logging.getLogger(__name__)


def train_prediction_model(df: pd.DataFrame, output_path: Path) -> None:
    feature_cols = [col for col in PREDICTION_FEATURE_COLUMNS if col in df.columns]
    target_col = "target_occupancy_rate_next_30min"

    X = df[feature_cols]
    y = df[target_col]

    model = RandomForestRegressor(
        n_estimators=120,
        max_depth=10,
        random_state=42,
    )
    model.fit(X, y)
    joblib.dump(model, output_path)
    logger.info("Saved occupancy predictor model -> %s", output_path)


def train_sensor_fault_classifier(output_path: Path) -> None:
    rng = np.random.default_rng(2026)
    rows: list[list[float]] = []
    labels: list[str] = []

    for _ in range(450):
        occupied = int(rng.integers(0, 2))
        distance = rng.normal(22, 5) if occupied else rng.normal(185, 24)
        rows.append([float(np.clip(distance, 5, 260)), float(rng.uniform(40, 100)), float(rng.uniform(-78, -45)), occupied])
        labels.append("normal")

    for _ in range(130):
        occupied = int(rng.integers(0, 2))
        rows.append([float(rng.uniform(10, 230)), float(rng.uniform(4, 14)), float(rng.uniform(-80, -45)), occupied])
        labels.append("low_battery")

    for _ in range(130):
        occupied = int(rng.integers(0, 2))
        rows.append([float(rng.uniform(10, 230)), float(rng.uniform(35, 95)), float(rng.uniform(-103, -91)), occupied])
        labels.append("signal_weak")

    for _ in range(160):
        occupied = int(rng.integers(0, 2))
        distance = rng.uniform(90, 230) if occupied else rng.uniform(8, 48)
        rows.append([float(distance), float(rng.uniform(40, 100)), float(rng.uniform(-78, -45)), occupied])
        labels.append("distance_outlier")

    model = DecisionTreeClassifier(max_depth=5, min_samples_leaf=8, random_state=42)
    model.fit(np.array(rows), np.array(labels))
    joblib.dump(model, output_path)
    logger.info("Saved sensor fault DecisionTreeClassifier -> %s", output_path)


def main() -> None:
    configure_logging()
    settings = get_settings()
    dataset_path = settings.data_dir / "seed" / "historical_occupancy_sample.csv"

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Historical dataset not found: {dataset_path}. Run `python -m scripts.seed_historical_data` first."
        )

    df = pd.read_csv(dataset_path)
    prediction_model_path = settings.models_dir / "occupancy_predictor.joblib"
    sensor_fault_model_path = settings.models_dir / "sensor_fault_classifier.joblib"

    train_prediction_model(df, prediction_model_path)
    train_sensor_fault_classifier(sensor_fault_model_path)
    logger.info("Model training completed successfully.")


if __name__ == "__main__":
    main()
