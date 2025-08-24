from datetime import date

import pandas as pd
import requests
import streamlit as st
from streamlit_option_menu import option_menu
from databases.production_request_form import ProductionRequestFormDB

db = ProductionRequestFormDB(range_name="A:O")
def append_to_sheetdb(data_dict):
    """
    Append a new row to the SheetDB.io sheet via API.

    Args:
        data_dict (dict): The data to append as a new row,
                          keys must match the column names in the sheet.

    Returns:
        requests.Response: The HTTP response object from the API.
    """
    if not isinstance(data_dict, dict):
        raise ValueError("data_dict must be a dictionary")

    api_url = st.secrets.get("SHEETDB_API_URL")
    if not api_url:
        raise ValueError("Missing SHEETDB_API_URL in Streamlit secrets")

    headers = {"Content-Type": "application/json"}
    payload = {"data": [data_dict]}  # SheetDB expects data inside a list under "data"

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception for 4xx/5xx
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Failed to append to SheetDB: {e}")
        return None

    return response


def send_telegram_message(chat_ids: list, message: str) -> dict:
    """
    Send a message to multiple Telegram chat IDs.

    Args:
        chat_ids (list): List of chat IDs (integers or strings).
        message (str): Message text in Markdown format.

    Returns:
        dict: A dictionary with chat_id as key and success status (True/False) as value.
    """
    bot_token = st.secrets.get("TELEGRAM_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    results = {}

    for chat_id in chat_ids:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",  # Use "MarkdownV2" if needed with proper escaping
        }
        try:
            response = requests.post(url, data=payload)
            results[chat_id] = response.status_code == 200
        except Exception as e:
            results[chat_id] = False
            st.error(f"❌ Failed to send message to chat ID {chat_id}: {e}")
    return results


@st.cache_data
def data_loader(is_stored: bool = False) -> pd.DataFrame:
    """Load spreadsheet data from Streamlit secrets with safety checks."""
    if is_stored:
        url = st.secrets.get("SPREADSHEET_DATA_STORED_URL")
    else:
        url = st.secrets.get("SPREADSHEET_URL")

    # 1. Check if the secret exists
    if not url:
        st.error("❌ Missing SPREADSHEET_URL in Streamlit secrets.")
        st.stop()  # Prevents the rest of the app from running

    # 2. Try reading the file, catch errors
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"❌ Failed to read spreadsheet from URL: {e}")
        st.stop()

    # 3. Optional: sanity check for empty DataFrame
    if df.empty:
        st.warning("⚠️ The loaded spreadsheet is empty.")

    return df


def get_form_questions(df: pd.DataFrame, col: int):
    try:
        return df.columns[col]
    except IndexError:
        return None


def safe_label(value, default=""):
    if isinstance(value, str) and value.strip():
        return value
    else:
        return default


def get_list(df: pd.DataFrame, col_index: int) -> list:
    return df[df.columns[col_index]].dropna().unique().tolist()


def request_form():
    questions = lambda x: get_form_questions(df, x)
    df = data_loader()

    with st.form("production_request_form"):

        st.header(safe_label(questions(11), "Production Request Form"), divider="green")

        col1, col2 = st.columns(2, border=True)

        with col1:
            username = st.text_input(
                safe_label(questions(0)), placeholder="Sam Vanthorn"
            )

        with col2:
            assigned_to = st.selectbox(
                safe_label(questions(1), "Assign To"),
                get_list(df, 1),
            )

        col1, col2 = st.columns(2, border=True)

        with col1:
            request_date = st.date_input(
                safe_label(questions(13), "Request Date *"), value=date.today()
            )
        with col2:
            to_date = st.date_input(
                safe_label(questions(14), "To Date *"), value=date.today()
            )
        selected_topic = option_menu(
            menu_title=safe_label(questions(2), "Topic *"),
            options=get_list(df, 2),
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
            safe_label(questions(3), "Description *"), height=100
        )

        col1, col2 = st.columns(2, border=True)

        with col1:
            amount = st.number_input(
                safe_label(questions(4), "Amount"),
                min_value=1,
                step=1,
                placeholder="Enter amount",
            )
        with col2:
            unit = st.selectbox(safe_label(questions(5), "Unit *"), get_list(df, 5))

        col1, col2, col3 = st.columns(3, border=True)

        with col1:
            room = st.selectbox(safe_label(questions(6), "Room *"), get_list(df, 6))

        with col2:
            building = st.selectbox(
                safe_label(questions(7), "Building *"), get_list(df, 7)
            )

        with col3:
            zoon = st.selectbox(safe_label(questions(8), "Zoon *"), get_list(df, 8))

        contact = st.text_input(
            safe_label(questions(9), "Contact *"),
            placeholder="Enter contact information",
        )

        submitted = st.form_submit_button(
            safe_label(questions(12), "Submit"),
            use_container_width=True,
            type="primary",
        )

        if submitted:
            errors = []

            # Step 1: Basic validation
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
            else:
                st.success("Form submitted successfully!")
                data = {
                    f"{safe_label(questions(0), 'Name')}": username,
                    f"{safe_label(questions(1), 'Assigned To')}": assigned_to,
                    f"{safe_label(questions(2), 'Topic')}": selected_topic,
                    f"{safe_label(questions(3), 'Description')}": (
                        description if description.strip() else "—"
                    ),
                    f"{safe_label(questions(4), 'Amount')}": f"{amount} {unit}",
                    f"{safe_label(questions(5), 'Room')}": room,
                    f"{safe_label(questions(6), 'Building')}": building,
                    f"{safe_label(questions(8), 'Zoon')}": zoon,
                    f"{safe_label(questions(9), 'Contact')}": contact,
                    f"{safe_label(questions(13), 'Request Date')}": request_date.strftime(
                        "%Y-%m-%d"
                    ),
                    f"{safe_label(questions(14), 'To Date')}": to_date.strftime(
                        "%Y-%m-%d"
                    ),
                }

                try:
                    # st.json(data)
                    write_to_sheet = db.append_row(data)
                    st.write(write_to_sheet)
                except Exception as e:
                    st.error(f"Failed to write data to sheet: {e}")
                # if write_to_sheet.status_code == 200:
                #     st.success("Data written to sheet successfully!")
                # else:
                #     st.error("Failed to write data to sheet.")

                receipt_html = f"""
                <div style="
                    border: 1.5px solid #4CAF50;
                    border-radius: 12px;
                    padding: 20px;
                    background-color: #f9fff9;
                    max-width: 700px;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    color: #333;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    margin-top: 20px;
                ">
                    <h3 style="color: #2E7D32; margin-bottom: 15px;">📄 {safe_label(questions(13), 'Submission Receipt')}</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tbody>
                            <tr>
                                <td style="padding: 8px; font-weight: 600; width: 30%;">{safe_label(questions(0), 'Name')}</td>
                                <td style="padding: 8px;">{username}</td>
                            </tr>
                            <tr style="background-color: #e8f5e9;">
                                <td style="padding: 8px; font-weight: 600;">{safe_label(questions(1), 'Assigned To')}</td>
                                <td style="padding: 8px;">{assigned_to}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: 600;">{safe_label(questions(2), 'Topic')}</td>
                                <td style="padding: 8px;">{selected_topic}</td>
                            </tr>
                            <tr style="background-color: #e8f5e9;">
                                <td style="padding: 8px; font-weight: 600;">{safe_label(questions(3), 'Description')}</td>
                                <td style="padding: 8px;">{description if description.strip() else '—'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: 600;">{safe_label(questions(4), 'Amount')}</td>
                                <td style="padding: 8px;">{amount} {unit}</td>
                            </tr>
                            <tr style="background-color: #e8f5e9;">
                                <td style="padding: 8px; font-weight: 600;">{safe_label(questions(6), 'Room')}</td>
                                <td style="padding: 8px;">{room}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: 600;">{safe_label(questions(7), 'Building')}</td>
                                <td style="padding: 8px;">{building}</td>
                            </tr>
                            <tr style="background-color: #e8f5e9;">
                                <td style="padding: 8px; font-weight: 600;">{safe_label(questions(8), 'Zoon')}</td>
                                <td style="padding: 8px;">{zoon}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: 600;">{safe_label(questions(9), 'Contact')}</td>
                                <td style="padding: 8px;">{contact}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """

                st.markdown(receipt_html, unsafe_allow_html=True)

                telegram_message = (
                    f"📄 *Submission Receipt*\n"
                    f"👤 *{safe_label(questions(0), 'Name')}:* {username}\n"
                    f"🧑‍💼 *{safe_label(questions(1), 'Assigned To')}:* {assigned_to}\n"
                    f"📚 *{safe_label(questions(2), 'Topic')}:* {selected_topic}\n"
                    f"📝 *{safe_label(questions(3), 'Description')}:* {description if description.strip() else '—'}\n"
                    f"🔢 *{safe_label(questions(4), 'Amount')}:* {amount} {unit}\n"
                    f"🚪 *{safe_label(questions(6), 'Room')}:* {room}\n"
                    f"🏢 *{safe_label(questions(7), 'Building')}:* {building}\n"
                    f"📍 *{safe_label(questions(8), 'Zoon')}:* {zoon}\n"
                    f"📞 *{safe_label(questions(9), 'Contact')}:* {contact}"
                )

                # send_to_telegram = send_telegram_message(
                #     chat_ids=get_list(
                #         df, 10
                #     ),  # Assuming chat IDs are in the 10th column
                #     message=telegram_message,
                # )

                # if send_to_telegram:
                #     st.success("Telegram message sent successfully!")
                # else:
                #     st.error("Failed to send Telegram message.")

    # st.dataframe(pd.DataFrame({"Column Name": df.columns}))