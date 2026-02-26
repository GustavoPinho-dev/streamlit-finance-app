import pandas as pd
from data.extract import GoogleSheetsExtractor  # Importando a nova classe
from services.utils import format_moeda_to_numeric

class FinanceDataPipeline:
  def __init__(self, sheet_id: str):
    self.sheet_id = sheet_id
    # Inicializamos o extrator uma única vez
    self.extractor = GoogleSheetsExtractor(self.sheet_id)

  def _extract(self, tab_name: str) -> pd.DataFrame:
    """Utiliza o novo método da classe Extrator"""
    return self.extractor.load_sheet_data(tab_name)
  
  def _transform_rendimentos(self, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = format_moeda_to_numeric(df)
    df["Data Inicio"] = pd.to_datetime(df["Data Inicio"], dayfirst=True).dt.date
    df["Data Fim"] = pd.to_datetime(df["Data Fim"], dayfirst=True).dt.date
    return df
  
  def _transform_gastos(self, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = format_moeda_to_numeric(df)
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True)
    df["Mês"] = df["Data"].dt.to_period("M")
    return df

  def _transform_inv(self, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = format_moeda_to_numeric(df)
    df["Vencimento"] = pd.to_datetime(df["Vencimento"], dayfirst=True, errors='coerce').dt.date

    df["Tipo"] = df.apply(
      lambda r: f"{r['Produto']} - {r['Indicador']}"
      if pd.notnull(r.get("Indicador")) else str(r.get("Produto", "N/A")),
      axis=1
    )
    return df
  
  def run(self):
    """Executa o pipeline completo (Extract -> Transform)"""
    raw_rend = self._extract("Rendimentos")
    raw_inv = self._extract("Investimentos")
    raw_gastos = self._extract("Gastos")

    return {
      "rendimentos": self._transform_rendimentos(raw_rend),
      "investimentos": self._transform_inv(raw_inv),
      "gastos": self._transform_gastos(raw_gastos)
    }