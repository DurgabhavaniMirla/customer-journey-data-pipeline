# Customer Journey Data Engineering Pipeline

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
