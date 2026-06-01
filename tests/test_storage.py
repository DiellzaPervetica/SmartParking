from app.services.occupancy_service import OccupancyService


def test_occupancy_summary_build():
    rows = [
        {"occupied": True},
        {"occupied": False},
        {"occupied": True},
    ]
    summary = OccupancyService.build_summary("parking_1", rows)
    assert summary.occupied_spots == 2
    assert summary.free_spots == 1
    assert round(summary.occupancy_rate, 2) == 0.67
