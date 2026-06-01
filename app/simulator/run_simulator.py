from __future__ import annotations

import logging
import random
import time

from app.domain.enums import EventType
from app.logging_config import configure_logging
from app.mqtt_layer.mqtt_publisher import MqttPublisher
from app.mqtt_layer.mqtt_topics import sensor_topic
from app.mqtt_layer.payload_builder import build_sensor_payload
from app.settings import get_settings
from app.simulator.parking_layout import build_default_parking_layout
from app.simulator.ultrasonic_sensor_simulator import UltrasonicSensorSimulator
from app.simulator.vehicle_flow_simulator import VehicleFlowSimulator
from app.utils.time_utils import utc_now

logger = logging.getLogger(__name__)


def run() -> None:
    configure_logging()
    settings = get_settings()
    randomizer = random.Random(2026)
    flow = VehicleFlowSimulator(seed=2026)
    sensor = UltrasonicSensorSimulator(seed=2027)
    publisher = MqttPublisher()
    spots = build_default_parking_layout()

    logger.info("Starting simulator for parking=%s with %s spots", settings.parking_id, len(spots))

    try:
        publisher.connect()

        while True:
            now = utc_now()

            for spot in spots:
                previous_occupied = spot.occupied

                if not spot.occupied and flow.should_arrive(now):
                    spot.occupied = True
                elif spot.occupied and flow.should_depart(now):
                    spot.occupied = False
                elif randomizer.random() < 0.01:
                    # small random disturbance
                    spot.occupied = not spot.occupied

                should_send_heartbeat = (
                    spot.last_heartbeat_at is None
                    or (now - spot.last_heartbeat_at).total_seconds() >= settings.heartbeat_seconds
                )

                state_changed = previous_occupied != spot.occupied

                if not state_changed and not should_send_heartbeat:
                    continue

                distance = sensor.simulate_distance_cm(spot.occupied)
                battery = sensor.simulate_battery_level()
                signal = sensor.simulate_signal_strength()
                event_type = EventType.STATE_CHANGE if state_changed else EventType.HEARTBEAT
                payload = build_sensor_payload(
                    spot=spot,
                    occupied=spot.occupied,
                    distance_cm=distance,
                    battery_level=battery,
                    signal_strength=signal,
                    event_type=event_type,
                    timestamp=now,
                )
                publisher.publish_json(sensor_topic(spot.spot_id), payload)
                spot.last_sent_at = now
                if event_type == EventType.HEARTBEAT:
                    spot.last_heartbeat_at = now
                elif state_changed:
                    spot.last_heartbeat_at = now

                logger.info(
                    "Simulator event | spot=%s occupied=%s distance_cm=%s event_type=%s",
                    spot.spot_id,
                    spot.occupied,
                    distance,
                    event_type.value,
                )

            time.sleep(settings.simulation_step_seconds)

    except KeyboardInterrupt:
        logger.info("Simulator stopped by user")
    finally:
        publisher.close()


if __name__ == "__main__":
    run()
