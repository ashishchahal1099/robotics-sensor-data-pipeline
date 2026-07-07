"""
pipeline.py
-----------
The real-time ingestion pipeline. This is the file you run to simulate
the whole 15-second data collection session.

Flow:
  1. Ask the simulator for the full stream of 93 readings (in time order).
  2. For each reading, as it "arrives":
       a. Run it through all 4 quality rules immediately (at ingest).
       b. Write the reading + its flag result into SQLite.
  3. (Optional) sleep 0.5s between timestamps so it behaves like a live feed
     instead of writing all 93 rows instantly.

This "check-then-store" order is what makes it a real-time QA pipeline
rather than just a bulk data dump.
"""

import time
import argparse

import db
import rules
from simulator import generate_readings, INTERVAL_SECONDS


def run_pipeline(live: bool = False, seed: int = 3):
    db.init_db()
    db.reset_db()  # start clean each run so numbers are reproducible

    readings = generate_readings(seed=seed)

    # keep track of each robot's last reading, in case a rule ever wants
    # to compare against the previous value (not used by our 4 rules yet,
    # but the hook is there -- this is what "pluggable" buys you later)
    last_reading_per_robot = {}

    flagged_count = 0
    last_timestamp = None

    for reading in readings:
        # simulate real-time arrival: pause when we reach a new timestamp
        if live and last_timestamp is not None and reading["timestamp"] != last_timestamp:
            time.sleep(INTERVAL_SECONDS)
        last_timestamp = reading["timestamp"]

        previous = last_reading_per_robot.get(reading["robot_id"])
        flagged, reasons = rules.run_all_rules(reading, previous)

        db.insert_reading(reading, flagged, reasons)
        last_reading_per_robot[reading["robot_id"]] = reading

        if flagged:
            flagged_count += 1
            print(f"[FLAGGED] t={reading['timestamp']}s {reading['robot_id']} -> {reasons}")

    total = len(readings)
    rate = (flagged_count / total) * 100
    print(f"\nIngest complete: {total} readings, {flagged_count} flagged ({rate:.2f}% flag rate)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the robot telemetry ingestion pipeline.")
    parser.add_argument("--live", action="store_true", help="Pause 0.5s between timestamps to mimic real-time streaming.")
    parser.add_argument("--seed", type=int, default=3, help="Random seed for the simulator.")
    args = parser.parse_args()

    run_pipeline(live=args.live, seed=args.seed)
