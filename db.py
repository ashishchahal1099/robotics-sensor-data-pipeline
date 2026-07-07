"""
db.py
-----
Everything related to talking to the SQLite database lives here.
Other files never write raw SQL themselves -- they call functions in this file.
This keeps the database logic in ONE place, which makes the project much
easier to debug and explain in an interview.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "telemetry.db"


def get_connection():
    """Open a connection to the database file (creates the file if missing)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["temperature"]
    return conn


def init_db():
    """Create the readings table if it doesn't already exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            robot_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            accel_x REAL NOT NULL,
            accel_y REAL NOT NULL,
            accel_z REAL NOT NULL,
            gps_lat REAL NOT NULL,
            gps_lon REAL NOT NULL,
            temperature REAL NOT NULL,
            flagged INTEGER NOT NULL DEFAULT 0,
            flag_reasons TEXT NOT NULL DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()


def insert_reading(reading: dict, flagged: bool, flag_reasons: list):
    """Insert one sensor reading row, along with its QA result."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO readings
            (robot_id, timestamp, accel_x, accel_y, accel_z,
             gps_lat, gps_lon, temperature, flagged, flag_reasons)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        reading["robot_id"], reading["timestamp"],
        reading["accel_x"], reading["accel_y"], reading["accel_z"],
        reading["gps_lat"], reading["gps_lon"], reading["temperature"],
        int(flagged), ",".join(flag_reasons)
    ))
    conn.commit()
    conn.close()


def get_all_readings():
    """Return every row in the table, oldest first."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM readings ORDER BY timestamp ASC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_flagged_readings():
    """Return only rows that were flagged as anomalies."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM readings WHERE flagged = 1 ORDER BY timestamp ASC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_readings_by_robot(robot_id: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM readings WHERE robot_id = ? ORDER BY timestamp ASC", (robot_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_flag(reading_id: int, flagged: bool, flag_reasons: list):
    """Used by the batch re-QA step to overwrite a row's flag result."""
    conn = get_connection()
    conn.execute(
        "UPDATE readings SET flagged = ?, flag_reasons = ? WHERE id = ?",
        (int(flagged), ",".join(flag_reasons), reading_id)
    )
    conn.commit()
    conn.close()


def reset_db():
    """Wipe the table clean -- handy while you're testing."""
    conn = get_connection()
    conn.execute("DELETE FROM readings")
    conn.commit()
    conn.close()
