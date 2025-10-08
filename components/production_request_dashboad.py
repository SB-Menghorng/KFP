import pandas as pd
import plotly.express as px
import streamlit as st

from databases.production_request_form import ProductionRequestFormDB

from .production_request import ProductionRequestForm

prod_form = ProductionRequestForm()
get_form_questions = prod_form.get_form_question


@st.cache_data(show_spinner="Loading production request data...", ttl=3600)
def load_production_request_data():
    db = ProductionRequestFormDB(
        range_name="A:P",
        spreadsheet=st.secrets["SPREADSHEET_PRODUCTION_REQUEST_FORM_STORED"],
    )
    df = db.get_df()
    return df

@st.cache_data(show_spinner="Loading production request data...", ttl=3600)
def load_production_info_data():
    db = ProductionRequestFormDB(
            range_name="A:P",
            spreadsheet=st.secrets["SPREADSHEET_PRODUCTION_REQUEST_FORM_READ"],
            sheet_name="dashboard",
        )
    df = db.get_df()
    return df

def normalize_dates(df, date_col):
    # Convert all to string first (to avoid weird mixed-type issues)
    df[date_col] = df[date_col].astype(str).str.strip()

    # Detect Excel-style numbers (like "45938")
    is_numeric = df[date_col].str.match(r"^\d+(\.\d+)?$")

    # Split numeric vs text for safe conversion
    numeric_part = df.loc[is_numeric, date_col].astype(float)
    text_part = df.loc[~is_numeric, date_col]

    # Convert numeric (Excel serial) to datetime
    converted_numeric = pd.to_datetime("1899-12-30") + pd.to_timedelta(
        numeric_part, unit="D"
    )

    # Convert text (normal date strings) to datetime
    converted_text = pd.to_datetime(text_part, errors="coerce")

    # Combine both back into one column
    df.loc[is_numeric, date_col] = converted_numeric
    df.loc[~is_numeric, date_col] = converted_text

    # Final cleanup
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    return df


class ProductionDashboard:
    """Class to handle production request dashboard visualizations."""

    def __init__(self):
        self.db = ProductionRequestFormDB(
            range_name="A:P",
            spreadsheet=st.secrets["SPREADSHEET_PRODUCTION_REQUEST_FORM_STORED"],
        )
        self.db_read = ProductionRequestFormDB(
            range_name="A:P",
            spreadsheet=st.secrets["SPREADSHEET_PRODUCTION_REQUEST_FORM_READ"],
            sheet_name="dashboard",
        )
        self.df = load_production_request_data()

    def title(self, x):
        df = load_production_info_data()
        return df.iloc[x, 0]

    def load_data(self) -> pd.DataFrame:
        """Load data from Google Sheets safely."""
        try:
            df = load_production_request_data()
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            return pd.DataFrame()

        if df.empty:
            st.warning("No data available.")
            return df

        # Convert date column to datetime safely
        date_col = get_form_questions(df, 13)
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(
                df[date_col], format="%Y-%m-%d", errors="coerce"
            )
        return df

    def render_metrics(self):
        """Display top metrics at the top of the dashboard."""
        title = self.title
        if self.df.empty:
            return

        df = self.df
        name_col = get_form_questions(df, 0)
        date_col = get_form_questions(df, 14)

        total_requests = df.shape[0]
        unique_users = df[name_col].nunique()

        df = normalize_dates(df, date_col)

        try:
            busiest_date = df[date_col].value_counts().idxmax().strftime("%Y-%m-%d")
        except Exception:
            busiest_date = "N/A"

        col1, col2, col3 = st.columns(3)
        col1.metric(title(0), total_requests)
        col2.metric(title(1), unique_users)
        col3.metric(title(2), busiest_date)
        st.divider()

    def render_charts(self):
        """Render charts for requests with multiple analysis views."""
        if self.df.empty:
            return

        df = self.df.copy()
        name_col = get_form_questions(df, 0)
        type_col = get_form_questions(df, 1)
        team_col = get_form_questions(df, 2)
        room_col = get_form_questions(df, 6)
        building_col = get_form_questions(df, 7)
        zone_col = get_form_questions(df, 8)
        date_col = get_form_questions(df, 14)

        # Ensure datetime
        # df = normalize_dates(df, date_col)

        st.subheader("📅 Select Date Range")

        start_date, end_date = st.date_input(
            "Filter by date:",
            value=[df[date_col].min(), df[date_col].max()],
            min_value=df[date_col].min(),
            max_value=df[date_col].max(),
        )

        df = df[
            (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
        ]

        # ------------------ Tabs ------------------ #
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "Overview",
                "By Type",
                "Room/Building/Zone",
                "Trends",
                "Heatmap",
                "Retention",
            ]
        )

        # ------------------ Overview ------------------ #
        with tab1:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("👥 Requests by User")
                user_counts = df[name_col].value_counts().reset_index(name="User")
                st.bar_chart(user_counts.set_index("User"))
                if st.checkbox("Show user data", key="user"):
                    st.dataframe(user_counts)

            with col2:
                st.subheader("📅 Requests by Date")
                date_counts = (
                    df[date_col].value_counts().sort_index().reset_index(name="Date")
                )
                st.bar_chart(date_counts.set_index("Date"))
                if st.checkbox("Show date data", key="date"):
                    st.dataframe(date_counts)

            with col3:
                st.subheader("📊 Requests by Team")
                team_counts = df[team_col].value_counts().reset_index(name="Team")
                st.bar_chart(team_counts.set_index("Team"))
                if st.checkbox("Show team data", key="team"):
                    st.dataframe(team_counts)

        # ------------------ Requests by Type ------------------ #
        with tab2:
            st.subheader("📍 Requests by Type")
            type_counts = df[type_col].value_counts().reset_index(name="Type")
            st.bar_chart(type_counts.set_index("Type"))
            if st.checkbox("Show type data"):
                st.dataframe(type_counts)

        # ------------------ Flexible Grouping ------------------ #
        with tab3:
            st.subheader("🏢 Requests by Room / Building / Zone")
            group_choice = st.radio(
                "Group requests by:",
                ["Room", "Building", "Zone", "All Available"],
                horizontal=True,
            )

            if group_choice == "Room":
                df_group = df.groupby(room_col).size().reset_index(name="Count")
                fig_group = px.bar(
                    df_group, x=room_col, y="Count", title="Requests by Room"
                )

            elif group_choice == "Building":
                df_group = df.groupby(building_col).size().reset_index(name="Count")
                fig_group = px.bar(
                    df_group, x=building_col, y="Count", title="Requests by Building"
                )

            elif group_choice == "Zone":
                df_group = df.groupby(zone_col).size().reset_index(name="Count")
                fig_group = px.bar(
                    df_group, x=zone_col, y="Count", title="Requests by Zone"
                )

            else:  # All Available
                df_group = (
                    df.groupby([room_col, building_col, zone_col])
                    .size()
                    .reset_index(name="Count")
                )
                fig_group = px.bar(
                    df_group,
                    x=room_col,
                    y="Count",
                    color=building_col,
                    hover_data=[zone_col],
                    barmode="group",
                    title="Requests by Room / Building / Zone",
                )

            st.plotly_chart(fig_group, use_container_width=True)
            if st.checkbox("Show grouped data"):
                st.dataframe(df_group)

        # ------------------ Trends ------------------ #
        with tab4:
            st.subheader("📆 Requests Over Time")
            df_time = df.groupby(date_col).size().reset_index(name="Count")
            fig_time = px.line(
                df_time, x=date_col, y="Count", markers=True, title="Requests Over Time"
            )
            st.plotly_chart(fig_time, use_container_width=True)

            # Cumulative
            df_time["Cumulative"] = df_time["Count"].cumsum()
            fig_cum = px.line(
                df_time,
                x=date_col,
                y="Cumulative",
                title="Cumulative Requests Over Time",
            )
            st.plotly_chart(fig_cum, use_container_width=True)

            # Moving average
            df_time["7d_avg"] = df_time["Count"].rolling(7, min_periods=1).mean()
            fig_trend = px.line(
                df_time,
                x=date_col,
                y=["Count", "7d_avg"],
                labels={"value": "Requests", "variable": "Metric"},
                title="Requests with 7-day Moving Average",
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            if st.checkbox("Show time data"):
                st.dataframe(df_time)

        # ------------------ Heatmap ------------------ #
        with tab5:
            st.subheader("🔥 Requests by Day of Week & Hour")
            if pd.api.types.is_datetime64_any_dtype(df[date_col]):
                df["weekday"] = df[date_col].dt.day_name()
                df["hour"] = df[date_col].dt.hour
                heatmap = (
                    df.groupby(["weekday", "hour"]).size().reset_index(name="Count")
                )
                fig_heatmap = px.density_heatmap(
                    heatmap,
                    x="hour",
                    y="weekday",
                    z="Count",
                    title="Requests by Day of Week & Hour",
                    nbinsx=24,
                    color_continuous_scale="Viridis",
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
                if st.checkbox("Show heatmap data"):
                    st.dataframe(heatmap)

        # ------------------ Retention ------------------ #
        with tab6:
            st.subheader("🔁 User Retention")
            requester_freq = df[name_col].value_counts()
            one_time = (requester_freq == 1).sum()
            repeat = (requester_freq > 1).sum()

            st.write(f"One-time requesters: {one_time}")
            st.write(f"Repeat requesters: {repeat}")
            fig_ret = px.pie(
                names=["One-time", "Repeat"],
                values=[one_time, repeat],
                title="User Retention",
            )
            st.plotly_chart(fig_ret, use_container_width=True)

    def render_data_table(self):
        """Display dataframe with interactive exploration options."""
        if self.df.empty:
            st.info("No data available to display.")
            return

        with st.expander("🔍 Explore Data"):
            view_option = st.radio(
                "Choose view:",
                ["Preview", "Full Data", "Column Overview"],
                horizontal=True,
            )

            if view_option == "Preview":
                st.dataframe(self.df.head(10), use_container_width=True)
                st.caption(f"Showing first 10 of {len(self.df)} rows.")

            elif view_option == "Full Data":
                st.dataframe(self.df, use_container_width=True)

            elif view_option == "Column Overview":
                st.table(
                    pd.DataFrame(
                        {
                            "Column Name": self.df.columns,
                            "Data Type": [str(dtype) for dtype in self.df.dtypes],
                            "Non-Null Count": [
                                self.df[col].notnull().sum() for col in self.df.columns
                            ],
                        }
                    )
                )

    def render_dashboard(self):
        """Render full dashboard with metrics, charts, and data table."""
        st.header("📊 Production Request Dashboard", divider="green")
        self.render_metrics()
        self.render_charts()
        self.render_data_table()
