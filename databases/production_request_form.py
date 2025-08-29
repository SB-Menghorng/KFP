import pandas as pd
import streamlit as st
from utils.google_sheets_client import GoogleSheetsClient


class ProductionRequestFormDB:
    def __init__(self, range_name: str, spreadsheet: str):
        self.google_client = GoogleSheetsClient()
        # Extract spreadsheet ID from Streamlit secrets
        self.sheet_id = self.google_client.extract_spreadsheet_id(spreadsheet)
        self.spreadsheet = self.google_client.open_sheet(self.sheet_id)

        # Optionally, get headers from the first row
        self.ranges = range_name
        self.headers = self._get_headers()

    def _get_headers(self):
        """Fetch headers from the first row of the sheet."""
        try:
            sheet_values = (
                self.google_client.sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=self.sheet_id, range=self.ranges)  # First row
                .execute()
            )
            return sheet_values.get("values", [[]])[0]
        except Exception as e:
            st.error(f"Failed to get headers: {e}")
            return []

    def append_row(self, data: dict, questions):
        """
        Append a new row to the production request form.
        Maps dict keys to sheet headers.
        """
        if not self.headers:
            st.error("Cannot append: Sheet headers not found.")
            return

        # Map headers to values from data
        row = [data.get(questions(header), "") for header in range(len(self.headers))]
        try:
            result = self.google_client.append_values(
                spreadsheet_id=self.sheet_id,
                range_name=self.ranges,
                values=[row],
                value_input_option="USER_ENTERED",
            )
            return result
        except Exception as e:
            st.error(f"Failed to append row: {e}")
            return None

    def get_df(self):
        """
        Fetch all rows from a Google Sheet as a pandas DataFrame.
        Handles missing or incomplete rows by filling with None and logs issues in Streamlit.
        """
        try:
            # Fetch data from Google Sheets
            result = (
                self.google_client.sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=self.sheet_id, range=self.ranges)
                .execute()
            )

            values = result.get("values", [])

            if not values:
                # st.warning("No data found in the sheet.")
                return pd.DataFrame()  # empty DataFrame

            headers = values[0]
            data_rows = values[1:]

            fixed_rows = []

            for i, row in enumerate(data_rows, start=1):
                # Handle completely empty row
                if not row:
                    # st.warning(f"Row {i} is empty. Filling with None.")
                    row = [None] * len(headers)
                # Handle short row
                elif len(row) < len(headers):
                    # st.warning(f"Row {i} has {len(row)} columns, expected {len(headers)}. Padding with None.")
                    row += [None] * (len(headers) - len(row))
                # Handle extra-long row
                elif len(row) > len(headers):
                    # st.warning(f"Row {i} has {len(row)} columns, expected {len(headers)}. Truncating extra values.")
                    row = row[: len(headers)]

                fixed_rows.append(row)

            # Create DataFrame safely
            df = pd.DataFrame(fixed_rows, columns=headers)
            # st.success(f"Data fetched successfully! {len(df)} rows loaded.")

            # Optional: display first few rows for debugging
            # st.dataframe(df.head())

            return df

        except Exception as e:
            st.error(f"Failed to get rows: {e}")
            return pd.DataFrame(
                columns=headers
            )  # Return empty DataFrame with headers if available
