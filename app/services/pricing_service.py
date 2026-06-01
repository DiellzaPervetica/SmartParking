from __future__ import annotations

from app.ai.dynamic_pricing import DynamicPricingEngine
from app.domain.schemas import PricingResult


class PricingService:
    def __init__(self) -> None:
        self.engine = DynamicPricingEngine()

    def generate(self, occupancy_rate: float, predicted_occupancy_rate: float) -> PricingResult:
        return self.engine.compute(occupancy_rate=occupancy_rate, predicted_occupancy_rate=predicted_occupancy_rate)
