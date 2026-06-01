from __future__ import annotations

import logging
from typing import Any

from app.ai.anomaly_detection import SensorAnomalyDetector
from app.ai.classification import EventClassifier
from app.ai.dynamic_pricing import DynamicPricingEngine
from app.ai.prediction import OccupancyPredictor
from app.domain.schemas import AlertResult, NormalizedSensorReading, ParkingSummary, SensorWindowMetric
from app.gateway.kafka_producer import KafkaEventProducer
from app.logging_config import configure_logging
from app.services.feature_store_service import FeatureStoreService
from app.services.occupancy_service import OccupancyService
from app.settings import get_settings
from app.storage.repositories import ParkingRepository
from app.utils.time_utils import floor_to_minute, utc_now

logger = logging.getLogger(__name__)


def build_sensor_schema():
    from pyspark.sql.types import BooleanType, DoubleType, IntegerType, StringType, StructField, StructType

    return StructType(
        [
            StructField("event_id", StringType(), nullable=False),
            StructField("parking_id", StringType(), nullable=False),
            StructField("parking_name", StringType(), nullable=False),
            StructField("zone_id", StringType(), nullable=False),
            StructField("spot_id", StringType(), nullable=False),
            StructField("sensor_id", StringType(), nullable=False),
            StructField("gateway_id", StringType(), nullable=False),
            StructField("sequence_no", IntegerType(), nullable=False),
            StructField("timestamp", StringType(), nullable=False),
            StructField("occupied", BooleanType(), nullable=False),
            StructField("distance_cm", DoubleType(), nullable=False),
            StructField("battery_level", DoubleType(), nullable=False),
            StructField("signal_strength", IntegerType(), nullable=False),
            StructField("event_type", StringType(), nullable=False),
            StructField("ingest_ts", StringType(), nullable=True),
        ]
    )


def severity_for_anomaly(anomaly_label: str, score: float) -> str:
    if anomaly_label in {"low_battery", "signal_weak"} or score >= 0.80:
        return "critical"
    if score >= 0.55:
        return "warning"
    return "info"


def create_spark_session():
    from pyspark.sql import SparkSession

    settings = get_settings()
    return (
        SparkSession.builder.appName(settings.spark_app_name)
        .master(settings.spark_master_url)
        .config("spark.jars.packages", settings.spark_kafka_package)
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.streaming.stopGracefullyOnShutdown", "true")
        .config("spark.cassandra.connection.host", ",".join(settings.cassandra_hosts))
        .getOrCreate()
    )


def read_valid_sensor_events(spark):
    from pyspark.sql.functions import col, current_timestamp, from_json, to_timestamp

    settings = get_settings()
    raw_events = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", settings.kafka_bootstrap_servers)
        .option("subscribe", settings.kafka_topic_raw)
        .option("startingOffsets", "latest")
        .load()
    )

    parsed = (
        raw_events.selectExpr("CAST(value AS STRING) AS raw_json")
        .select(from_json(col("raw_json"), build_sensor_schema()).alias("data"), col("raw_json"))
        .select("data.*", "raw_json")
        .withColumn("event_ts", to_timestamp(col("timestamp")))
        .withColumn("spark_ingest_ts", current_timestamp())
    )

    return parsed.where(
        col("parking_id").isNotNull()
        & col("spot_id").isNotNull()
        & col("sensor_id").isNotNull()
        & col("event_ts").isNotNull()
        & col("distance_cm").between(0, 500)
        & col("battery_level").between(0, 100)
        & col("signal_strength").between(-120, 0)
    )


def write_processed_events_to_kafka(events):
    from pyspark.sql.functions import col, struct, to_json

    settings = get_settings()
    checkpoint = settings.spark_checkpoint_dir / "processed-events-topic"
    return (
        events.select(
            col("spot_id").cast("string").alias("key"),
            to_json(
                struct(
                    "event_id",
                    "parking_id",
                    "zone_id",
                    "spot_id",
                    "sensor_id",
                    "gateway_id",
                    "sequence_no",
                    "timestamp",
                    "occupied",
                    "distance_cm",
                    "battery_level",
                    "signal_strength",
                    "event_type",
                    "spark_ingest_ts",
                )
            ).alias("value"),
        )
        .writeStream.format("kafka")
        .option("kafka.bootstrap.servers", settings.kafka_bootstrap_servers)
        .option("topic", settings.kafka_topic_processed)
        .option("checkpointLocation", str(checkpoint))
        .outputMode("append")
        .start()
    )


def write_sensor_batch_to_cassandra(batch_df, batch_id: int) -> None:
    rows = [row.asDict(recursive=True) for row in batch_df.collect()]
    if not rows:
        return

    settings = get_settings()
    repository = ParkingRepository()
    occupancy_service = OccupancyService()
    predictor = OccupancyPredictor()
    anomaly_detector = SensorAnomalyDetector()
    classifier = EventClassifier()
    pricing_engine = DynamicPricingEngine()
    alert_producer = KafkaEventProducer()

    try:
        for row in rows:
            reading = _reading_from_spark_row(row)
            anomaly_result = anomaly_detector.detect(reading)
            classification_result = classifier.classify(reading, anomaly_result)

            repository.upsert_sensor_metadata(reading)
            repository.insert_sensor_event(
                reading,
                classification_label=classification_result.label,
                anomaly_label=anomaly_result.anomaly_label,
                anomaly_score=anomaly_result.anomaly_score,
            )
            repository.upsert_current_status(
                reading,
                classification_label=classification_result.label,
                anomaly_label=anomaly_result.anomaly_label,
                anomaly_score=anomaly_result.anomaly_score,
            )

            current_rows = repository.get_current_spot_status(settings.parking_id)
            summary = occupancy_service.build_summary(settings.parking_id, current_rows)
            recent_events = repository.get_recent_events_for_spot(settings.parking_id, reading.spot_id, limit=10)
            feature_row = FeatureStoreService.build_feature_row(
                reading=reading,
                current_occupancy_rate=summary.occupancy_rate,
                recent_events=recent_events,
            )
            prediction_result = predictor.predict(settings.parking_id, feature_row)
            pricing_result = pricing_engine.compute(
                occupancy_rate=summary.occupancy_rate,
                predicted_occupancy_rate=prediction_result.predicted_occupancy_rate,
            )

            repository.update_spot_ai_status(
                parking_id=settings.parking_id,
                spot_id=reading.spot_id,
                classification_label=classification_result.label,
                anomaly_label=anomaly_result.anomaly_label,
                anomaly_score=anomaly_result.anomaly_score,
            )
            repository.insert_ai_result(
                ai_type="prediction",
                entity_id=settings.parking_id,
                label=prediction_result.model_name,
                score=prediction_result.predicted_occupancy_rate,
                payload=prediction_result.model_dump(mode="json"),
                parking_id=settings.parking_id,
            )
            repository.insert_ai_result(
                ai_type="anomaly",
                entity_id=reading.spot_id,
                label=anomaly_result.anomaly_label,
                score=anomaly_result.anomaly_score,
                payload=anomaly_result.model_dump(mode="json"),
                parking_id=settings.parking_id,
            )
            repository.insert_ai_result(
                ai_type="classification",
                entity_id=reading.spot_id,
                label=classification_result.label,
                score=classification_result.confidence,
                payload=classification_result.model_dump(mode="json"),
                parking_id=settings.parking_id,
            )
            repository.insert_ai_result(
                ai_type="pricing",
                entity_id=settings.parking_id,
                label=pricing_result.price_tier,
                score=pricing_result.price_eur,
                payload=pricing_result.model_dump(mode="json"),
                parking_id=settings.parking_id,
            )
            repository.insert_parking_summary(
                ParkingSummary(
                    parking_id=summary.parking_id,
                    generated_at=floor_to_minute(utc_now()),
                    occupied_spots=summary.occupied_spots,
                    free_spots=summary.free_spots,
                    occupancy_rate=summary.occupancy_rate,
                    predicted_occupancy_rate=prediction_result.predicted_occupancy_rate,
                    price_eur=pricing_result.price_eur,
                    price_tier=pricing_result.price_tier,
                )
            )

            if anomaly_result.anomaly_label != "normal":
                alert = AlertResult(
                    parking_id=reading.parking_id,
                    generated_at=utc_now(),
                    entity_id=reading.spot_id,
                    alert_type=anomaly_result.anomaly_label,
                    severity=severity_for_anomaly(anomaly_result.anomaly_label, anomaly_result.anomaly_score),
                    message="; ".join(anomaly_result.reasons),
                    score=anomaly_result.anomaly_score,
                )
                repository.insert_alert(alert)
                alert_producer.send_alert(alert.model_dump(mode="json"))

        alert_producer.flush()
        logger.info("Spark batch %s processed %s events into Cassandra", batch_id, len(rows))
    finally:
        repository.close()


def write_window_metrics_to_cassandra(batch_df, batch_id: int) -> None:
    rows = [row.asDict(recursive=True) for row in batch_df.collect()]
    if not rows:
        return

    repository = ParkingRepository()
    try:
        for row in rows:
            window = row["window"]
            repository.insert_window_metric(
                SensorWindowMetric(
                    parking_id=row["parking_id"],
                    window_start=window["start"],
                    window_end=window["end"],
                    event_count=int(row["event_count"] or 0),
                    occupied_event_count=int(row["occupied_event_count"] or 0),
                    avg_distance_cm=round(float(row["avg_distance_cm"] or 0.0), 2),
                    avg_battery_level=round(float(row["avg_battery_level"] or 0.0), 2),
                    weak_signal_count=int(row["weak_signal_count"] or 0),
                )
            )
        logger.info("Spark batch %s stored %s window metrics", batch_id, len(rows))
    finally:
        repository.close()


def start_streaming() -> None:
    from pyspark.sql.functions import avg, col, count, sum as spark_sum, when, window

    settings = get_settings()
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    events = read_valid_sensor_events(spark)
    storage_checkpoint = settings.spark_checkpoint_dir / "cassandra-sensor-events"
    metrics_checkpoint = settings.spark_checkpoint_dir / "cassandra-window-metrics"

    storage_query = (
        events.writeStream.foreachBatch(write_sensor_batch_to_cassandra)
        .option("checkpointLocation", str(storage_checkpoint))
        .trigger(processingTime=f"{settings.spark_trigger_seconds} seconds")
        .outputMode("append")
        .start()
    )

    window_metrics = (
        events.withWatermark("event_ts", "2 minutes")
        .groupBy(window(col("event_ts"), "1 minute"), col("parking_id"))
        .agg(
            count("*").alias("event_count"),
            spark_sum(when(col("occupied"), 1).otherwise(0)).alias("occupied_event_count"),
            avg("distance_cm").alias("avg_distance_cm"),
            avg("battery_level").alias("avg_battery_level"),
            spark_sum(when(col("signal_strength") < -85, 1).otherwise(0)).alias("weak_signal_count"),
        )
    )
    metrics_query = (
        window_metrics.writeStream.foreachBatch(write_window_metrics_to_cassandra)
        .option("checkpointLocation", str(metrics_checkpoint))
        .trigger(processingTime=f"{settings.spark_trigger_seconds} seconds")
        .outputMode("update")
        .start()
    )
    processed_topic_query = write_processed_events_to_kafka(events)

    logger.info(
        "Spark Streaming started | kafka=%s raw_topic=%s cassandra_keyspace=%s",
        settings.kafka_bootstrap_servers,
        settings.kafka_topic_raw,
        settings.cassandra_keyspace,
    )
    spark.streams.awaitAnyTermination()

    storage_query.stop()
    metrics_query.stop()
    processed_topic_query.stop()


def _reading_from_spark_row(row: dict[str, Any]) -> NormalizedSensorReading:
    ingest_ts = row.get("spark_ingest_ts") or utc_now()
    return NormalizedSensorReading(
        event_id=row["event_id"],
        parking_id=row["parking_id"],
        parking_name=row["parking_name"],
        zone_id=row["zone_id"],
        spot_id=row["spot_id"],
        sensor_id=row["sensor_id"],
        gateway_id=row["gateway_id"],
        sequence_no=int(row["sequence_no"]),
        timestamp=row["timestamp"],
        occupied=bool(row["occupied"]),
        distance_cm=float(row["distance_cm"]),
        battery_level=float(row["battery_level"]),
        signal_strength=int(row["signal_strength"]),
        event_type=row["event_type"],
        ingest_ts=ingest_ts,
    )


def main() -> None:
    configure_logging()
    start_streaming()


if __name__ == "__main__":
    main()
