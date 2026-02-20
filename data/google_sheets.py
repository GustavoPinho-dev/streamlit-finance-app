import streamlit as st
import gspread
import pandas as pd
from services.utils import format_data_bot
from datetime import datetime
from google.oauth2.service_account import Credentials

# Escopos de leitura
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

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

def save_data_sheets(sheet_id: str, data_bot: dict):
  try:
    sheet = client.open_by_key(sheet_id)
    
    if data_bot['tipo'] == 'Receita':
      worksheet = sheet.worksheet('Gastos')
    else:
      worksheet = sheet.worksheet(data_bot['tipo'])

    data_to_save = format_data_bot(data_bot)

    column_a = worksheet.col_values(1) 
    proxima_linha = len(column_a) + 1

    worksheet.insert_row(data_to_save, proxima_linha)
    #worksheet.append_row(linha)
    print("✅ Dados enviados com sucesso para o Sheets!")
    return True
  except Exception as e:
    print(f"❌ Erro ao salvar no Sheets: {e}")
    return False
