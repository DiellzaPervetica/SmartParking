from __future__ import annotations

import logging

from confluent_kafka.admin import AdminClient, NewTopic

from app.settings import get_settings

logger = logging.getLogger(__name__)


def create_default_topics() -> None:
    settings = get_settings()
    admin = AdminClient({"bootstrap.servers": settings.kafka_bootstrap_servers})

    topic_defs = [
        NewTopic(settings.kafka_topic_raw, num_partitions=1, replication_factor=1),
        NewTopic(settings.kafka_topic_processed, num_partitions=1, replication_factor=1),
        NewTopic(settings.kafka_topic_ai, num_partitions=1, replication_factor=1),
        NewTopic(settings.kafka_topic_alerts, num_partitions=1, replication_factor=1),
    ]

    existing = set(admin.list_topics(timeout=10).topics.keys())
    to_create = [topic for topic in topic_defs if topic.topic not in existing]

    if not to_create:
        logger.info("Kafka topics already exist")
        return

    futures = admin.create_topics(to_create)
    for topic_name, future in futures.items():
        try:
            future.result()
            logger.info("Created Kafka topic: %s", topic_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Topic may already exist or failed to create (%s): %s", topic_name, exc)
