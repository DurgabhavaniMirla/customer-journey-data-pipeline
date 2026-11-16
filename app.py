import sqlite3
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Customer Journey Analytics Platform",
    page_icon="📈",
    layout="wide",
)

st.title("Customer Journey & High-Friction Path Analytics")
st.markdown(
    "**Enterprise Analytics Portal** | End-to-End Data Pipeline & SQLite Engine"
)
st.markdown("---")


# Load Data from SQLite Database
@st.cache_resource
def load_data():
  conn = sqlite3.connect("customer_journey.db")
  sessions = pd.read_sql("SELECT * FROM session", conn)
  orders = pd.read_sql("SELECT * FROM 'order'", conn)
  events = pd.read_sql("SELECT * FROM journey_event", conn)
  ground_truth = pd.read_sql("SELECT * FROM ground_truth", conn)
  conn.close()
  return sessions, orders, events, ground_truth


sessions, orders, events, ground_truth = load_data()

# Top-Level KPI Metric Cards
col1, col2, col3, col4 = st.columns(4)
total_sessions = len(sessions)
total_conversions = len(orders)
conv_rate = (
    (total_conversions / total_sessions) * 100 if total_sessions > 0 else 0
)
total_anomalies = len(ground_truth)

col1.metric("Total Sessions", f"{total_sessions:,}")
col2.metric("Successful Conversions", f"{total_conversions:,}")
col3.metric("Funnel Conversion Rate", f"{conv_rate:.2f}%")
col4.metric("Logged Anomalies", f"{total_anomalies:,}")
st.markdown("---")

# Multi-Tab Professional Layout
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Funnel & Channels",
        "High-Friction Paths",
        "Ground Truth Anomalies",
        "Database Inspector",
    ]
)

with tab1:
  st.subheader("Channel Distribution & Session Overview")
  st.markdown("Analysis of incoming user traffic across web, app, and support channels.")

  col_a, col_b = st.columns(2)
  with col_a:
    channel_counts = sessions["channel"].value_counts().reset_index()
    channel_counts.columns = ["Channel", "Session Count"]
    st.bar_chart(channel_counts.set_index("Channel"))
  with col_b:
    st.dataframe(channel_counts, use_container_width=True, hide_index=True)

with tab2:
  st.subheader("Drop-off & Event Bottleneck Analysis")
  st.markdown("Tracking user touchpoints to locate friction loops and drop-offs.")

  event_summary = events["event_type"].value_counts().reset_index()
  event_summary.columns = ["Event Type", "Total Occurrences"]
  st.bar_chart(event_summary.set_index("Event Type"))

with tab3:
  st.subheader("Isolated Anomaly Ground Truth Manifest")
  st.markdown(
      "Explicitly logged failure modes and edge cases (bot traffic, duplicate"
      " conversions, ingestion delays)."
  )

  issue_types = ["All"] + list(ground_truth["issue_type"].unique())
  selected_issue = st.selectbox("Filter by Anomaly Type", issue_types)

  if selected_issue != "All":
    filtered_gt = ground_truth[ground_truth["issue_type"] == selected_issue]
  else:
    filtered_gt = ground_truth

  st.dataframe(filtered_gt, use_container_width=True, hide_index=True)

with tab4:
  st.subheader("SQLite Relational Database Inspector")
  st.markdown("Inspect raw records directly from the underlying SQLite database.")

  conn = sqlite3.connect("customer_journey.db")
  tables_df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
  selected_table = st.selectbox("Select Database Table", tables_df["name"].tolist())

  table_data = pd.read_sql(f"SELECT * FROM '{selected_table}' LIMIT 100", conn)
  conn.close()

  st.write(f"Previewing top 100 rows for table: `{selected_table}`")
  st.dataframe(table_data, use_container_width=True)