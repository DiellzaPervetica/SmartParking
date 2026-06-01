This project uses Cassandra as the primary IoT event store.

Tables:
- sensor_events_by_spot: append-only historical event stream
- current_spot_status: latest status per parking spot
- parking_summary_by_minute: aggregate parking occupancy summary
- ai_results_by_time: prediction, anomaly, classification and pricing outputs
