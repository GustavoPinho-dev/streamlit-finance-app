from datetime import datetime

import pandas as pd
import streamlit as st

from data.extract import GoogleSheetsExtractor
from etl.transform import FinanceDataPipeline
from services.utils import get_data_resumo


class FinanceService:
  def __init__(self, sheet_id: str):
    self.sheet_id = sheet_id
    self.pipeline = FinanceDataPipeline(sheet_id)
    self.extractor = GoogleSheetsExtractor(sheet_id)

  def get_df_gastos(self):
    data = self.pipeline.run()
    return data["gastos"]

  def salvar_registro(self, dados: dict) -> bool:
    return self.extractor.save_bot_data(dados)

  def consultar_resumo(self, instituicao: str):
    df = self.get_df_gastos().copy()
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True)

    filtro_mes_atual = (df["Data"].dt.month == datetime.now().month) & (
      df["Data"].dt.year == datetime.now().year
    )

    return get_data_resumo(df[filtro_mes_atual], instituicao)

  def get_instituicoes(self):
    df = self.get_df_gastos()
    return pd.unique(df["Instituição"])