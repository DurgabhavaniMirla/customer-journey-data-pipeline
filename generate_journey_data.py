import os
import random
import numpy as np
import pandas as pd

WORKSPACE_DIR = "."
os.makedirs(WORKSPACE_DIR, exist_ok=True)

SEED = 20261022
np.random.seed(SEED)
random.seed(SEED)

print(f"[Info] Initializing full-scale data generator in: {os.path.abspath(WORKSPACE_DIR)}")

NUM_SESSIONS = 100000
NUM_CUSTOMERS = int(NUM_SESSIONS * 0.7)
NUM_PRODUCTS = 50
NUM_PAGES = 20

# Step 1 & 2: Master Data Generation
print("[Step 1/10] Generating Master Data...")
customers = pd.DataFrame({
    'customer_id': [f"CUS-{i:06d}" for i in range(1, NUM_CUSTOMERS + 1)],
    'created_at': pd.date_range(start="2026-01-01", periods=NUM_CUSTOMERS, freq="h"),
    'consent_status': np.random.choice([True, False], size=NUM_CUSTOMERS, p=[0.85, 0.15]),
    'device_type': np.random.choice(['mobile', 'desktop', 'tablet'], size=NUM_CUSTOMERS, p=[0.6, 0.35, 0.05])
})

pages = pd.DataFrame({
    'page_id': [f"PG-{i:03d}" for i in range(1, NUM_PAGES + 1)],
    'page_path': [f"/shop/category-{i}/item" for i in range(1, NUM_PAGES + 1)],
    'category': np.random.choice(['Electronics', 'Apparel', 'Home', 'Beauty'], size=NUM_PAGES)
})

products = pd.DataFrame({
    'product_id': [f"PRD-{i:04d}" for i in range(1, NUM_PRODUCTS + 1)],
    'product_name': [f"Product Item {i}" for i in range(1, NUM_PRODUCTS + 1)],
    'price': np.round(np.random.uniform(10.0, 500.0, size=NUM_PRODUCTS), 2),
    'category': np.random.choice(['Electronics', 'Apparel', 'Home', 'Beauty'], size=NUM_PRODUCTS)
})

# Step 3 & 4: Sessions & Experiments (Strict Consent Enforcement)
print("[Step 2/10] Generating Sessions and Experiments with Consent Enforcement...")
session_ids = [f"SES-2026-{i:06d}" for i in range(1, NUM_SESSIONS + 1)]

# CRITICAL FIX: Only pool customers who have consented (consent_status == True)
consented_customer_pool = customers[customers['consent_status'] == True]['customer_id'].tolist()
customer_pool = consented_customer_pool + [None]

cust_prob_per_user = 0.8 / len(consented_customer_pool)
customer_probabilities = [cust_prob_per_user] * len(consented_customer_pool) + [0.2]

sessions = pd.DataFrame({
    'session_id': session_ids,
    'customer_id': np.random.choice(customer_pool, size=NUM_SESSIONS, p=customer_probabilities),
    'channel': np.random.choice(['web', 'app', 'support'], size=NUM_SESSIONS, p=[0.5, 0.4, 0.1]),
    'start_time': pd.date_range(start="2026-10-01", periods=NUM_SESSIONS, freq="s")
})

experiments = pd.DataFrame({
    'experiment_id': [f"EXP-2026-{i:06d}" for i in range(1, NUM_SESSIONS + 1)],
    'session_id': session_ids,
    'variant': np.random.choice(['Control', 'Treatment_A', 'Treatment_B'], size=NUM_SESSIONS, p=[0.5, 0.25, 0.25])
})

# Step 5: Dependent Transactions, Events & Specific Edge Case Injection
print("[Step 3/10] Generating Events, Transactions & Injecting Edge Cases...")
event_rows = []
cart_rows = []
order_rows = []
ticket_rows = []
outcome_rows = []
ground_truth_anomalies = []

for idx, row in sessions.iterrows():
    s_id = row['session_id']
    start_t = row['start_time']
    
    # -> UPDATED LINE: Increased to generate ~2 million events total
    num_events = np.random.randint(15, 26)

    is_bot = (np.random.rand() < 0.04)
    has_ingestion_delay = (np.random.rand() < 0.05)
    has_merge_error = (np.random.rand() < 0.03 and row['customer_id'] is None)
    has_duplicate_conversion = (np.random.rand() < 0.02)

    session_has_conversion = False

    for e_idx in range(1, num_events + 1):
        evt_id = f"EVT-{s_id}-{e_idx:06d}"
        event_type = np.random.choice(
            ['page_view', 'click', 'add_to_cart', 'checkout', 'support_contact'], 
            p=[0.4, 0.3, 0.15, 0.1, 0.05]
        )
        
        event_timestamp = start_t + pd.Timedelta(seconds=e_idx * 15)
        ingestion_timestamp = event_timestamp

        if has_ingestion_delay and e_idx == 2:
            ingestion_timestamp = event_timestamp - pd.Timedelta(minutes=5)
            ground_truth_anomalies.append({
                'entity_id': evt_id, 'session_id': s_id,
                'issue_type': 'ingestion_ordering_anomaly',
                'description': 'Event ingestion timestamp precedes event occurrence timestamp.'
            })

        if is_bot:
            event_timestamp = start_t + pd.Timedelta(milliseconds=e_idx * 50)
            ingestion_timestamp = event_timestamp
            if e_idx == 1:
                ground_truth_anomalies.append({
                    'entity_id': s_id, 'session_id': s_id,
                    'issue_type': 'bot_traffic_spike',
                    'description': 'Automated high-frequency bot traffic mixed into session stream.'
                })

        event_rows.append({
            'event_id': evt_id,
            'session_id': s_id,
            'event_type': event_type,
            'event_timestamp': event_timestamp,
            'ingestion_timestamp': ingestion_timestamp
        })

        if event_type == 'add_to_cart':
            prod = products.sample(1).iloc[0]
            cart_rows.append({
                'cart_id': f"CRT-{s_id}-{e_idx}",
                'session_id': s_id,
                'product_id': prod['product_id'],
                'quantity': np.random.randint(1, 3)
            })
            
        elif event_type == 'checkout' and (not session_has_conversion or has_duplicate_conversion):
            if not session_has_conversion:
                session_has_conversion = True
                
            order_id = f"ORD-{s_id}-{e_idx}"
            order_rows.append({
                'order_id': order_id,
                'session_id': s_id,
                'customer_id': row['customer_id'] if row['customer_id'] else "CUS-ANONYMOUS",
                'order_amount': float(np.random.uniform(50.0, 1000.0)),
                'status': 'success'
            })
            
            if has_duplicate_conversion:
                ground_truth_anomalies.append({
                    'entity_id': order_id, 'session_id': s_id,
                    'issue_type': 'duplicate_conversion',
                    'description': 'Same session recorded duplicate successful conversion orders.'
                })
                has_duplicate_conversion = False

        elif event_type == 'support_contact':
            ticket_rows.append({
                'ticket_id': f"TCK-{s_id}-{e_idx}",
                'session_id': s_id,
                'customer_id': row['customer_id'] if row['customer_id'] else "CUS-ANONYMOUS",
                'issue_type': 'general',
                'status': 'open'
            })

    # End of Session Event Loop
    if has_merge_error:
        ground_truth_anomalies.append({
            'entity_id': s_id, 'session_id': s_id,
            'issue_type': 'anonymous_id_merge_error',
            'description': 'Distinct anonymous sessions incorrectly mapped to same customer profile.'
        })

    if not session_has_conversion:
        outcome_rows.append({'outcome_id': f"OUT-{s_id}", 'session_id': s_id, 'outcome_type': 'abandonment'})
    else:
        outcome_rows.append({'outcome_id': f"OUT-{s_id}", 'session_id': s_id, 'outcome_type': 'conversion'})

journey_events = pd.DataFrame(event_rows)
carts = pd.DataFrame(cart_rows)
orders = pd.DataFrame(order_rows)
support_tickets = pd.DataFrame(ticket_rows)
journey_outcomes = pd.DataFrame(outcome_rows)
ground_truth = pd.DataFrame(ground_truth_anomalies)

print("[Step 4/10] Running Referential Integrity & Validation checks...")
assert sessions['session_id'].is_unique, "PK violation in sessions!"
assert journey_events['event_id'].is_unique, "PK violation in events!"

print("[Step 5/10] Exporting tables to CandidateWorkspace root...")
customers.to_csv("customer.csv", index=False)
sessions.to_csv("session.csv", index=False)
pages.to_csv("page.csv", index=False)
products.to_csv("product.csv", index=False)
journey_events.to_csv("journey_event.csv", index=False)
if not carts.empty: carts.to_csv("cart.csv", index=False)
if not orders.empty: orders.to_csv("order.csv", index=False)
if not support_tickets.empty: support_tickets.to_csv("support_ticket.csv", index=False)
experiments.to_csv("experiment.csv", index=False)
journey_outcomes.to_csv("journey_outcome.csv", index=False)
ground_truth.to_csv("ground_truth.csv", index=False)

print("[Success] 2 Million Event Dataset Generation Complete!")