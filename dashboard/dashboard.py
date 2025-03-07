import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ovos_metrics")
engine = create_engine(DATABASE_URL)

st.set_page_config(page_title="OVOS Metrics Dashboard", layout="wide")

st.title("📊 OVOS Metrics Dashboard")

# Load Data
@st.cache_data(ttl=60)
def load_data():
    query = "SELECT * FROM metrics ORDER BY timestamp DESC"
    return pd.read_sql(query, engine)

df = load_data()

if df.empty:
    st.warning("⚠️ No data available yet!")
else:
    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    languages = st.sidebar.multiselect("Select Language", df["language"].unique(), default=df["language"].unique())
    intents = st.sidebar.multiselect("Select Intent", df["intent"].unique(), default=df["intent"].unique())

    # Date Filter
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    min_date, max_date = df["timestamp"].min(), df["timestamp"].max()
    start_date, end_date = st.sidebar.date_input("📅 Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    # Apply Filters
    df_filtered = df[(df["language"].isin(languages)) & (df["intent"].isin(intents))]
    df_filtered = df_filtered[(df_filtered["timestamp"].dt.date >= start_date) & (df_filtered["timestamp"].dt.date <= end_date)]

    # Summary Stats
    col1, col2, col3 = st.columns(3)
    col1.metric("📌 Total Records", len(df_filtered))
    col2.metric("🎯 Unique Intents", df_filtered["intent"].nunique())
    col3.metric("🗣️ Languages", df_filtered["language"].nunique())

    # Data Table with Search & Sorting
    st.subheader("📋 Data Table")
    st.dataframe(df_filtered)

    # Charts
    col4, col5 = st.columns(2)

    with col4:
        st.subheader("🌍 Language Distribution")
        fig = px.pie(df_filtered, names="language", title="Languages Used", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)

    with col5:
        st.subheader("💡 Intent Distribution")
        fig = px.pie(df_filtered, names="intent", title="Intent Frequency", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)

    # Export Options
    st.subheader("📤 Export Data")
    col6, col7 = st.columns(2)

    with col6:
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download CSV", csv, "ovos_metrics.csv", "text/csv")

    with col7:
        json = df_filtered.to_json(orient="records")
        st.download_button("⬇️ Download JSON", json, "ovos_metrics.json", "application/json")

    # Refresh Button
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.experimental_rerun()
