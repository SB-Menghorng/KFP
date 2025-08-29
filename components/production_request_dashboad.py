import pandas as pd
import plotly.express as px
import streamlit as st

from databases.production_request_form import ProductionRequestFormDB

from .production_request import ProductionRequestForm

prod_form = ProductionRequestForm()
get_form_questions = prod_form.get_form_question


class ProductionDashboard:
    """Class to handle production request dashboard visualizations."""

    def __init__(self):
        self.db = ProductionRequestFormDB(
            range_name="A:P",
            spreadsheet=st.secrets["SPREADSHEET_PRODUCTION_REQUEST_FORM_STORED"],
        )
        self.df = self.load_data()

    def load_data(self) -> pd.DataFrame:
        """Load data from Google Sheets safely."""
        try:
            df = self.db.get_df()
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            return pd.DataFrame()

        if df.empty:
            st.warning("No data available.")
            return df

        # Convert date column to datetime safely
        date_col = get_form_questions(df, 13)
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d", errors="coerce")
        return df

    def render_metrics(self):
        """Display top metrics at the top of the dashboard."""
        if self.df.empty:
            return

        df = self.df
        name_col = get_form_questions(df, 0)
        date_col = get_form_questions(df, 13)

        col1, col2, col3 = st.columns(3)
        col1.metric("📌 Total Requests", df.shape[0])
        col2.metric("👤 Unique Users", df[name_col].nunique())
        try:
            busiest_date = df[date_col].value_counts().idxmax().strftime("%Y-%m-%d")
            col3.metric("📅 Busiest Date", busiest_date)
        except Exception:
            col3.metric("📅 Busiest Date", "N/A")
        st.divider()

    def render_charts(self):
        """Render charts for requests by user, date, team, type, and room/building/zone."""
        if self.df.empty:
            return

        df = self.df
        name_col = get_form_questions(df, 0)
        type_col = get_form_questions(df, 1)
        team_col = get_form_questions(df, 6)
        room_col = get_form_questions(df, 2)
        building_col = get_form_questions(df, 3)
        zoon_col = get_form_questions(df, 4)
        date_col = get_form_questions(df, 13)

        # Requests by User / Date / Team
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("👥 Requests by User")
            user_counts = df[name_col].value_counts().reset_index()
            user_counts.columns = ["User", "Count"]
            st.bar_chart(user_counts.set_index("User"))

        with col2:
            st.subheader("📅 Requests by Date")
            date_counts = df[date_col].value_counts().sort_index().reset_index()
            date_counts.columns = ["Date", "Count"]
            st.bar_chart(date_counts.set_index("Date"))

        with col3:
            st.subheader("📊 Requests by Team")
            team_counts = df[team_col].value_counts().reset_index()
            team_counts.columns = ["Team", "Count"]
            st.bar_chart(team_counts.set_index("Team"))

        st.divider()

        # Requests by Type
        st.subheader("📍 Requests by Type")
        type_counts = df[type_col].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        st.bar_chart(type_counts.set_index("Type"))

        # Requests by Room / Building / Zone
        st.subheader("🏢 Requests by Room / Building / Zone")
        df_rbz = (
            df.groupby([room_col, building_col, zoon_col])
            .size()
            .reset_index(name="Count")
        )
        fig_rbz = px.bar(
            df_rbz,
            x=room_col,
            y="Count",
            color=building_col,
            hover_data=[zoon_col],
            barmode="group",
            title="Requests by Room / Building / Zone",
        )
        st.plotly_chart(fig_rbz, use_container_width=True)

        # Requests over time
        st.subheader("📆 Requests Over Time")
        df_time = df.groupby(date_col).size().reset_index(name="Count")
        fig_time = px.line(
            df_time, x=date_col, y="Count", markers=True, title="Requests Over Time"
        )
        st.plotly_chart(fig_time, use_container_width=True)

    def render_data_table(self):
        """Optionally display full dataframe for exploration."""
        if self.df.empty:
            return

        show_data = st.checkbox("Show Full Data")
        if show_data:
            st.dataframe(self.df, use_container_width=True)
        st.dataframe(pd.DataFrame({"Column Name": self.df.columns}))

    def render_dashboard(self):
        """Render full dashboard with metrics, charts, and data table."""
        st.header("📊 Production Request Dashboard", divider="green")
        self.render_metrics()
        self.render_charts()
        self.render_data_table()
