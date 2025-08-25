from utils.google_sheets_client import GoogleSheetsClient
import streamlit as st
import pandas as pd
import pandas as pd


class ProductionRequestFormDB:
    def __init__(self, range_name):
        self.google_client = GoogleSheetsClient()
        # Extract spreadsheet ID from Streamlit secrets
        self.sheet_id = self.google_client.extract_spreadsheet_id(
            st.secrets["SPREADSHEET_DATA_STORED_URL"]
        )
        self.spreadsheet = self.google_client.open_sheet(self.sheet_id)

        # Optionally, get headers from the first row
        self.ranges = range_name
        self.headers = self._get_headers()

    def _get_headers(self):
        """Fetch headers from the first row of the sheet."""
        try:
            sheet_values = self.google_client.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.ranges  # First row
            ).execute()
            return sheet_values.get("values", [[]])[0]
        except Exception as e:
            st.error(f"Failed to get headers: {e}")
            return []

    def append_row(self, data: dict):
        """
        Append a new row to the production request form.
        Maps dict keys to sheet headers.
        """
        if not self.headers:
            st.error("Cannot append: Sheet headers not found.")
            return

        # Map headers to values from data
        row = [data.get(header, "") for header in self.headers]

        try:
            result = self.google_client.append_values(
                spreadsheet_id=self.sheet_id,
                range_name=self.ranges,
                values=[row],
                value_input_option="USER_ENTERED"
            )
            return result
        except Exception as e:
            st.error(f"Failed to append row: {e}")
            return None

    def get_df(self):
        """Fetch all rows as a pandas DataFrame."""
        try:
            result = self.google_client.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.ranges
            ).execute()
            values = result.get("values", [])
            if not values:
                return pd.DataFrame()

            headers = values[0]
            data_rows = values[1:]
            return pd.DataFrame(data_rows, columns=headers)
        except Exception as e:
            st.error(f"Failed to get rows: {e}")
            return pd.DataFrame()
