import json
import os
import re
import tempfile
from typing import List, Optional

import streamlit as st
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request


class GoogleSheetsClient:
    def __init__(
        self,
        scopes: Optional[List[str]] = None,
        service_account: bool = True,
        spreadsheet_url: str = None,
        token_range: str = "Token!A1"
    ):
        if scopes is None:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]


        if service_account:
            # ✅ Just use service account creds directly
            self.creds = ServiceAccountCredentials.from_service_account_info(
                json.loads(st.secrets["google_service_account"]["CREDENTIAL"]),
                scopes=scopes,
            )

        else:
            self.spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_url)
            self.token_range = token_range
            self.creds = None
            # ✅ Use service account ONLY to read/write the token cell
            service_creds = ServiceAccountCredentials.from_service_account_info(
                json.loads(st.secrets["google_service_account"]["CREDENTIAL"]),
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            sheet_service = build("sheets", "v4", credentials=service_creds)

            # 1. Try to load token from Google Sheet
            result = sheet_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.token_range
            ).execute()
            values = result.get("values", [])

            if values and values[0] and values[0][0]:
                try:
                    token_json = values[0][0]
                    self.creds = ServiceAccountCredentials.from_authorized_user_info(json.loads(token_json), scopes)
                except Exception:
                    self.creds = None

            # 2. If no valid creds → run OAuth flow
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    client_config = json.loads(st.secrets["google_api"]["CREDENTIALS_GOOGLE_API"])
                    flow = InstalledAppFlow.from_client_config(client_config, scopes)
                    self.creds = flow.run_local_server(port=0)

                # Save new token JSON into Google Sheet
                sheet_service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=self.token_range,
                    valueInputOption="RAW",
                    body={"values": [[self.creds.to_json()]]}
                ).execute()

        # 3. Build final services
        self.sheets_service = build("sheets", "v4", credentials=self.creds)
        self.drive_service = build("drive", "v3", credentials=self.creds)

        # Separate services for Sheets and Drive
        self.sheets_service = build("sheets", "v4", credentials=self.creds)
        self.drive_service = build("drive", "v3", credentials=self.creds)

    def get_service(self):
        """Return the Google Sheets API service object."""
        return self.sheets_service

    def open_sheet(self, spreadsheet_id: str):
        """Get spreadsheet metadata using the official API."""
        try:
            sheet = (
                self.sheets_service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id)
                .execute()
            )
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
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
            ) as tmp:
                temp_path = tmp.name
                tmp.write(uploaded_file.getbuffer())

            file_metadata = {
                "name": uploaded_file.name,
                "parents": [folder_id],  # Folder ID inside the Shared Drive
            }
            st.write("file metadata", file_metadata)
            media = MediaFileUpload(temp_path, mimetype=uploaded_file.type)

            file = (
                self.drive_service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, webViewLink",
                    supportsAllDrives=True,  # Required for Shared Drives
                )
                .execute()
            )

            st.success(f"✅ Uploaded successfully: {file['webViewLink']}")
            return file["webViewLink"]

        except HttpError as error:
            st.error(f"❌ An error occurred: {error}")
            return None
