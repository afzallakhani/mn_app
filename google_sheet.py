import os
import json
import gspread
from google.oauth2.service_account import Credentials

def save_feedback_to_sheet(row: dict):
    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    if not sa_json or not sheet_id:
        raise RuntimeError("Google Sheet env vars not set")

    creds_dict = json.loads(sa_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1

    # Add header once
    if not sheet.get_all_values():
        sheet.append_row(list(row.keys()))

    sheet.append_row(list(row.values()))
