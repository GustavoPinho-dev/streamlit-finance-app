import pandas as pd
from data.extract import GoogleSheetsExtractor  # Importando a nova classe
from services.utils import format_moeda_to_numeric

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
    if "Operação" not in df.columns and "Tipo" in df.columns:
      df = df.rename(columns={"Tipo": "Operação"})

    df = format_moeda_to_numeric(df)
    df["Vencimento"] = pd.to_datetime(df["Vencimento"], dayfirst=True, errors='coerce').dt.date

    df["Tipo"] = df.apply(
      lambda r: f"{r['Produto']} - {r['Indicador']}"
      if pd.notnull(r.get("Indicador")) else str(r.get("Produto", "N/A")),
      axis=1
    )
    df["Operação"] = (
      df["Operação"]
      .astype(str)
      .str.strip()
      .str.title()
    )
    return df

  def _transform_planejamento(self, df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o DataFrame de planejamento lido do Sheets."""
    if df.empty:
      return df

    def _parse_decimal_br(value):
      """Converte textos numéricos pt-BR/us para float (ex.: 5.062,31 / 5062.31 / 41,48%)."""
      if pd.isna(value):
        return 0.0

      if isinstance(value, (int, float)):
        return float(value)

      text = str(value).strip()
      if not text:
        return 0.0

      is_percent = "%" in text
      text = text.replace("%", "").replace("R$", "").replace(" ", "")

      if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
      elif "," in text:
        text = text.replace(",", ".")

      number = pd.to_numeric(text, errors="coerce")
      if pd.isna(number):
        return 0.0

      number = float(number)
      if is_percent and number <= 1:
        # Caso venha do Sheets como fração (0.4148), convertemos para 41.48.
        return number * 100
      return number

    if "Receita" in df.columns:
      df["Receita"] = df["Receita"].apply(_parse_decimal_br)
    if "Valor" in df.columns:
      df["Valor"] = df["Valor"].apply(_parse_decimal_br)
    if "Percentual" in df.columns:
      df["Percentual"] = df["Percentual"].apply(_parse_decimal_br)

    return df
  
  def run(self):
    """Executa o pipeline completo (Extract -> Transform)"""
    raw_rend = self._extract("Rendimentos")
    raw_inv = self._extract("Investimentos")
    raw_gastos = self._extract("Gastos")

    try:
      raw_plan = self.extractor.load_planejamento()
    except Exception:
      raw_plan = pd.DataFrame()

    return {
      "rendimentos": self._transform_rendimentos(raw_rend),
      "investimentos": self._transform_inv(raw_inv),
      "gastos": self._transform_gastos(raw_gastos),
      "planejamento": self._transform_planejamento(raw_plan),
    }
