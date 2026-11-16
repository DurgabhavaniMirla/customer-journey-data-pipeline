import os
import pandas as pd

WORKSPACE_DIR = "."
print("=" * 60)
print(" RUNNING CUSTOMER JOURNEY & HIGH-FRICTION DROP-OFF ANALYTICS ")
print("=" * 60)

# 1. Load Data
try:
    sessions = pd.read_csv(os.path.join(WORKSPACE_DIR, "session.csv"))
    events = pd.read_csv(os.path.join(WORKSPACE_DIR, "journey_event.csv"))
    orders = pd.read_csv(os.path.join(WORKSPACE_DIR, "order.csv"))
    outcomes = pd.read_csv(os.path.join(WORKSPACE_DIR, "journey_outcome.csv"))
    ground_truth = pd.read_csv(os.path.join(WORKSPACE_DIR, "ground_truth.csv"))
except FileNotFoundError as e:
    print(f"[Error] Missing required CSV files: {e}. Run data generator first.")
    exit(1)

# 2. Funnel Analysis & Conversion Metrics
print("\n[1] --- Funnel Stage & Conversion Analysis ---")
total_sessions = len(sessions)
total_conversions = len(orders)
conversion_rate = (total_conversions / total_sessions) * 100

print(f"Total Sessions Analyzed: {total_sessions:,}")
print(f"Total Successful Conversions (Orders): {total_conversions:,}")
print(f"Overall Funnel Conversion Rate: {conversion_rate:.2f}%")

# Funnel breakdown by channel
channel_funnel = (
    sessions.merge(outcomes, on="session_id", how="left")
    .groupby("channel")["outcome_type"]
    .value_counts(normalize=True)
    .unstack()
    .fillna(0)
    * 100
)
print("\nConversion & Outcome Breakdown by Channel (%):")
print(channel_funnel.round(2))

# 3. High-Friction Path, Bottleneck & Derivation Analytics
print("\n[2] --- Derived Metrics: Latency, Duration & Drop-off Detection ---")

# Convert timestamps to datetime for accurate math
events['event_timestamp'] = pd.to_datetime(events['event_timestamp'])
events['ingestion_timestamp'] = pd.to_datetime(events['ingestion_timestamp'])

# Derive latency directly from timestamps
events['latency_seconds'] = (events['ingestion_timestamp'] - events['event_timestamp']).dt.total_seconds()

# Calculate event counts, duration, latency, and exact drop-off stage from raw events
session_friction = (
    events.groupby("session_id")
    .agg(
        event_count=("event_id", "count"),
        unique_steps=("event_type", "nunique"),
        has_support=("event_type", lambda x: "support_contact" in x.values),
        session_duration_seconds=("event_timestamp", lambda x: (x.max() - x.min()).total_seconds()),
        avg_latency_seconds=("latency_seconds", "mean"),
        drop_off_stage=("event_type", "last") # The exact last action they took
    )
    .reset_index()
)

# Merge with outcomes to identify friction in abandoned vs converted sessions
friction_analysis = session_friction.merge(outcomes, on="session_id")
friction_summary = (
    friction_analysis.groupby("outcome_type")
    .agg(
        avg_events=("event_count", "mean"),
        avg_duration_sec=("session_duration_seconds", "mean"),
        avg_latency_sec=("avg_latency_seconds", "mean"),
        support_contact_ratio=("has_support", "mean"),
    )
    .reset_index()
)

print("\nDerived Journey Metrics by Session Outcome:")
print(friction_summary.round(2).to_string(index=False))

# Show the top drop-off stages for abandoned sessions
abandoned_sessions = friction_analysis[friction_analysis['outcome_type'] == 'abandonment']
top_drop_offs = abandoned_sessions['drop_off_stage'].value_counts(normalize=True) * 100
print("\nTop Funnel Drop-off Stages (% of abandoned sessions):")
print(top_drop_offs.round(2).head())

# 4. Anomaly & Ground Truth Evaluation
print("\n[3] --- Ground Truth Validation & Anomaly Detection ---")
total_anomalies = len(ground_truth)
bot_sessions = ground_truth[
    ground_truth["issue_type"] == "bot_traffic_spike"
].shape[0]

print(f"Total Ground-Truth Anomalies Logged: {total_anomalies:,}")
print(f"  - Bot Traffic Spikes: {bot_sessions:,}")
print(
    f"  - Anomaly Ratio in Dataset: {(total_anomalies / total_sessions)*100:.2f}%"
)

print("\n" + "=" * 60)
print(" ANALYTICS PIPELINE COMPLETED SUCCESSFULLY ")
print("=" * 60)