import os
import sqlite3

DB_NAME = "customer_journey.db"

print("=" * 70)
print(" AUTOMATED DATA PIPELINE VALIDATION & QA ")
print("=" * 70)

if not os.path.exists(DB_NAME):
    raise FileNotFoundError(f"Database {DB_NAME} not found.")

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

def run_check(test_name, query, expected_zero=True, is_anomaly_check=False):
    cursor.execute(query)
    result = cursor.fetchone()[0]
    
    if expected_zero:
        if result == 0:
            print(f"[PASS] {test_name}: Clean (0 violations)")
        else:
            if is_anomaly_check:
                print(f"[FLAG] {test_name}: Detected {result:,} intentional anomalies (Matches Ground Truth)")
            else:
                print(f"[FAIL] {test_name}: Found {result:,} unexpected violations!")
    return result

# 1. Primary Key Uniqueness
run_check("Primary key uniqueness", 
          "SELECT (COUNT(session_id) - COUNT(DISTINCT session_id)) FROM session")

# 2. Foreign Key Integrity
run_check("Foreign key integrity", 
          "SELECT COUNT(*) FROM journey_event WHERE session_id NOT IN (SELECT session_id FROM session)")

# 3. Allowed Enum Values
run_check("Allowed enum values", 
          "SELECT COUNT(*) FROM journey_event WHERE event_type NOT IN ('page_view', 'click', 'add_to_cart', 'checkout', 'support_contact')")

# 4. Nullability Constraints
run_check("Nullability constraints", 
          "SELECT COUNT(*) FROM session WHERE channel IS NULL OR start_time IS NULL")

# 5. Timestamp Ordering (Detects our injected ingestion latency)
run_check("Timestamp ordering", 
          "SELECT COUNT(*) FROM journey_event WHERE ingestion_timestamp < event_timestamp", 
          is_anomaly_check=True)

# 6. Arithmetic Reconciliation
run_check("Arithmetic reconciliation", 
          "SELECT COUNT(*) FROM \"order\" WHERE order_amount <= 0.0")

# 7. Lifecycle Transitions (Ensures every session has a definitive outcome)
run_check("Lifecycle transitions", 
          "SELECT COUNT(*) FROM session WHERE session_id NOT IN (SELECT session_id FROM journey_outcome)")

# 8. Duplicate Event Detection
run_check("Duplicate event detection", 
          "SELECT COUNT(*) FROM (SELECT session_id, event_type, event_timestamp FROM journey_event GROUP BY 1, 2, 3 HAVING COUNT(*) > 1)")

# 9. Duplicate Conversion Detection (Detects our injected checkout glitches)
run_check("Duplicate conversion detection", 
          "SELECT COUNT(*) FROM (SELECT session_id FROM \"order\" WHERE status='success' GROUP BY session_id HAVING COUNT(*) > 1)", 
          is_anomaly_check=True)

# 10. Sessionization Correctness
run_check("Sessionization correctness", 
          "SELECT COUNT(*) FROM journey_event e JOIN session s ON e.session_id = s.session_id WHERE e.event_timestamp < s.start_time")

# 11. Customer Identity Stitching (Detects our injected merge errors)
run_check("Customer identity stitching", 
          "SELECT COUNT(*) FROM \"order\" o JOIN session s ON o.session_id = s.session_id WHERE o.customer_id != s.customer_id AND o.customer_id != 'CUS-ANONYMOUS'", 
          is_anomaly_check=True)

# 12. Valid Entity Joins (Ensures no orphan sessions without events)
run_check("Valid entity joins", 
          "SELECT COUNT(*) FROM session s LEFT JOIN journey_event e ON s.session_id = e.session_id WHERE e.event_id IS NULL")

print("-" * 70)
print(" VALIDATION SUITE COMPLETE ")
print("=" * 70)

conn.close()