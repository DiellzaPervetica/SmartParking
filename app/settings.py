from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Smart Parking Prishtina")
    environment: str = os.getenv("ENVIRONMENT", "development")

    parking_id: str = os.getenv("PARKING_ID", "prishtina_center_01")
    parking_name: str = os.getenv("PARKING_NAME", "Qendra Parking Prishtine")
    total_spots: int = int(os.getenv("TOTAL_SPOTS", "20"))

    mqtt_host: str = os.getenv("MQTT_HOST", "localhost")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_keepalive: int = int(os.getenv("MQTT_KEEPALIVE", "60"))
    mqtt_topic_root: str = os.getenv("MQTT_TOPIC_ROOT", "parking/prishtina/prishtina_center_01")

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic_raw: str = os.getenv("KAFKA_TOPIC_RAW", "parking.raw-events")
    kafka_topic_processed: str = os.getenv("KAFKA_TOPIC_PROCESSED", "parking.processed-events")
    kafka_topic_ai: str = os.getenv("KAFKA_TOPIC_AI", "parking.ai-input")
    kafka_topic_alerts: str = os.getenv("KAFKA_TOPIC_ALERTS", "parking.sensor-alerts")

    spark_app_name: str = os.getenv("SPARK_APP_NAME", "SmartParkingSparkStreaming")
    spark_master_url: str = os.getenv("SPARK_MASTER_URL", "local[*]")
    spark_checkpoint_dir: Path = BASE_DIR / os.getenv("SPARK_CHECKPOINT_DIR", "data/checkpoints/spark")
    spark_trigger_seconds: int = int(os.getenv("SPARK_TRIGGER_SECONDS", "10"))
    spark_kafka_package: str = os.getenv(
        "SPARK_KAFKA_PACKAGE",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1",
    )

    cassandra_hosts: list[str] = tuple(
        host.strip() for host in os.getenv("CASSANDRA_HOSTS", "localhost").split(",") if host.strip()
    )
    cassandra_port: int = int(os.getenv("CASSANDRA_PORT", "9042"))
    cassandra_keyspace: str = os.getenv("CASSANDRA_KEYSPACE", "smart_parking")
    cassandra_datacenter: str = os.getenv("CASSANDRA_DATACENTER", "datacenter1")

    simulation_step_seconds: int = int(os.getenv("SIMULATION_STEP_SECONDS", "5"))
    heartbeat_seconds: int = int(os.getenv("HEARTBEAT_SECONDS", "30"))

    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    base_price_eur: float = float(os.getenv("BASE_PRICE_EUR", "1.0"))
    peak_surcharge_eur: float = float(os.getenv("PEAK_SURCHARGE_EUR", "0.4"))
    max_price_eur: float = float(os.getenv("MAX_PRICE_EUR", "3.0"))
    min_price_eur: float = float(os.getenv("MIN_PRICE_EUR", "0.5"))

    models_dir: Path = BASE_DIR / "app" / "ai" / "models"
    data_dir: Path = BASE_DIR / "data"
    exports_dir: Path = BASE_DIR / "data" / "exports"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    settings.exports_dir.mkdir(parents=True, exist_ok=True)
    settings.spark_checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return settings
