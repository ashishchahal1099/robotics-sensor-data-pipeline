"""
api.py
------
A small Flask REST API sitting on top of the SQLite database, so any
client (browser, dashboard, curl, Postman) can query live telemetry and
alerts over HTTP.

Endpoints:
  GET /health                     -> simple liveness check
  GET /telemetry                  -> all readings
  GET /telemetry/<robot_id>       -> readings for one robot
  GET /alerts                     -> only flagged (anomalous) readings
  GET /stats                      -> summary counts (total, flagged, flag rate)

Run with:  python3 api.py
Then visit http://localhost:5000/telemetry in a browser or:
  curl http://localhost:5000/alerts
"""

from flask import Flask, jsonify
import db

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/telemetry")
def telemetry():
    return jsonify(db.get_all_readings())


@app.route("/telemetry/<robot_id>")
def telemetry_by_robot(robot_id):
    rows = db.get_readings_by_robot(robot_id)
    if not rows:
        return jsonify({"error": f"no readings found for {robot_id}"}), 404
    return jsonify(rows)


@app.route("/alerts")
def alerts():
    return jsonify(db.get_flagged_readings())


@app.route("/stats")
def stats():
    all_rows = db.get_all_readings()
    flagged_rows = [r for r in all_rows if r["flagged"]]
    total = len(all_rows)
    flagged = len(flagged_rows)
    rate = (flagged / total * 100) if total else 0
    return jsonify({
        "total_readings": total,
        "flagged_readings": flagged,
        "flag_rate_percent": round(rate, 2),
    })


if __name__ == "__main__":
    # host="0.0.0.0" so it's reachable from outside the Docker container too
    app.run(host="0.0.0.0", port=5000, debug=True)
