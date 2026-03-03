import pandas as pd
from data.extract import GoogleSheetsExtractor  # Importando a nova classe
from services.utils import format_moeda_to_numeric
from etl.validators import build_empty_with_error, validate_dataset

class FinanceDataPipeline:
  def __init__(self, sheet_id: str, credentials_dict: dict):
    self.sheet_id = sheet_id
    self.credentials_dict = credentials_dict
    # Inicializamos o extrator uma única vez
    self.extractor = GoogleSheetsExtractor(
      sheet_id=self.sheet_id,
      credentials_dict=self.credentials_dict
    )

  def _extract(self, tab_name: str) -> pd.DataFrame:
    """Utiliza o novo método da classe Extrator"""
    return self.extractor.load_sheet_data(tab_name)
  
  def _transform_rendimentos(self, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    is_valid, error_payload = validate_dataset(df, "Rendimentos")
    if not is_valid:
      return build_empty_with_error("Rendimentos", error_payload)

    df = format_moeda_to_numeric(df)
    df["Data Inicio"] = pd.to_datetime(df["Data Inicio"], dayfirst=True).dt.date
    df["Data Fim"] = pd.to_datetime(df["Data Fim"], dayfirst=True).dt.date
    return df
  
  def _transform_gastos(self, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    is_valid, error_payload = validate_dataset(df, "Gastos")
    if not is_valid:
      return build_empty_with_error("Gastos", error_payload)

    df = format_moeda_to_numeric(df)
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True)
    df["Mês"] = df["Data"].dt.to_period("M")
    return df

  def _transform_inv(self, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    is_valid, error_payload = validate_dataset(df, "Investimentos")
    if not is_valid:
      return build_empty_with_error("Investimentos", error_payload)

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

    is_valid_rend, error_rend = validate_dataset(raw_rend, "Rendimentos") if not raw_rend.empty else (True, None)
    is_valid_inv, error_inv = validate_dataset(raw_inv, "Investimentos") if not raw_inv.empty else (True, None)
    is_valid_gastos, error_gastos = validate_dataset(raw_gastos, "Gastos") if not raw_gastos.empty else (True, None)

    return {
      "rendimentos": self._transform_rendimentos(raw_rend) if is_valid_rend else build_empty_with_error("Rendimentos", error_rend),
      "investimentos": self._transform_inv(raw_inv) if is_valid_inv else build_empty_with_error("Investimentos", error_inv),
      "gastos": self._transform_gastos(raw_gastos) if is_valid_gastos else build_empty_with_error("Gastos", error_gastos)
    }
