from datetime import date
from typing import Dict, List, Optional

import pandas as pd
import requests
import streamlit as st
from streamlit_option_menu import option_menu

from databases.production_request_form import ProductionRequestFormDB


class ProductionRequestForm:
    """Class to manage Production Request Form with Google Sheets and Streamlit."""

    def __init__(self):
        # Initialize DB connections
        self.db_stored = ProductionRequestFormDB(
            range_name="A:P",
            spreadsheet=st.secrets["SPREADSHEET_PRODUCTION_REQUEST_FORM_STORED"],
        )
        self.db_read = ProductionRequestFormDB(
            range_name="A:Q",
            spreadsheet=st.secrets["SPREADSHEET_PRODUCTION_REQUEST_FORM_READ"],
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

    @staticmethod
    def send_telegram_message(chat_ids: List[str], message: str) -> Dict[str, bool]:
        """Send a message to multiple Telegram chat IDs."""
        bot_token = st.secrets.get("TELEGRAM_TOKEN")
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        results = {}

        for chat_id in chat_ids:
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
            try:
                response = requests.post(url, data=payload)
                results[chat_id] = response.status_code == 200
            except Exception as e:
                results[chat_id] = False
                st.error(f"❌ Failed to send message to chat ID {chat_id}: {e}")
        return results

    # ------------------ Data Loading ------------------ #
    def load_data(self) -> pd.DataFrame:
        """Load spreadsheet data safely."""
        try:
            df = self.db_read.get_df()
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

        with st.form("production_request_form"):
            st.header(
                self.safe_label(questions(11), "Production Request Form"),
                divider="green",
            )

            # --- User input ---
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input(
                    self.safe_label(questions(0)), placeholder="Sam Vanthorn"
                )
            with col2:
                assigned_to = st.selectbox(
                    self.safe_label(questions(1), "Assign To"), self.get_list(df, 1)
                )

            col1, col2 = st.columns(2)
            with col1:
                request_date = st.date_input(
                    self.safe_label(questions(13), "Request Date *"), value=date.today()
                )
            with col2:
                to_date = st.date_input(
                    self.safe_label(questions(14), "To Date *"), value=date.today()
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
            col1, col2, col3 = st.columns(3)
            with col1:
                room = st.selectbox(
                    self.safe_label(questions(6), "Room *"), self.get_list(df, 6)
                )
            with col2:
                building = st.selectbox(
                    self.safe_label(questions(7), "Building *"), self.get_list(df, 7)
                )
            with col3:
                zoon = st.selectbox(
                    self.safe_label(questions(8), "Zoon *"), self.get_list(df, 8)
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
                    room,
                    building,
                    zoon,
                    contact,
                    request_date,
                    to_date,
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
        request_date,
        to_date,
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

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
            return

        st.success("Form submitted successfully!")

        # --- Handle image ---
        image_url = "—"
        if image is not None:
            try:
                # Example: Save image locally
                save_path = f"uploads/{username}_{image.name}"
                with open(save_path, "wb") as f:
                    f.write(image.getbuffer())
                image_url = save_path  # Or you could upload to cloud and use URL
            except Exception as e:
                st.warning(f"Failed to save image: {e}")

        # --- Prepare data for Google Sheet ---
        data = {
            f"{self.safe_label(questions(0), 'Name')}": username,
            f"{self.safe_label(questions(1), 'Assigned To')}": assigned_to,
            f"{self.safe_label(questions(2), 'Topic')}": selected_topic,
            f"{self.safe_label(questions(3), 'Description')}": (
                description if description.strip() else "—"
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
            "Image": image_url,
        }

        # --- Append to Google Sheet ---
        try:
            write_response = self.db_stored.append_row(data)
        except Exception as e:
            st.error(f"Failed to write data to sheet: {e}")

        # Optional: send Telegram message
        chat_ids = self.get_list(df, 10)
        message = f"New submission by {username}"
        self.send_telegram_message(chat_ids, message)
