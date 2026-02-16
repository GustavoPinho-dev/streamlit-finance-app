import pandas as pd
from data.google_sheets import read_sheet_by_name
from services.utils import format_moeda_to_numeric, normalize_df_inv

class FinanceDataPipeline:
  def __init__(self, sheet_id):
    self.sheet_id = sheet_id

  def _extract(self, tab_name: str) -> pd.DataFrame:
    return read_sheet_by_name(self.sheet_id, tab_name)
  
  def _transform_rendimentos(self, df: pd.DataFrame) -> pd.DataFrame:
    df = format_moeda_to_numeric(df)
    df["Data Inicio"] = pd.to_datetime(df["Data Inicio"], dayfirst=True).dt.date
    df["Data Fim"] = pd.to_datetime(df["Data Fim"], dayfirst=True).dt.date
    return df
  
  def _transform_gastos(self, df: pd.DataFrame) -> pd.DataFrame:
    df = format_moeda_to_numeric(df)
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True)
    df["Mês"] = df["Data"].dt.to_period("M")
    return df
  
  def run(self):
    """Executa o pipeline completo e retorna dados prontos para consumo (Load)"""
    raw_rend = self._extract("Rendimentos")
    raw_inv = self._extract("Investimentos")
    raw_gastos = self._extract("Gastos")

    return {
      "rendimentos": self._transform_rendimentos(raw_rend),
      "investimentos": normalize_df_inv(format_moeda_to_numeric(raw_inv)),
      "gastos": self._transform_gastos(raw_gastos)
    }