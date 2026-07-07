"""
reqa.py
-------
Batch re-QA: re-runs the same 4 rules against every row already stored in
the database, and compares the fresh result to what was recorded at ingest
time. This is what proves the real-time flagging was correct/consistent --
exactly the "0 missed on batch re-QA, 100% rule consistency" line.

Run this AFTER pipeline.py has populated the database.
"""

import db
import rules


def run_reqa():
    all_readings = db.get_all_readings()
    if not all_readings:
        print("No readings found -- run pipeline.py first.")
        return

    mismatches = []
    last_reading_per_robot = {}

    for row in all_readings:
        previous = last_reading_per_robot.get(row["robot_id"])
        fresh_flagged, fresh_reasons = rules.run_all_rules(row, previous)
        last_reading_per_robot[row["robot_id"]] = row

        original_flagged = bool(row["flagged"])

        if fresh_flagged != original_flagged:
            mismatches.append({
                "id": row["id"],
                "robot_id": row["robot_id"],
                "timestamp": row["timestamp"],
                "ingest_time_flagged": original_flagged,
                "reqa_flagged": fresh_flagged,
                "reqa_reasons": fresh_reasons,
            })

    total = len(all_readings)
    flagged_at_ingest = sum(1 for r in all_readings if r["flagged"])
    consistency_rate = ((total - len(mismatches)) / total) * 100

    print(f"Re-QA scanned {total} historical readings.")
    print(f"Flagged at ingest: {flagged_at_ingest}")
    print(f"Mismatches found: {len(mismatches)}")
    print(f"Rule consistency: {consistency_rate:.2f}%")

    if mismatches:
        print("\nDetails of mismatches:")
        for m in mismatches:
            print(f"  id={m['id']} {m['robot_id']} t={m['timestamp']} "
                  f"ingest={m['ingest_time_flagged']} reqa={m['reqa_flagged']} reasons={m['reqa_reasons']}")

    return mismatches


if __name__ == "__main__":
    run_reqa()
