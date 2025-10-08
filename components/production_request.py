import json
from datetime import date, time
from typing import Dict, List, Optional

import pandas as pd
import requests
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_tags import st_tags

from databases.production_request_form import (
    GoogleSheetsClient,
    ProductionRequestFormDB,
)


@st.cache_data(show_spinner="Loading production request data...", ttl=600)
def load_production_info_data():
    db = ProductionRequestFormDB(
        range_name="A:T",
        spreadsheet=st.secrets["SPREADSHEET_PRODUCTION_REQUEST_FORM_READ"],
    )
    df = db.get_df()
    return df


class ProductionRequestForm:
    """Class to manage Production Request Form with Google Sheets and Streamlit."""

    def __init__(self):
        # Initialize DB connections
        self.db_read = st.secrets["SPREADSHEET_PRODUCTION_REQUEST_FORM_READ"]
        self.db_write = st.secrets["SPREADSHEET_PRODUCTION_REQUEST_FORM_STORED"]
        self.db_stored = ProductionRequestFormDB(
            range_name="A:O",
            spreadsheet=self.db_write,
        )
        self.db_read = ProductionRequestFormDB(
            range_name="A:Q",
            spreadsheet=self.db_read,
        )

    # ------------------ Google Sheets / SheetDB ------------------ #
    @staticmethod
    def append_to_sheetdb(data_dict: dict) -> Optional[requests.Response]:
        """Append a new row to SheetDB via API."""
        if not isinstance(data_dict, dict):
            raise ValueError("data_dict must be a dictionary")
        api_url = st.secrets.get("SHEETDB_API_URL")
        if not api_url:
            st.error("Missing SHEETDB_API_URL in Streamlit secrets")
            return None

        payload = {"data": [data_dict]}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to append to SheetDB: {e}")
            return None

        return response

    def send_telegram_message(
        self, image_file, chat_ids: List[str], message: str
    ) -> Dict[str, bool]:
        bot_token = st.secrets.get("TELEGRAM_TOKEN")
        base_url = f"https://api.telegram.org/bot{bot_token}"
        results = {}

        # read file once into memory
        file_bytes = None
        if image_file is not None:
            file_bytes = image_file.read()
            image_file.seek(0)  # reset pointer so Streamlit can still use it

        for chat_id in chat_ids:
            try:
                # send text message
                resp = requests.post(
                    f"{base_url}/sendMessage",
                    data={
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "Markdown",
                    },
                )
                results[chat_id] = resp.status_code == 200

                # send image if provided
                if file_bytes:
                    files = {"photo": ("image.jpg", file_bytes)}
                    resp_img = requests.post(
                        f"{base_url}/sendPhoto",
                        data={"chat_id": chat_id},
                        files=files,
                    )

                    results[chat_id] = results[chat_id] and resp_img.status_code == 200

            except Exception as e:
                results[chat_id] = False
                st.error(f"❌ Failed to send message to chat ID {chat_id}: {e}")

        return results

    @staticmethod
    def format_request_message(questions: dict, data: dict) -> str:
        """Format the request data into a beautiful Telegram message."""
        lines = []
        lines.append("📌 *New Request Submitted*")
        lines.append("")
        lines.append(f"👤 *{questions(0)}*: {data.get(questions(0), '—')}")
        lines.append(f"📋 *{questions(1)}*: {data.get(questions(1), '—')}")
        lines.append(f"🏷️ *{questions(2)}*: {data.get(questions(2), '—')}")
        lines.append("")
        lines.append(f"📝 *{questions(3)}*:\n{data.get(questions(3), '—')}")
        lines.append("")
        lines.append(f"📦 *{questions(4)}*: {data.get(questions(4), '—')}")
        lines.append(f"🏠 *{questions(6)}*: {data.get(questions(6), '—')}")
        lines.append(f"🏢 *{questions(7)}*: {data.get(questions(7), '—')}")
        lines.append(f"📍 *{questions(8)}*: {data.get(questions(8), '—')}")
        lines.append(f"📞 *{questions(9)}*: {data.get(questions(9), '—')}")
        lines.append("")
        lines.append(f"📅 *{questions(13)}*: {data.get(questions(13), "-")}")
        lines.append(f"📅 *{questions(14)}*: {data.get(questions(14), '—')}")
        lines.append(f"⏰ *{questions(19)}*: {data.get(questions(19), '—')}")

        return "\n".join(lines)

    # ------------------ Data Loading ------------------ #
    def load_data(self) -> pd.DataFrame:
        """Load spreadsheet data safely."""
        try:
            df = load_production_info_data()
        except Exception as e:
            st.error(f"❌ Failed to read spreadsheet: {e}")
            st.stop()

        if df.empty:
            st.warning("⚠️ The loaded spreadsheet is empty.")
        return df

    # ------------------ Utility Methods ------------------ #
    @staticmethod
    def safe_label(value: Optional[str], default: str = "") -> str:
        return value.strip() if isinstance(value, str) and value.strip() else default

    @staticmethod
    def get_list(df: pd.DataFrame, col_index: int) -> List[str]:
        return df[df.columns[col_index]].dropna().unique().tolist()

    @staticmethod
    def get_form_question(df: pd.DataFrame, col: int) -> Optional[str]:
        try:
            return df.columns[col]
        except IndexError:
            return None

    # ------------------ Streamlit Form ------------------ #
    def render_form(self):
        df = self.load_data()
        questions = lambda x: self.get_form_question(df, x)

        # --- Reactive cascading selects (outside form) ---
        col1, col2, col3 = st.columns(3)
        with col1:
            df_new = df.iloc[:, [6, 7, 8]].copy()
            zoon = st.selectbox(
                self.safe_label(questions(8), "Zoon *"),
                self.get_list(df, 8),
                key="zoon",
            )

        with col2:
            filtered_buildings = df_new[df_new[questions(8)] == zoon][
                questions(7)
            ].unique()
            building = st.selectbox(
                self.safe_label(questions(7), "Building *"),
                sorted(filtered_buildings),
                key="building",
            )

        with col3:
            filtered_rooms = df_new[
                (df_new[questions(8)] == zoon) & (df_new[questions(7)] == building)
            ][questions(6)].unique()
            room = st.selectbox(
                self.safe_label(questions(6), "Room *"),
                sorted(filtered_rooms),
                key="room",
            )

        # --- Form starts here ---
        with st.form("production_request_form"):
            st.header(
                self.safe_label(questions(11), "Production Request Form"),
                divider="green",
            )

            # --- User input ---
            col1, col2 = st.columns(2)
            with col1:
                options = self.get_list(df, 0)
                username = st.selectbox(self.safe_label(questions(0)), options)
            with col2:
                assigned_to = st.selectbox(
                    self.safe_label(questions(1), "Assign To"), self.get_list(df, 1)
                )

            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                request_date = st.date_input(
                    self.safe_label(questions(13), "Request Date *"), value=date.today()
                )
            with col2:
                to_date = st.date_input(
                    self.safe_label(questions(14), "To Date *"), value=date.today()
                )
            with col3:
                time_to = st.time_input(
                    self.safe_label(questions(19), "Repair Time"), value=time(8, 0)
                )
            selected_topic = option_menu(
                menu_title=self.safe_label(questions(2), "Topic *"),
                options=self.get_list(df, 2)[:-1],
                styles={
                    "container": {"background-color": "#86e6864a"},
                    "nav-link": {
                        "font-size": "14px",
                        "color": "#333",
                        "background-color": "#ddd",
                        "border-radius": "5px",
                        "margin": "0 3px",
                    },
                    "nav-link-selected": {
                        "background-color": "#11B30CBA",
                        "color": "white",
                    },
                },
            )

            description = st.text_area(
                self.safe_label(questions(3), "Description *"), height=100
            )

            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input(
                    self.safe_label(questions(4), "Amount"),
                    min_value=1,
                    step=1,
                    placeholder="Enter amount",
                )
            with col2:
                unit = st.selectbox(
                    self.safe_label(questions(5), "Unit *"), self.get_list(df, 5)
                )

            # --- New: User image upload ---
            image = st.file_uploader(
                self.safe_label(questions(-1), "Upload Image"),
                type=["png", "jpg", "jpeg"],
            )

            contact = st.text_input(
                self.safe_label(questions(9), "Contact *"),
                placeholder="Enter contact information",
            )

            submitted = st.form_submit_button(
                self.safe_label(questions(12), "Submit"),
                use_container_width=True,
                type="primary",
            )

            if submitted:
                self.handle_submission(
                    df,
                    questions,
                    username,
                    assigned_to,
                    selected_topic,
                    description,
                    amount,
                    unit,
                    room,  # from outside form
                    building,  # from outside form
                    zoon,  # from outside form
                    contact,
                    request_date,
                    to_date,
                    time_to,
                    image,
                )

    # ------------------ Submission Handling ------------------ #
    def handle_submission(
        self,
        df,
        questions,
        username,
        assigned_to,
        selected_topic,
        description,
        amount,
        unit,
        room,
        building,
        zoon,
        contact,
        request_date: date,
        to_date: date,
        time_to: time,
        image=None,
    ):
        # --- Validate inputs ---
        errors = []
        if not username.strip():
            errors.append("Name is required.")
        if not request_date:
            errors.append("Request Date is required.")
        if not to_date:
            errors.append("To Date is required.")
        if not assigned_to:
            errors.append("Assigned To is required.")
        if not selected_topic:
            errors.append("Topic is required.")
        if amount <= 0:
            errors.append("Amount must be greater than zero.")
        if not unit:
            errors.append("Unit is required.")
        if not room:
            errors.append("Room is required.")
        if not building:
            errors.append("Building is required.")
        if not zoon:
            errors.append("Zoon is required.")
        if not contact.strip():
            errors.append("Contact information is required.")
        if not time_to:
            errors.append("To Tim is required")
        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
            return

        st.success("Form submitted successfully!")

        # --- Prepare data for Google Sheet ---
        data = {
            f"{self.safe_label(questions(0), 'Name')}": username,
            f"{self.safe_label(questions(1), 'Assigned To')}": assigned_to,
            f"{self.safe_label(questions(2), 'Topic')}": selected_topic,
            f"{self.safe_label(questions(3), 'Description')}": (
                description if description else "—"
            ),
            f"{self.safe_label(questions(4), 'Amount')}": f"{amount} {unit}",
            f"{self.safe_label(questions(6), 'Room')}": room,
            f"{self.safe_label(questions(7), 'Building')}": building,
            f"{self.safe_label(questions(8), 'Zoon')}": zoon,
            f"{self.safe_label(questions(9), 'Contact')}": contact,
            f"{self.safe_label(questions(13), 'Request Date')}": request_date.strftime(
                "%Y-%m-%d"
            ),
            f"{self.safe_label(questions(14), 'To Date')}": to_date.strftime(
                "%Y-%m-%d"
            ),
            f"{self.safe_label(questions(19), 'To Time')}": time_to.strftime(
                "%I:%M %p"
            ),
            "Image": image,
        }

        # --- Append to Google Sheet ---
        st.json(data)
        try:
            write_response = self.db_stored.append_row(
                data, lambda x: self.safe_label(questions(x))
            )
        except Exception as e:
            st.error(f"Failed to write data to sheet: {e}")

        # Optional: send Telegram message
        chat_ids = self.get_list(df, 10)
        message = self.format_request_message(
            lambda x: self.safe_label(questions(x)), data
        )
        file_id = self.send_telegram_message(image, chat_ids, message)
        st.info(f"file id: {file_id}")
