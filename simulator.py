"""
simulator.py
------------
Stands in for real robot hardware. Generates a stream of sensor readings for
3 robots over 15 seconds at 0.5s intervals (31 timestamps x 3 robots = 93
readings total), with some anomalies deliberately injected so the quality
rules have real problems to catch.

In a real deployment, this file would be replaced by actual sensor drivers
(e.g. reading an I2C accelerometer or a GPS module) -- everything else in
the pipeline stays the same, because they all just produce a `reading` dict
with the same keys.
"""

import random

ROBOT_IDS = ["robot_1", "robot_2", "robot_3"]
DURATION_SECONDS = 15
INTERVAL_SECONDS = 0.5

# Roughly-safe "home base" GPS point per robot, small random drift around it
BASE_GPS = {
    "robot_1": (12.94, 77.60),
    "robot_2": (12.95, 77.59),
    "robot_3": (12.93, 77.61),
}


def generate_readings(seed: int = 3):
    """Returns a list of reading dicts, in the order they'd stream in live."""
    random.seed(seed)
    readings = []
    n_steps = int(DURATION_SECONDS / INTERVAL_SECONDS) + 1  # 31

    for step in range(n_steps):
        timestamp = round(step * INTERVAL_SECONDS, 2)
        for robot_id in ROBOT_IDS:
            base_lat, base_lon = BASE_GPS[robot_id]

            # --- normal baseline sensor noise ---
            accel_x = random.gauss(0, 0.6)
            accel_y = random.gauss(0, 0.6)
            accel_z = random.gauss(1.0, 0.6)  # ~1g resting due to gravity
            gps_lat = base_lat + random.gauss(0, 0.003)
            gps_lon = base_lon + random.gauss(0, 0.003)
            temperature = random.gauss(35, 4)

            # --- randomly inject one of 4 anomaly types (~22% chance) ---
            roll = random.random()
            if roll < 0.06:
                # crash: all axes spike together
                accel_x += random.uniform(5, 8)
                accel_y += random.uniform(5, 8)
                accel_z += random.uniform(5, 8)
            elif roll < 0.12:
                # axis spike: only one axis goes wild
                accel_x += random.uniform(4, 7)
            elif roll < 0.17:
                # thermal fault: force a hard override so it reliably crosses
                # the safe range regardless of the baseline noise
                temperature = random.uniform(78, 95) if random.random() < 0.5 else random.uniform(-30, -18)
            elif roll < 0.225:
                # GPS geofence breach
                gps_lat += random.uniform(0.05, 0.1)
                gps_lon += random.uniform(0.05, 0.1)

            readings.append({
                "robot_id": robot_id,
                "timestamp": timestamp,
                "accel_x": round(accel_x, 3),
                "accel_y": round(accel_y, 3),
                "accel_z": round(accel_z, 3),
                "gps_lat": round(gps_lat, 5),
                "gps_lon": round(gps_lon, 5),
                "temperature": round(temperature, 2),
            })

    return readings
