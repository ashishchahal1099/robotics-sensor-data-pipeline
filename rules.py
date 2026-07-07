"""
rules.py
--------
Each rule is a small class with one job: look at a reading (and maybe the
previous reading from that robot) and decide if it's an anomaly.

Every rule has the SAME shape:
    check(reading, previous_reading) -> (is_flagged: bool, reason: str or None)

Because they all share that shape, the pipeline can loop over a LIST of rules
without caring which rule is which. That's what makes them "pluggable" --
add a new rule class, drop it in the list in pipeline.py, done.
"""

# ---- Thresholds (tunable constants) ----
CRASH_ACCEL_MAGNITUDE_G = 6.0       # total acceleration above this = possible crash/impact
AXIS_SPIKE_G = 4.0                  # single axis reading above this, others normal = spike
THERMAL_MIN_C = -10.0
THERMAL_MAX_C = 70.0
GEOFENCE_LAT_RANGE = (12.90, 12.99)   # allowed latitude window
GEOFENCE_LON_RANGE = (77.55, 77.64)   # allowed longitude window


class CrashDetectionRule:
    """Flags a reading if the combined 3-axis acceleration magnitude spikes
    far above normal walking/driving vibration -- suggesting an impact."""
    name = "crash_detection"

    def check(self, reading, previous_reading):
        magnitude = (reading["accel_x"] ** 2 + reading["accel_y"] ** 2 + reading["accel_z"] ** 2) ** 0.5
        if magnitude > CRASH_ACCEL_MAGNITUDE_G:
            return True, f"{self.name}: |accel|={magnitude:.2f}g exceeds {CRASH_ACCEL_MAGNITUDE_G}g"
        return False, None


class AxisSpikeRule:
    """Flags a reading if ONE axis is way out of line while the others look
    normal -- this pattern often means a loose sensor or wiring glitch rather
    than a real crash (which usually shows up on all 3 axes)."""
    name = "axis_spike"

    def check(self, reading, previous_reading):
        axes = [reading["accel_x"], reading["accel_y"], reading["accel_z"]]
        for i, value in enumerate(axes):
            others = axes[:i] + axes[i + 1:]
            if abs(value) > AXIS_SPIKE_G and all(abs(o) < AXIS_SPIKE_G / 2 for o in others):
                axis_name = ["x", "y", "z"][i]
                return True, f"{self.name}: axis {axis_name}={value:.2f}g isolated spike"
        return False, None


class ThermalFaultRule:
    """Flags a reading if temperature is outside the safe operating range."""
    name = "thermal_fault"

    def check(self, reading, previous_reading):
        temp = reading["temperature"]
        if temp < THERMAL_MIN_C or temp > THERMAL_MAX_C:
            return True, f"{self.name}: temp={temp:.1f}C outside [{THERMAL_MIN_C},{THERMAL_MAX_C}]"
        return False, None


class GPSGeofenceRule:
    """Flags a reading if the robot's GPS position falls outside the
    permitted operating zone (a rectangle here, for simplicity)."""
    name = "gps_geofence"

    def check(self, reading, previous_reading):
        lat, lon = reading["gps_lat"], reading["gps_lon"]
        lat_ok = GEOFENCE_LAT_RANGE[0] <= lat <= GEOFENCE_LAT_RANGE[1]
        lon_ok = GEOFENCE_LON_RANGE[0] <= lon <= GEOFENCE_LON_RANGE[1]
        if not (lat_ok and lon_ok):
            return True, f"{self.name}: position ({lat:.4f},{lon:.4f}) outside geofence"
        return False, None


# The pipeline imports just this list -- adding rule #5 means writing a class
# above and adding one line here. Nothing else in the codebase changes.
ALL_RULES = [
    CrashDetectionRule(),
    AxisSpikeRule(),
    ThermalFaultRule(),
    GPSGeofenceRule(),
]


def run_all_rules(reading, previous_reading=None):
    """Run every rule against one reading. Returns (flagged: bool, reasons: list[str])."""
    reasons = []
    for rule in ALL_RULES:
        flagged, reason = rule.check(reading, previous_reading)
        if flagged:
            reasons.append(reason)
    return (len(reasons) > 0), reasons
