from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FlowProfile:
    arrival_probability: float
    departure_probability: float


class VehicleFlowSimulator:
    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)

    def get_hourly_profile(self, dt: datetime) -> FlowProfile:
        hour = dt.hour
        weekday = dt.weekday()

        if 7 <= hour <= 9:
            return FlowProfile(arrival_probability=0.30, departure_probability=0.10)
        if 10 <= hour <= 14:
            return FlowProfile(arrival_probability=0.18, departure_probability=0.12)
        if 15 <= hour <= 18:
            return FlowProfile(arrival_probability=0.24, departure_probability=0.18)
        if 19 <= hour <= 22:
            return FlowProfile(arrival_probability=0.10, departure_probability=0.22)
        if weekday >= 5:
            return FlowProfile(arrival_probability=0.12, departure_probability=0.14)
        return FlowProfile(arrival_probability=0.06, departure_probability=0.08)

    def should_arrive(self, dt: datetime) -> bool:
        profile = self.get_hourly_profile(dt)
        return self.random.random() < profile.arrival_probability

    def should_depart(self, dt: datetime) -> bool:
        profile = self.get_hourly_profile(dt)
        return self.random.random() < profile.departure_probability
