from app.services.simulation_snapshot_service import SimulationSnapshotService


def test_simulation_snapshot_has_dashboard_shape():
    snapshot = SimulationSnapshotService().generate(scenario="morning_peak")

    assert snapshot["source"] == "lightweight_simulation"
    assert snapshot["summary"]["total_spots"] == len(snapshot["spots"])
    assert snapshot["summary"]["occupied_spots"] + snapshot["summary"]["free_spots"] == len(snapshot["spots"])
    assert snapshot["summary"]["price_eur"] >= 0.5
    assert snapshot["digital_signs"]
    assert {zone["zone_id"] for zone in snapshot["zones"]} == {"A", "B"}


def test_maintenance_snapshot_surfaces_sensor_warnings():
    snapshot = SimulationSnapshotService().generate(scenario="maintenance")

    assert snapshot["health"]["low_battery_spots"] >= 1
    assert snapshot["health"]["weak_signal_spots"] >= 1
    assert len(snapshot["ai"]["anomalies"]) >= 1
