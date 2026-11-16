import os
import sqlite3
import json

DB_NAME = "customer_journey.db"
os.makedirs("docs", exist_ok=True)

print("[Info] Generating Documentation and Exports...")

# 1. Export SQL Schema
conn = sqlite3.connect(DB_NAME)
with open("schema.sql", "w", encoding="utf-8") as f:
    for line in conn.iterdump():
        f.write(f"{line}\n")
conn.close()
print(" -> Exported schema.sql")

# 2. Source Manifest (Lawful Data Usage)
manifest = {
    "project_name": "Customer Journey Data Engineering Pipeline",
    "data_provenance": {
        "source_type": "100% Synthetic",
        "seed_value": 20261022,
        "generation_script": "generate_journey_data.py",
        "external_data_used": False,
        "license": "MIT / Open for Hackathon Evaluation",
        "attribution": "Generated entirely via programmatic pseudo-randomization."
    }
}
with open("source_manifest.json", "w") as f:
    json.dump(manifest, f, indent=4)
print(" -> Exported source_manifest.json")

# 3. Data Dictionary & ERD
data_dict_content = """# Data Dictionary & Database Schema

## Entity Relationship Diagram (Text Representation)
* `customer` (1) ---> (M) `session`
* `session` (1) ---> (M) `journey_event`
* `session` (1) ---> (M) `cart`
* `session` (1) ---> (0,1) `order`
* `session` (1) ---> (0,1) `support_ticket`
* `session` (1) ---> (1) `experiment`
* `session` (1) ---> (1) `journey_outcome`
* `product` (1) ---> (M) `cart`
* `page` (1) ---> (M) `journey_event` (implicit via URL)

## Entities (10 Core Entities)
1. **customer**: Master user profiles. (customer_id [PK], consent_status)
2. **session**: Traffic sessions. (session_id [PK], customer_id [FK])
3. **page**: Website hierarchy. (page_id [PK])
4. **product**: Catalog items. (product_id [PK])
5. **journey_event**: Clickstream interactions. (event_id [PK], session_id [FK])
6. **cart**: Intermediate transaction states (Bridge). (cart_id [PK], product_id [FK])
7. **order**: Successful conversions. (order_id [PK], session_id [FK])
8. **support_ticket**: Friction logs. (ticket_id [PK], session_id [FK])
9. **experiment**: A/B testing variants. (experiment_id [PK], session_id [FK])
10. **journey_outcome**: Final derived session state. (outcome_id [PK], session_id [FK])

## Business Rules & Funnel Definitions
* **Sessionization:** Grouped by `session_id`, bounded by `start_time` and the final chronological event.
* **Funnel Sequence:** page_view -> click -> add_to_cart -> checkout.
* **Anomaly Taxonomy:** bot_traffic_spike, ingestion_ordering_anomaly, duplicate_conversion, anonymous_id_merge_error.
"""
with open("docs/data_dictionary.md", "w") as f:
    f.write(data_dict_content)
print(" -> Exported docs/data_dictionary.md")

# 4. Master README
readme_content = """# Customer Journey Data Engineering Pipeline

## Project Overview
An automated, strict-schema data pipeline generating 100,000 sessions and ~2,000,000 cross-channel events. It handles identity stitching, A/B experiments, and automated QA validation.

## Execution Instructions
Run the pipeline in this exact order:
1. `python generate_journey_data.py` (Generates synthetic CSVs)
2. `python load_to_sqlite.py` (Enforces referential integrity in SQLite)
3. `python analyze_journeys.py` (Derives analytics from raw records)
4. `python validate_pipeline.py` (Runs automated QA checks)
5. `python export_ground_truth.py` (Compiles ground_truth.json)
6. `python generate_summary_report.py` (Generates final metrics)

## Validation & Provenance
* All data is 100% synthetically generated (Seed: 20261022).
* Separate ground-truth prevents label leakage.
* Fully reproducible.
"""
with open("README.md", "w") as f:
    f.write(readme_content)
print(" -> Exported README.md")
print("[Success] Documentation is ready.")