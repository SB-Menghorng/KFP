# import streamlit as st
# import streamlit_authenticator as stauth
# from utils.google_sheets_client import GoogleSheetsClient

# def get_authenticator():

#     # --- Connect to Google Sheet ---
#     google = GoogleSheetsClient()
#     spreadsheet_id = google.extract_spreadsheet_id(st.secrets["system_data_stored"]["USERS"])
#     spreadsheet = google.open_sheet(spreadsheet_id)

#     worksheet_title = "user_login"
#     try:
#         worksheet = spreadsheet.worksheet(worksheet_title)
#     except Exception:
#         worksheet = spreadsheet.add_worksheet(title=worksheet_title, rows="100", cols="20")

#     columns = ["username", "email", "password"]
#     if worksheet.row_count == 0 or worksheet.row_values(1) != columns:
#         worksheet.insert_row(columns, index=1)

#     users = worksheet.get_all_records()

#     # --- Handle registration ---
#     if st.session_state.get("registering"):
#         username = st.session_state["register_username"]
#         email = st.session_state["register_email"]
#         raw_password = st.session_state["register_password"]

#         # Hash the password securely
#         hashed_password = stauth.Hasher([raw_password]).generate()[0]

#         # Append to Google Sheet
#         worksheet.append_row([username, email, hashed_password])

#         # Update local users list
#         users.append({"username": username, "email": email, "password": hashed_password})
#         st.session_state["registering"] = False
#         st.success(f"User {username} registered successfully!")

#     # --- Prepare credentials for authenticator ---
#     credentials = {
#         "usernames": {
#             user["username"]: {
#                 "name": user["username"],  # you can change to full name if needed
#                 "email": user["email"],
#                 "password": user["password"],  # hashed password
#             }
#             for user in users
#         }
#     }

#     # --- Initialize the authenticator ---
#     authenticator = stauth.Authenticate(
#         credentials,
#         cookie_name="kfp_auth_cookie",
#         key="abcdef",
#         cookie_expiry_days=1,
#     )

#     return authenticator, worksheet
