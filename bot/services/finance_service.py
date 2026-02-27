from etl.transform import FinanceDataPipeline
from data.extract import GoogleSheetsExtractor
from services.utils import get_data_resumo
from datetime import datetime
import pandas as pd
import streamlit as st

SHEET_ID = st.secrets["SHEET_ID"]

# Inicialização global das ferramentas de dados
pipeline = FinanceDataPipeline(SHEET_ID)
extractor = GoogleSheetsExtractor(SHEET_ID)

def get_df_gastos():
  data = pipeline.run()
  return data["gastos"]

def salvar_registro(dados: dict) -> bool:
  return extractor.save_bot_data(dados)

def consultar_resumo(instituicao: str):
  df = get_df_gastos()
  df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)

  filtro_mes_atual = (df['Data'].dt.month == datetime.now().month) & (df['Data'].dt.year == datetime.now().year)

  return get_data_resumo(df[filtro_mes_atual], instituicao)