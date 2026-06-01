from __future__ import annotations

from app.domain.enums import PriceTier
from app.domain.schemas import PricingResult
from app.settings import get_settings
from app.utils.helpers import clamp
from datetime import datetime

from app.utils.time_utils import utc_now


class DynamicPricingEngine:
    def __init__(self) -> None:
        self.settings = get_settings()

    def compute(
        self,
        occupancy_rate: float,
        predicted_occupancy_rate: float,
        generated_at: datetime | None = None,
    ) -> PricingResult:
        now = generated_at or utc_now()
        hour = now.hour
        base = self.settings.base_price_eur
        peak_component = self.settings.peak_surcharge_eur if 7 <= hour <= 9 or 15 <= hour <= 18 else 0.0
        occupancy_component = occupancy_rate * 1.2
        forecast_component = predicted_occupancy_rate * 0.8
        raw_price = base + peak_component + occupancy_component + forecast_component
        final_price = round(clamp(raw_price, self.settings.min_price_eur, self.settings.max_price_eur), 2)

        if final_price < 1.2:
            tier = PriceTier.LOW.value
        elif final_price < 2.1:
            tier = PriceTier.MEDIUM.value
        else:
            tier = PriceTier.HIGH.value

        return PricingResult(
            parking_id=self.settings.parking_id,
            generated_at=now,
            price_eur=final_price,
            price_tier=tier,
            rationale={
                "base_price": base,
                "peak_component": peak_component,
                "occupancy_component": round(occupancy_component, 2),
                "forecast_component": round(forecast_component, 2),
                "current_hour": hour,
                "current_occupancy_rate": round(occupancy_rate, 4),
                "predicted_occupancy_rate": round(predicted_occupancy_rate, 4),
            },
        )
