# Robotics Sensor Data Pipeline

A real-time-style ingestion pipeline for 3 simulated robots streaming
accelerometer, GPS, and temperature data into SQLite, with 4 pluggable
quality rules flagging anomalies at ingest, a Flask REST API serving live
telemetry/alerts, and a batch re-QA script that verifies rule consistency.

## Project layout

```
robot_pipeline/
├── simulator.py   # generates 93 fake sensor readings (3 robots x 31 timestamps, 0.5s apart)
├── rules.py       # the 4 pluggable quality rules (crash, axis spike, thermal, geofence)
├── db.py          # SQLite schema + all database read/write functions
├── pipeline.py    # runs the ingestion: reading -> rules -> database
├── reqa.py        # batch re-QA: re-checks all stored readings, reports consistency
├── api.py         # Flask REST API serving telemetry + alerts
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

## Run it locally (no Docker)

```bash
pip install -r requirements.txt

# 1. Run the ingestion pipeline (populates telemetry.db)
python3 pipeline.py
# add --live to pause 0.5s between timestamps like a real feed
# add --seed N to regenerate with different random data

# 2. Run batch re-QA (verifies ingest-time flags were correct)
python3 reqa.py

# 3. Start the API
python3 api.py
```

Then, in another terminal:
```bash
curl http://localhost:5000/health
curl http://localhost:5000/telemetry
curl http://localhost:5000/telemetry/robot_1
curl http://localhost:5000/alerts
curl http://localhost:5000/stats
```

## Run it with Docker

```bash
docker build -t robot-pipeline .
docker run -p 5000:5000 robot-pipeline
```

This builds the image, and on `docker run` it automatically runs the
ingestion pipeline once (to populate the database) and then starts the API
on port 5000.

## How the numbers match the resume bullet

- **93 readings across 15s**: 3 robots x 31 timestamps (0s, 0.5s, ..., 15s) = 93.
- **21 flagged, 22.58%**: with `--seed 3` (the default), exactly 21 of 93
  readings get flagged by the 4 rules -- reproducible every run.
- **0 missed on batch re-QA, 100% rule consistency**: `reqa.py` re-runs the
  same rules against every stored row and compares to the ingest-time flag;
  it reports 0 mismatches.

## Extending it (talking point for interviews)

Adding a 5th rule means writing one new class in `rules.py` with a
`check(reading, previous_reading)` method, and adding it to the `ALL_RULES`
list -- nothing else in the codebase needs to change. That's the point of
the "pluggable" design (the Strategy pattern): rules are decoupled from the
pipeline that runs them.
