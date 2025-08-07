from datetime import date

import pandas as pd
import requests
import streamlit as st
from streamlit_chat import message
from streamlit_option_menu import option_menu

# Telegram bot token and chat_id
bot_token = "8222531296:AAGMXu5NWgde12aQ0BfMEMbE4uwZdp8W0sw"


# Load data from published Google Sheet CSV
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcBysyi5VzKi-4JkiIYCeMhkPTV6jcqIyzNXf3TS30rxY9JbrtwZd6KQxPJNrEHmj91PPC_D5PYCzo/pub?gid=0&single=true&output=csv"
df = pd.read_csv(url)

# Extract unique values for dropdowns
rooms = df["room"].dropna().unique().tolist()
buildings = df[df.columns[1]].dropna().unique().tolist()
topics = df[df.columns[2]].dropna().unique().tolist()
zoons = df[df.columns[3]].dropna().unique().tolist()
units = df[df.columns[4]].dropna().unique().tolist()
team_members = df[df.columns[5]].dropna().unique().tolist()
chat_ids = df[df.columns[6]].dropna().unique().tolist()
with st.form("production_request_form"):
    st.header("Production Request Form")

    # User info and assignment
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Your Name *")
    with col2:
        assigned_to = st.selectbox("Assign To", team_members)

    # Topic selection (horizontal menu)
    selected_topic = option_menu(
        menu_title="Topic *", options=topics, orientation="horizontal"
    )

    # Location selection: zoon, building, room
    col1, col2, col3 = st.columns(3)
    with col1:
        zoon = st.selectbox("Zoon *", zoons)
    with col2:
        building = st.selectbox("Building *", buildings)
    with col3:
        room = st.selectbox("Room *", rooms)

    # Value and unit input
    col1, col2 = st.columns([1, 2])
    with col1:
        value = st.number_input("Enter Value *", min_value=1, step=1)
    with col2:
        selected_unit = st.selectbox("Select Unit *", units)
        # If "Other", show custom unit input
        if selected_unit == "Other":
            custom_unit = st.text_input("Enter Custom Unit *")
            final_unit = custom_unit.strip()
        else:
            final_unit = selected_unit

    # Date, note, contact info
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_date = st.date_input("Select Date *", value=date.today())
    with col2:
        note = st.text_area("Note (Optional)")
    with col3:
        contact_user = st.text_input("Contact User *")
        email = st.text_input("Email (Optional)")
        phone = st.text_input("Phone Number (Optional)")

    # Submit button
    submitted = st.form_submit_button("Submit")

    if submitted:
        # Validation of required fields
        errors = []
        if not username.strip():
            errors.append("Your Name is required.")
        if not selected_topic:
            errors.append("Topic is required.")
        if not zoon:
            errors.append("Zoon is required.")
        if not building:
            errors.append("Building is required.")
        if not room:
            errors.append("Room is required.")
        if not value or value <= 0:
            errors.append("Value must be greater than zero.")
        if selected_unit == "Other" and (not final_unit):
            errors.append("Custom Unit is required when 'Other' is selected.")
        if not selected_date:
            errors.append("Date is required.")
        if not contact_user.strip():
            errors.append("Contact User is required.")

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
        else:
            st.success("Form submitted successfully!")
            # You can process/save form data here
            st.write(f"**Your Name:** {username}")
            st.write(f"**Assign To:** {assigned_to}")
            st.write(f"**Topic:** {selected_topic}")
            st.write(f"**Location:** Zoon: {zoon}, Building: {building}, Room: {room}")
            st.write(f"**Value:** {value} {final_unit}")
            st.write(f"**Date:** {selected_date}")
            if note.strip():
                st.write(f"**Note:** {note}")
            st.write(f"**Contact User:** {contact_user}")
            if email.strip():
                st.write(f"**Email:** {email}")
            if phone.strip():
                st.write(f"**Phone:** {phone}")
            # Format message
            telegram_message = f"""
            📝 *Production Request Submitted*:
            👤 *User:* {username}
            📥 *Assigned To:* {assigned_to}
            🗂️ *Topic:* {selected_topic}
            📍 *Location:* Zoon: {zoon}, Building: {building}, Room: {room}
            📦 *Value:* {value} {final_unit}
            📅 *Date:* {selected_date}
            🗒️ *Note:* {note if note.strip() else "None"}
            ☎️ *Contact User:* {contact_user}
            📧 *Email:* {email if email.strip() else "None"}
            📱 *Phone:* {phone if phone.strip() else "None"}
            """
            for id in chat_ids:
                # Send to Telegram
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": id,
                    "text": telegram_message,
                    "parse_mode": "Markdown",
                }

                response = requests.post(url, data=payload)

            if response.status_code != 200:
                st.error("❌ Failed to send message to Telegram.")
            else:
                st.info("✅ Sent to Telegram successfully!")
                
import google.generativeai as genai

# Configure your Gemini API key (from secrets.toml or environment)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash")  # Adjust model name as needed

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.form("chat_form"):
    user_input = st.text_input(
        "You:",
        value="",
        placeholder="Type here if you have any question",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Send")
form_info = """
You are an assistant helping users fill a Production Request Form. The form has the following fields:

- username (required): User's full name.
- assigned_to: Team member assigned to the task.
- topic (required): Topic of the request (e.g. Repair, Maintenance).
- zoon (required): Location zone.
- building (required): Building name.
- room (required): Room name.
- value (required): Numeric value greater than zero.
- unit (required): Measurement unit (kg, ton, Other). If "Other" is selected, a custom unit is required.
- date (required): Date of the request.
- note: Optional notes.
- contact_user (required): Contact person.
- email: Optional email.
- phone: Optional phone number.

Always validate required fields and confirm information with the user.
"""

if submitted and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input.strip()})
    try:
        response = model.generate_content(form_info + user_input.strip())
        reply = response.text.strip()
    except Exception as e:
        reply = f"⚠️ Error: {e}"
    st.session_state.messages.append({"role": "bot", "content": reply})
    st.rerun()

for msg in st.session_state.messages:
    role_icon = "🧑" if msg["role"] == "user" else "🤖"
    st.markdown(f"{role_icon} **{msg['role'].capitalize()}**: {msg['content']}")
