from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from app.settings import get_settings


def generate_dataset(days: int = 21) -> pd.DataFrame:
    rng = np.random.default_rng(2026)
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(days=days)

    rows = []
    current_occ = 0.35
    total_spots = get_settings().total_spots

    for step in range(days * 24 * 2):  # every 30 minutes
        ts = start + timedelta(minutes=30 * step)
        hour = ts.hour
        weekday = ts.weekday()
        is_weekend = 1 if weekday >= 5 else 0

        if 7 <= hour <= 9:
            pressure = 0.18
        elif 10 <= hour <= 14:
            pressure = 0.10
        elif 15 <= hour <= 18:
            pressure = 0.14
        elif 19 <= hour <= 22:
            pressure = -0.12
        else:
            pressure = -0.05

        if is_weekend:
            pressure *= 0.8

        noise = rng.normal(0, 0.04)
        next_occ = float(np.clip(current_occ + pressure + noise, 0.05, 0.98))

        distance_cm = 20 if current_occ > 0.7 else 160
        if rng.random() < current_occ:
            distance_cm = float(rng.normal(24, 4))
        else:
            distance_cm = float(rng.normal(180, 20))

        battery_level = float(np.clip(rng.normal(82, 8), 20, 100))
        signal_strength = int(np.clip(rng.normal(-65, 8), -100, -35))
        recent_event_count = int(np.clip(rng.normal(5, 2), 1, 12))
        avg_recent_distance = float(np.clip(distance_cm + rng.normal(0, 8), 8, 250))

        rows.append(
            {
                "timestamp": ts.isoformat(),
                "hour": hour,
                "day_of_week": weekday,
                "is_weekend": is_weekend,
                "current_occupancy_rate": round(current_occ, 4),
                "distance_cm": round(distance_cm, 2),
                "battery_level": round(battery_level, 2),
                "signal_strength": signal_strength,
                "recent_event_count": recent_event_count,
                "avg_recent_distance": round(avg_recent_distance, 2),
                "target_occupancy_rate_next_30min": round(next_occ, 4),
                "occupied_spots_estimate": int(round(current_occ * total_spots)),
            }
        )
        current_occ = next_occ

    return pd.DataFrame(rows)


def main() -> None:
    settings = get_settings()
    output_path = settings.data_dir / "seed" / "historical_occupancy_sample.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_dataset(days=21)
    df.to_csv(output_path, index=False)
    print(f"Generated historical dataset -> {output_path}")


if __name__ == "__main__":
    main()
