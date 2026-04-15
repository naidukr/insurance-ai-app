# Monitoring Dashboard Component for Streamlit
# Add this to your app.py to include monitoring metrics

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

def render_monitoring_dashboard(api_base_url="http://localhost:8000"):
    """
    Render monitoring dashboard in Streamlit
    Call this function in your main app.py
    """

    st.header("📊 Application Monitoring Dashboard")

    # Create tabs for different monitoring views
    tab1, tab2, tab3, tab4 = st.tabs(["Health", "Performance", "Usage", "System"])

    with tab1:
        render_health_tab(api_base_url)

    with tab2:
        render_performance_tab(api_base_url)

    with tab3:
        render_usage_tab(api_base_url)

    with tab4:
        render_system_tab(api_base_url)

def render_health_tab(api_base_url):
    """Render application health metrics"""
    st.subheader("Application Health")

    try:
        # Get health status from backend
        response = requests.get(f"{api_base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()

            # Status indicators
            col1, col2, col3 = st.columns(3)

            with col1:
                status = "🟢 Healthy" if health_data.get("status") == "healthy" else "🔴 Issues"
                st.metric("Application Status", status)

            with col2:
                version = health_data.get("version", "Unknown")
                st.metric("Version", version)

            with col3:
                uptime = health_data.get("timestamp", "Unknown")
                st.metric("Last Check", uptime[:19] if uptime != "Unknown" else "Unknown")

            # Observability status
            st.subheader("Observability Status")
            obs_data = health_data.get("observability", {})

            obs_col1, obs_col2 = st.columns(2)

            with obs_col1:
                langsmith_status = "✅ Enabled" if obs_data.get("langsmith", {}).get("enabled") else "⚠️ Disabled"
                st.metric("LangSmith Tracing", langsmith_status)

            with obs_col2:
                app_insights_status = "✅ Enabled" if obs_data.get("application_insights", {}).get("enabled") else "⚠️ Disabled"
                st.metric("Azure App Insights", app_insights_status)

        else:
            st.error(f"Failed to fetch health data: {response.status_code}")

    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        st.info("Make sure the FastAPI backend is running on the configured port")

def render_performance_tab(api_base_url):
    """Render performance metrics"""
    st.subheader("Performance Metrics")

    # Mock performance data (replace with real metrics from your backend)
    performance_data = {
        "metric": ["Avg Response Time", "P95 Response Time", "Error Rate", "RAG Latency"],
        "value": [2.3, 5.1, 0.8, 1.8],
        "unit": ["seconds", "seconds", "%", "seconds"]
    }

    df_perf = pd.DataFrame(performance_data)

    # Performance metrics cards
    cols = st.columns(len(df_perf))
    for i, col in enumerate(cols):
        with col:
            st.metric(
                df_perf.iloc[i]["metric"],
                f"{df_perf.iloc[i]['value']} {df_perf.iloc[i]['unit']}"
            )

    # Performance trends chart
    st.subheader("Response Time Trends (Last 24h)")

    # Generate mock time series data
    now = datetime.now()
    time_range = [now - timedelta(hours=i) for i in range(24, 0, -1)]
    mock_response_times = [2.0 + 0.5 * (i % 3) for i in range(24)]

    fig = px.line(
        x=time_range,
        y=mock_response_times,
        title="Average Response Time",
        labels={"x": "Time", "y": "Response Time (seconds)"}
    )
    st.plotly_chart(fig, use_container_width=True)

def render_usage_tab(api_base_url):
    """Render usage analytics"""
    st.subheader("Usage Analytics")

    # Mock usage data
    usage_data = {
        "metric": ["Total Chat Requests", "Documents Processed", "Active Users", "Avg Session Length"],
        "value": [1250, 89, 23, 12.5],
        "change": [15.2, 8.7, -2.1, 5.3],
        "unit": ["requests", "documents", "users", "minutes"]
    }

    df_usage = pd.DataFrame(usage_data)

    # Usage metrics with trend indicators
    cols = st.columns(2)
    for i in range(len(df_usage)):
        with cols[i % 2]:
            delta = df_usage.iloc[i]["change"]
            delta_color = "normal" if delta >= 0 else "inverse"
            st.metric(
                df_usage.iloc[i]["metric"],
                f"{df_usage.iloc[i]['value']} {df_usage.iloc[i]['unit']}",
                delta=f"{delta:+.1f}%",
                delta_color=delta_color
            )

    # Usage trends
    st.subheader("Chat Activity (Last 7 days)")

    dates = pd.date_range(end=datetime.now(), periods=7)
    chat_counts = [45, 52, 38, 67, 71, 58, 63]

    fig = px.bar(
        x=dates,
        y=chat_counts,
        title="Daily Chat Requests",
        labels={"x": "Date", "y": "Requests"}
    )
    st.plotly_chart(fig, use_container_width=True)

def render_system_tab(api_base_url):
    """Render system/infrastructure metrics"""
    st.subheader("System Health")

    # Memory system status
    try:
        response = requests.get(f"{api_base_url}/api/memory/health", timeout=5)
        if response.status_code == 200:
            memory_data = response.json()

            col1, col2, col3 = st.columns(3)

            with col1:
                backend = memory_data.get("backend", "Unknown")
                st.metric("Memory Backend", backend)

            with col2:
                conversations = memory_data.get("conversations", 0)
                st.metric("Active Conversations", conversations)

            with col3:
                status = memory_data.get("status", "Unknown")
                status_icon = "🟢" if status == "healthy" else "🟡" if status == "fallback" else "🔴"
                st.metric("Memory Status", f"{status_icon} {status}")

            # Show warning if using fallback
            if memory_data.get("warning"):
                st.warning(f"⚠️ {memory_data['warning']}")

        else:
            st.error("Failed to fetch memory health data")

    except Exception as e:
        st.error(f"Error fetching memory status: {str(e)}")

    # System resources (mock data - replace with real system metrics)
    st.subheader("System Resources")

    system_data = {
        "Component": ["FastAPI Backend", "Streamlit Frontend", "Redis Memory", "FAISS Vector Store"],
        "Status": ["Running", "Running", "Connected", "Loaded"],
        "CPU %": [15.2, 8.7, 3.1, 2.4],
        "Memory MB": [245, 189, 67, 123]
    }

    df_system = pd.DataFrame(system_data)
    st.dataframe(df_system, use_container_width=True)

# Example usage in app.py:
"""
# Add this to your app.py file

from monitoring_dashboard import render_monitoring_dashboard

# In your main function or sidebar
if st.sidebar.checkbox("Show Monitoring Dashboard"):
    render_monitoring_dashboard()
"""