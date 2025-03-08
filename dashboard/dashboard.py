import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os
import io

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ovos_metrics")
engine = create_engine(DATABASE_URL)

st.set_page_config(page_title="OVOS Metrics Dashboard", layout="wide")

st.title("📊 OVOS Community Dataset")


# Load metadata only (NO AUDIO DATA)
@st.cache_data(ttl=60)
def load_data(query):
    return pd.read_sql(query, engine)


# Load metadata only (no audio) for wake words & utterances
wake_words_df = load_data(
    "SELECT id, name, model, plugin, plugin_config, language, timestamp FROM wake_words ORDER BY timestamp DESC")
utterances_df = load_data(
    "SELECT id, transcript, model, plugin, plugin_config, language, timestamp FROM stt ORDER BY timestamp DESC")
intent_df = load_data(
    "SELECT * FROM intents ORDER BY timestamp DESC")


# TODO - Fetch audio on demand
def fetch_audio(wake_word_id=None, utterance_id=None):
    query = None
    if wake_word_id:
        query = f"SELECT audio FROM wake_words WHERE id = {wake_word_id}"
    elif utterance_id:
        query = f"SELECT audio FROM stt WHERE id = {utterance_id}"

    if query:
        with engine.connect() as connection:
            result = connection.execute(query).fetchone()
            if result and result[0]:
                return io.BytesIO(result[0])  # Convert to a stream for playback
    return None


# Create tabs
tab1, tab2, tab3 = st.tabs(["🧭 Intents", "🎤 Wake Words", "🗣️ Utterances"])

with tab1:
    if intent_df.empty:
        st.warning("⚠️ No data available yet!")
    else:
        st.subheader("🧭 Intents")

        # Sidebar Filters
        st.sidebar.header("🔍 Intent Filters")
        languages = st.sidebar.multiselect("Select Language", intent_df["language"].unique(), default=intent_df["language"].unique())
        intents = st.sidebar.multiselect("Select Intent", intent_df["intent"].unique(), default=intent_df["intent"].unique())

        # Date Filter
        intent_df["timestamp"] = pd.to_datetime(intent_df["timestamp"])
        min_date, max_date = intent_df["timestamp"].min(), intent_df["timestamp"].max()
        start_date, end_date = st.sidebar.date_input("📅 Select Date Range", [min_date, max_date], min_value=min_date,
                                                     max_value=max_date)

        # Apply Filters
        df_filtered = intent_df[(intent_df["language"].isin(languages)) & (intent_df["intent"].isin(intents))]
        df_filtered = df_filtered[
            (df_filtered["timestamp"].dt.date >= start_date) & (df_filtered["timestamp"].dt.date <= end_date)]

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
            fig = px.pie(df_filtered, names="language", title="Languages Used", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)

        with col5:
            st.subheader("💡 Intent Distribution")
            fig = px.pie(df_filtered, names="intent", title="Intent Frequency", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Set3)
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


with tab2:
    if wake_words_df.empty:
        st.warning("⚠️ No wake words available!")
    else:
        st.subheader("🎤 Wake Words")

        # Sidebar Filters
        st.sidebar.header("🔍 Wake Words Filters")
        models = st.sidebar.multiselect("Select Model", wake_words_df["model"].unique(),
                                        default=wake_words_df["model"].unique())
        plugins = st.sidebar.multiselect("Select Plugin", wake_words_df["plugin"].unique(),
                                         default=wake_words_df["plugin"].unique())

        wake_words_df = wake_words_df[(wake_words_df["model"].isin(models)) & (wake_words_df["plugin"].isin(plugins))]

        # Summary Stats
        col1, col2, col3 = st.columns(3)
        col1.metric("📌 Total Records", len(wake_words_df))
        col2.metric("🎯 Unique WakeWords", wake_words_df["name"].nunique())
        col3.metric("🗣️ Languages", wake_words_df["language"].nunique())

        # Frequency Chart
        st.subheader("📈 Most Common Wake Words")
        fig = px.bar(wake_words_df["name"].value_counts(), title="Wake Word Frequency",
                     labels={"index": "Wake Word", "value": "Count"})
        st.plotly_chart(fig, use_container_width=True)

        # Data Table with Search & Sorting
        st.subheader("📋 Data Table")
        st.dataframe(wake_words_df)

with tab3:
    if utterances_df.empty:
        st.warning("⚠️ No utterances available!")
    else:
        st.subheader("🗣️ Utterances")

        # Sidebar Filters
        st.sidebar.header("🔍 STT Filters")
        models = st.sidebar.multiselect("Select Model", utterances_df["model"].unique(),
                                        default=utterances_df["model"].unique())
        plugins = st.sidebar.multiselect("Select Plugin", utterances_df["plugin"].unique(),
                                         default=utterances_df["plugin"].unique())

        utterances_df = utterances_df[(utterances_df["model"].isin(models)) & (utterances_df["plugin"].isin(plugins))]

        # Summary Stats
        col1, col2, col3 = st.columns(3)
        col1.metric("📌 Total Records", len(utterances_df))
        col2.metric("🎯 Unique Utterances", utterances_df["transcript"].nunique())
        col3.metric("🗣️ Languages", utterances_df["language"].nunique())

        # Data Table with Search & Sorting
        st.subheader("📋 Data Table")
        st.dataframe(utterances_df)
