from app.ai.dynamic_pricing import DynamicPricingEngine


def test_dynamic_pricing_bounds():
    engine = DynamicPricingEngine()
    result = engine.compute(occupancy_rate=0.95, predicted_occupancy_rate=0.98)
    assert result.price_eur >= 0.5
    assert result.price_eur <= 3.0
    assert result.price_tier in {"low", "medium", "high"}
