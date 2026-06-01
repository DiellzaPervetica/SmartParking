from __future__ import annotations

import json
import logging
from typing import Any

import paho.mqtt.client as mqtt

from app.settings import get_settings

logger = logging.getLogger(__name__)


class MqttPublisher:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.host = settings.mqtt_host
        self.port = settings.mqtt_port
        self.keepalive = settings.mqtt_keepalive
        self.connected = False

    def connect(self) -> None:
        if self.connected:
            return
        self.client.connect(self.host, self.port, self.keepalive)
        self.client.loop_start()
        self.connected = True
        logger.info("Connected to MQTT broker at %s:%s", self.host, self.port)

    def publish_json(self, topic: str, payload: dict[str, Any]) -> None:
        if not self.connected:
            self.connect()
        message = json.dumps(payload, ensure_ascii=False)
        result = self.client.publish(topic, message, qos=1)
        result.wait_for_publish()
        logger.debug("Published to MQTT topic %s", topic)

    def close(self) -> None:
        if not self.connected:
            return
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
