from __future__ import annotations

import pandas as pd


PREDICTION_FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "is_weekend",
    "current_occupancy_rate",
    "distance_cm",
    "battery_level",
    "signal_strength",
    "recent_event_count",
    "avg_recent_distance",
]


def to_dataframe(feature_row: dict) -> pd.DataFrame:
    return pd.DataFrame([feature_row], columns=PREDICTION_FEATURE_COLUMNS)
