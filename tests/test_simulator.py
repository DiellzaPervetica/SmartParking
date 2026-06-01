from app.simulator.ultrasonic_sensor_simulator import UltrasonicSensorSimulator


def test_ultrasonic_simulator_ranges():
    sensor = UltrasonicSensorSimulator(seed=1)
    occupied_distance = sensor.simulate_distance_cm(True)
    free_distance = sensor.simulate_distance_cm(False)

    assert 5 <= occupied_distance <= 40
    assert 50 <= free_distance <= 260
