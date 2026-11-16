import os
import sqlite3
import pandas as pd

DB_NAME = "customer_journey.db"
WORKSPACE_DIR = "."

print("[Info] Setting up strict relational schema and loading CSVs...")
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Step 4: Strict SQL Table Definitions with PK, FK, and Enum Constraints
schema_script = """
DROP TABLE IF EXISTS "order";
DROP TABLE IF EXISTS journey_event;
DROP TABLE IF EXISTS session;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS ground_truth;

CREATE TABLE customer (
    customer_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    consent_status BOOLEAN NOT NULL,
    device_type TEXT NOT NULL CHECK(device_type IN ('mobile', 'desktop', 'tablet'))
);

CREATE TABLE session (
    session_id TEXT PRIMARY KEY,
    customer_id TEXT,
    channel TEXT NOT NULL CHECK(channel IN ('web', 'app', 'support')),
    start_time TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customer(customer_id)
);

CREATE TABLE journey_event (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('page_view', 'click', 'add_to_cart', 'checkout', 'support_contact')),
    event_timestamp TEXT NOT NULL,
    ingestion_timestamp TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES session(session_id)
);

CREATE TABLE "order" (
    order_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    order_amount REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('success', 'abandoned')),
    FOREIGN KEY(session_id) REFERENCES session(session_id)
);

CREATE TABLE ground_truth (
    entity_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL
);

-- Creating Indexes for frequently queried columns
CREATE INDEX idx_session_customer ON session(customer_id);
CREATE INDEX idx_event_session ON journey_event(session_id);
CREATE INDEX idx_order_session ON "order"(session_id);
"""

# Execute the strict schema
cursor.executescript(schema_script)

tables = [
    "customer",
    "session",
    "journey_event",
    "order",
    "ground_truth",
    "page",          # Pandas will auto-generate basic schema for non-strict tables
    "product",
    "cart",
    "support_ticket",
    "experiment",
    "journey_outcome"
]

for table in tables:
    csv_path = os.path.join(WORKSPACE_DIR, f"{table}.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # We use "append" so Pandas respects our strict SQL constraints
        df.to_sql(table, conn, if_exists="append", index=False)
        print(f" -> Loaded '{table}.csv' into table '{table}' ({len(df):,} rows)")

conn.close()
print(f"[Success] Database '{DB_NAME}' created successfully with strict constraints!")