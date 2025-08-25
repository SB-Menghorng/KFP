import json
import re
import tempfile
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaFileUpload
import streamlit as st

class GoogleSheetsClient:
    def __init__(self, scopes: list[str] = None):
        if scopes is None:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
        self.creds = Credentials.from_service_account_info(
            json.loads(st.secrets["google_service_account"]["CREDENTIAL"]),
            scopes=scopes,
        )
        # Separate services for Sheets and Drive
        self.sheets_service = build("sheets", "v4", credentials=self.creds)
        self.drive_service = build("drive", "v3", credentials=self.creds)

    def get_service(self):
        """Return the Google Sheets API service object."""
        return self.sheets_service

    def open_sheet(self, spreadsheet_id: str):
        """Get spreadsheet metadata using the official API."""
        try:
            sheet = self.sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            return sheet
        except HttpError as error:
            st.error(f"An error occurred: {error}")
            return None

    def append_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: list[list],
        value_input_option="USER_ENTERED",
    ):
        """Append rows to the spreadsheet."""
        try:
            body = {"values": values}
            result = (
                self.sheets_service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )
            st.success(f"{result.get('updates').get('updatedCells')} cells appended.")
            return result
        except HttpError as error:
            st.error(f"An error occurred: {error}")
            return None

    @staticmethod
    def extract_spreadsheet_id(url_or_id: str) -> str:
        """Extract the spreadsheet ID from a URL or return the ID if given directly."""
        pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
        elif re.fullmatch(r"[a-zA-Z0-9-_]+", url_or_id):
            return url_or_id
        else:
            raise ValueError("Invalid Google Sheets URL or spreadsheet ID.")

    @staticmethod
    def extract_drive_id(url_or_id: str) -> str:
        """Extract a Drive folder/file ID from a URL or return the ID if given directly."""
        pattern = r"/(?:folders|file/d)/([a-zA-Z0-9-_]+)"
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
        elif re.fullmatch(r"[a-zA-Z0-9-_]+", url_or_id):
            return url_or_id
        else:
            raise ValueError("Invalid Google Drive URL or ID.")

    def upload_image_to_drive(self, uploaded_file, folder_id: str) -> str:
            """
            Upload an image (Streamlit UploadedFile) to a Google Drive folder in a Shared Drive.
            """
            try:
                # Save the uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_file_path = tmp_file.name

                file_metadata = {
                    "name": uploaded_file.name,
                    "parents": [folder_id],  # Folder ID inside the Shared Drive
                }
                st.write("file metadata", file_metadata)
                media = MediaFileUpload(tmp_file_path, mimetype=uploaded_file.type)

                file = (
                    self.drive_service.files()
                    .create(
                        body=file_metadata,
                        media_body=media,
                        fields="id, webViewLink",
                        supportsAllDrives=True  # Required for Shared Drives
                    )
                    .execute()
                )

                st.success(f"✅ Uploaded successfully: {file['webViewLink']}")
                return file["id"]

            except HttpError as error:
                st.error(f"❌ An error occurred: {error}")
                return None
