import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from services.utils import format_data_bot

class GoogleSheetsExtractor:
  def __init__(self, sheet_id: str):
    self.sheet_id = sheet_id
    self.scopes = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive"
    ]
    self.client = self._authenticate()

  def _authenticate(self):
    """Gerencia a conexão com a API do Google."""
    try:
      creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=self.scopes
      )
      return gspread.authorize(creds)
    except Exception as e:
      st.error("Falha crítica na autenticação com Google Sheets.")
      st.exception(e)
      st.stop()

  def load_sheet_data(self, worksheet_name: str) -> pd.DataFrame:
    """Extrai dados de uma aba específica e retorna um DataFrame."""
    try:
      sheet = self.client.open_by_key(self.sheet_id)
      worksheet = sheet.worksheet(worksheet_name)
      data = worksheet.get_all_records()
      return pd.DataFrame(data)
    except Exception as e:
      st.error(f"[ERROR] Erro ao ler a aba {worksheet_name}: {e}")
      return pd.DataFrame()

  def save_bot_data(self, data_bot: dict) -> bool:
    """Formata e salva os dados vindos do bot na aba correta."""
    try:
      sheet = self.client.open_by_key(self.sheet_id)
      
      # Lógica de mapeamento de abas
      tab_name = "Gastos" if data_bot.get('tipo') == 'Receita' else data_bot.get('tipo')
      worksheet = sheet.worksheet(tab_name)

      # Formata os dados usando a função utilitária
      data_to_save = format_data_bot(data_bot)

      # Insere na próxima linha disponível
      # Usar append_row é geralmente mais eficiente que calcular a linha manualmente
      worksheet.append_row(data_to_save, value_input_option='USER_ENTERED')
      
      print(f"✅ Dados enviados com sucesso para a aba {tab_name}!")
      return True
    except Exception as e:
      print(f"❌ Erro ao salvar no Sheets: {e}")
      return False