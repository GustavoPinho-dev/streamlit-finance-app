import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# Escopos de leitura
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def connect_to_sheets(credentials_file: str):
    creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client


def read_sheet_by_name(client, sheet_id: str, worksheet_name: str) -> pd.DataFrame:
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)
