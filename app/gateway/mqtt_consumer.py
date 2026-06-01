from __future__ import annotations

import json
import logging

import paho.mqtt.client as mqtt

from app.gateway.kafka_producer import KafkaEventProducer
from app.gateway.normalizer import normalize_payload
from app.gateway.status_monitor import StatusMonitor
from app.gateway.validator import validate_sensor_payload
from app.logging_config import configure_logging
from app.mqtt_layer.mqtt_topics import wildcard_topic
from app.settings import get_settings
from app.utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class MqttGatewayConsumer:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.monitor = StatusMonitor()
        self.kafka = KafkaEventProducer()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client: mqtt.Client, userdata, flags, reason_code, properties) -> None:
        topic = wildcard_topic()
        client.subscribe(topic, qos=1)
        logger.info("Gateway subscribed to MQTT topic: %s", topic)

    def on_message(self, client: mqtt.Client, userdata, message: mqtt.MQTTMessage) -> None:
        try:
            raw_data = json.loads(message.payload.decode("utf-8"))
            is_valid, payload, error = validate_sensor_payload(raw_data)
            if not is_valid or payload is None:
                logger.error("Invalid sensor payload: %s", error)
                self.kafka.send_alert(
                    {
                        "timestamp": utc_now().isoformat(),
                        "sensor_id": raw_data.get("sensor_id", "unknown"),
                        "alert_type": "validation_error",
                        "message": error,
                        "raw_payload": raw_data,
                    }
                )
                return

            normalized = normalize_payload(payload)
            anomalies = self.monitor.process(normalized)

            normalized_dict = normalized.model_dump(mode="json")
            self.kafka.send_reading(normalized_dict)

            for anomaly in anomalies:
                self.kafka.send_alert(
                    {
                        "timestamp": utc_now().isoformat(),
                        "sensor_id": normalized.sensor_id,
                        "spot_id": normalized.spot_id,
                        "alert_type": anomaly.label,
                        "score": anomaly.score,
                        "message": anomaly.message,
                    }
                )

            logger.info(
                "Gateway forwarded sensor event to Kafka | spot=%s sensor=%s occupied=%s",
                normalized.spot_id,
                normalized.sensor_id,
                normalized.occupied,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to process MQTT message: %s", exc)

    def run(self) -> None:
        self.client.connect(self.settings.mqtt_host, self.settings.mqtt_port, self.settings.mqtt_keepalive)
        logger.info("Gateway connected to MQTT broker at %s:%s", self.settings.mqtt_host, self.settings.mqtt_port)
        self.client.loop_forever()


def main() -> None:
    configure_logging()
    consumer = MqttGatewayConsumer()
    consumer.run()


if __name__ == "__main__":
    main()
