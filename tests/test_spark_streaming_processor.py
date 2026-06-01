from app.streaming.spark_streaming_processor import severity_for_anomaly


def test_severity_for_anomaly_prioritizes_operational_faults():
    assert severity_for_anomaly("low_battery", 0.40) == "critical"
    assert severity_for_anomaly("distance_outlier", 0.70) == "warning"
    assert severity_for_anomaly("normal", 0.05) == "info"
