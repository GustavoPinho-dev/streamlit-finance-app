import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# Escopos de leitura
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def connect_to_sheets():
  creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
  )
  return gspread.authorize(creds)

@st.cache_resource
def get_client():
  try:
    return connect_to_sheets()
  except Exception as e:
    st.error("Erro ao conectar ao Google Sheets")
    st.exception(e)
    st.stop()

client = get_client()

def read_sheet_by_name(sheet_id: str, worksheet_name: str) -> pd.DataFrame:
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)
