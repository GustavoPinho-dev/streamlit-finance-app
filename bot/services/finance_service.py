import pandas as pd

from bot.services.logger import get_logger
from data.extract import GoogleSheetsExtractor
from etl.transform import FinanceDataPipeline
from services.dates import current_month_period, month_period_from_date, parse_date_br
from services.utils import get_data_resumo

logger = get_logger(__name__)

class FinanceService:
  def __init__(self, sheet_id: str, credentials_dict: dict):
    self.sheet_id = sheet_id
    self.credentials_dict = credentials_dict
    self.pipeline = FinanceDataPipeline(sheet_id, credentials_dict)
    self.extractor = GoogleSheetsExtractor(sheet_id, credentials_dict)

  def get_df_gastos(self):
    data = self.pipeline.run()
    return data["gastos"]

  def salvar_registro(self, dados: dict) -> bool:
    try:
      return self.extractor.save_bot_data(dados)
    except Exception:
      logger.exception('Erro ao salvar registro no Google Sheets para sheet_id=%s', self.sheet_id)
      return False

  def consultar_resumo(self, instituicao: str, today=None):
    df = self.get_df_gastos().copy()
    df["Data"] = parse_date_br(df["Data"])

    filtro_mes_atual = month_period_from_date(df["Data"]) == current_month_period(today)

    return get_data_resumo(df[filtro_mes_atual], instituicao)

  def get_instituicoes(self):
    df = self.get_df_gastos()
    return pd.unique(df["Instituição"])