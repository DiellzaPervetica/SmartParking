CREATE KEYSPACE IF NOT EXISTS smart_parking
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE smart_parking;

CREATE TABLE IF NOT EXISTS sensor_metadata_by_id (
    parking_id text,
    sensor_id text,
    spot_id text,
    zone_id text,
    gateway_id text,
    sensor_type text,
    unit text,
    installed_at timestamp,
    firmware_version text,
    status text,
    PRIMARY KEY ((parking_id), sensor_id)
);

CREATE TABLE IF NOT EXISTS sensor_events_by_spot (
    parking_id text,
    spot_id text,
    event_ts timestamp,
    event_id uuid,
    zone_id text,
    gateway_id text,
    sensor_id text,
    occupied boolean,
    distance_cm double,
    battery_level double,
    signal_strength int,
    event_type text,
    classification_label text,
    anomaly_label text,
    anomaly_score double,
    raw_json text,
    PRIMARY KEY ((parking_id, spot_id), event_ts, event_id)
) WITH CLUSTERING ORDER BY (event_ts DESC, event_id ASC);

CREATE TABLE IF NOT EXISTS current_spot_status (
    parking_id text,
    spot_id text,
    zone_id text,
    last_update timestamp,
    sensor_id text,
    gateway_id text,
    occupied boolean,
    distance_cm double,
    battery_level double,
    signal_strength int,
    event_type text,
    classification_label text,
    anomaly_label text,
    anomaly_score double,
    last_sequence_no int,
    PRIMARY KEY ((parking_id), spot_id)
);

CREATE TABLE IF NOT EXISTS parking_summary_by_minute (
    parking_id text,
    bucket_date date,
    minute_ts timestamp,
    occupied_spots int,
    free_spots int,
    occupancy_rate double,
    predicted_occupancy_rate double,
    price_eur double,
    price_tier text,
    PRIMARY KEY ((parking_id, bucket_date), minute_ts)
) WITH CLUSTERING ORDER BY (minute_ts DESC);

CREATE TABLE IF NOT EXISTS sensor_window_metrics_by_minute (
    parking_id text,
    bucket_date date,
    window_start timestamp,
    window_end timestamp,
    event_count int,
    occupied_event_count int,
    avg_distance_cm double,
    avg_battery_level double,
    weak_signal_count int,
    PRIMARY KEY ((parking_id, bucket_date), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS ai_results_by_time (
    parking_id text,
    ai_type text,
    bucket_date date,
    generated_at timestamp,
    entity_id text,
    label text,
    score double,
    json_payload text,
    PRIMARY KEY ((parking_id, ai_type, bucket_date), generated_at, entity_id)
) WITH CLUSTERING ORDER BY (generated_at DESC, entity_id ASC);

CREATE TABLE IF NOT EXISTS alerts_by_time (
    parking_id text,
    bucket_date date,
    generated_at timestamp,
    entity_id text,
    alert_type text,
    severity text,
    message text,
    score double,
    PRIMARY KEY ((parking_id, bucket_date), generated_at, entity_id)
) WITH CLUSTERING ORDER BY (generated_at DESC, entity_id ASC);
