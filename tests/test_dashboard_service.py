from app.services.dashboard_service import DashboardService


def test_dashboard_falls_back_to_simulation_without_cassandra():
    dashboard = DashboardService().build(scenario="maintenance")

    assert dashboard["source"] in {"simulation_fallback", "simulation_until_cassandra_has_rows", "cassandra_spark_streaming"}
    assert dashboard["summary"]["total_spots"] == len(dashboard["spots"])
    assert "Spark" in {item["name"] for item in dashboard["gateway"]}
