from app.gateway.validator import validate_sensor_payload


def test_validate_sensor_payload_success():
    payload = {
        "event_id": "1",
        "parking_id": "prishtina_center_01",
        "parking_name": "Qendra Parking Prishtine",
        "zone_id": "A",
        "spot_id": "P01",
        "sensor_id": "ultra-p01",
        "gateway_id": "gateway-prishtina-01",
        "sequence_no": 1,
        "timestamp": "2026-04-03T12:00:00+00:00",
        "occupied": True,
        "distance_cm": 21.0,
        "battery_level": 92.0,
        "signal_strength": -60,
        "event_type": "state_change",
    }

    ok, validated, error = validate_sensor_payload(payload)
    assert ok is True
    assert validated is not None
    assert error is None
