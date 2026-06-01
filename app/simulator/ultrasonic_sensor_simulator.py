from __future__ import annotations

import random


class UltrasonicSensorSimulator:
    def __init__(self, seed: int = 1234) -> None:
        self.random = random.Random(seed)

    def simulate_distance_cm(self, occupied: bool) -> float:
        if occupied:
            base = self.random.uniform(12, 30)
            noise = self.random.uniform(-2, 2)
            return round(max(5.0, base + noise), 2)
        base = self.random.uniform(150, 240)
        noise = self.random.uniform(-5, 5)
        return round(max(50.0, base + noise), 2)

    def simulate_battery_level(self, previous: float | None = None) -> float:
        if previous is None:
            return round(self.random.uniform(80, 100), 2)
        drain = self.random.uniform(0.01, 0.05)
        return round(max(5.0, previous - drain), 2)

    def simulate_signal_strength(self) -> int:
        return int(self.random.uniform(-78, -48))
