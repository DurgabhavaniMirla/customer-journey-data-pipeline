import os
import json
import sqlite3
import pandas as pd

DB_NAME = "customer_journey.db"
OUTPUT_JSON = "ground_truth.json"

print("[Info] Compiling Master Ground Truth JSON...")

if not os.path.exists(DB_NAME):
    raise FileNotFoundError(f"Database {DB_NAME} not found.")

conn = sqlite3.connect(DB_NAME)

# 1. Pull the separate ground truth labels and anomalies
outcomes = pd.read_sql("SELECT session_id, outcome_type FROM journey_outcome", conn)
anomalies = pd.read_sql("SELECT session_id, issue_type, description FROM ground_truth", conn)
conn.close()

print("[Info] Processing labels and exception classifications...")

# 2. Build the exact structure requested by Step 12
ground_truth_dict = {}

# Set expected outcomes and conversion/abandonment labels
for _, row in outcomes.iterrows():
    s_id = row['session_id']
    o_type = row['outcome_type']
    
    ground_truth_dict[s_id] = {
        "expected_journey_outcome": o_type,
        "correct_conversion_label": 1 if o_type == "conversion" else 0,
        "expected_abandonment_label": 1 if o_type == "abandonment" else 0,
        "known_anomalies": [],
        "exception_classifications": []
    }

# Inject the anomalies and exception classifications
for _, row in anomalies.iterrows():
    s_id = row['session_id']
    if s_id in ground_truth_dict:
        ground_truth_dict[s_id]["known_anomalies"].append(row['issue_type'])
        ground_truth_dict[s_id]["exception_classifications"].append(row['description'])

# 3. Export to separate JSON file
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(ground_truth_dict, f, indent=4)

print(f"[Success] Master ground truth exported successfully to: {os.path.abspath(OUTPUT_JSON)}")
print(f" -> Total Sessions Labeled: {len(ground_truth_dict):,}")