import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from .production_request import data_loader, safe_label

def read_sheedb_to_df() -> pd.DataFrame:
    """
    Fetch data from shee.db API endpoint and return it as a pandas DataFrame.

    Args:
        api_url (str): The full URL to the shee.db API endpoint.

    Returns:
        pd.DataFrame: DataFrame containing the data from the API.
    """
    api_url = st.secrets.get("SHEETDB_API_URL")
    response = requests.get(api_url)
    response.raise_for_status()  # raise error if request failed

    data_json = response.json()
    
    # shee.db API typically returns data in a 'results' or 'data' key, 
    # but you should adjust this based on the actual response structure
    # For example:
    # data = data_json.get('results') or data_json.get('data') or data_json

    # Example assuming data is directly the list of dicts
    data = data_json
    
    df = pd.DataFrame(data)
    return df

def dashboard():
    st.header("📊 Production Request Dashboard", divider="green")

    # Load stored data
    # df = data_loader(is_stored=True)
    df = read_sheedb_to_df()

    if df.empty:
        st.warning("No data available for dashboard.")
        return

    # Assuming column names match your Google Sheet
    name_col = "Your Name/ឈ្មោះអ្នកស្នើ"
    type_col = "ប្រភេទសំណើរ/Request type"
    room_col = "បន្ទប់/room"
    building_col = "អគា/building"
    zoon_col = "តំបន់/zoon"
    date_col = "Request Date"
    team_col = "ក្រុម/team"

    # Convert date column to datetime
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # --- Top Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("📌 Total Requests", df.shape[0])
    col2.metric("👤 Unique Users", df[name_col].nunique())
    busiest_date = df[date_col].value_counts().idxmax().strftime("%Y-%m-%d")
    col3.metric("📅 Busiest Date", busiest_date)

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("👥 Requests by User")
        user_counts = df[name_col].value_counts().reset_index()
        user_counts.columns = ["User", "Count"]
        user_counts["Count"] = user_counts["Count"].astype(int)
        st.bar_chart(user_counts.set_index("User"))
    with col2:
        st.subheader("📅 Requests by Date")
        requests_by_date = df[date_col].value_counts().reset_index()
        requests_by_date.columns = ["Date", "Count"]
        st.bar_chart(requests_by_date.set_index("Date"))
    with col3:
        st.subheader("📊 Requests by Team")
        requests_by_team = df[df.columns[1]].value_counts().reset_index()
        requests_by_team.columns = ["Team", "Count"]
        st.bar_chart(requests_by_team.set_index("Team"))
    st.divider()
    # --- Requests by Type ---
    st.subheader("📍 Requests by Type")
    type_count = df[type_col].value_counts().reset_index()
    type_count.columns = ["Type", "Count"]
    st.bar_chart(type_count.set_index("Type"))

    # --- Requests by Room, Building, Zone ---
    st.subheader("🏢 Requests by Room / Building / Zone")
    room_building_zoon = (
        df.groupby([room_col, building_col, zoon_col]).size().reset_index(name="Count")
    )
    fig_rbz = px.bar(
        room_building_zoon,
        x=room_col,
        y="Count",
        color=building_col,
        hover_data=[zoon_col],
        barmode="group",
    )
    st.plotly_chart(fig_rbz, use_container_width=True)

    # --- Requests over Time ---
    st.subheader("📆 Requests Over Time")
    daily_requests = df.groupby(date_col).size().reset_index(name="Count")
    fig_time = px.line(daily_requests, x=date_col, y="Count", markers=True)
    st.plotly_chart(fig_time, use_container_width=True)

    # --- Full Data ---
    show_data = st.checkbox("Show Data")

    if show_data:
        st.dataframe(df, use_container_width=True)



