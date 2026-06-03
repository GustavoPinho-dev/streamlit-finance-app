import unittest

import pandas as pd

from services.dates import (
  current_month_period,
  format_date_br,
  month_period_from_date,
  parse_date_br,
)
from services.utils import format_data_bot


class DateServiceTests(unittest.TestCase):
  def test_parse_and_format_date_br_use_timestamp_internally(self):
    parsed = parse_date_br("31/01/2024")

    self.assertIsInstance(parsed, pd.Timestamp)
    self.assertEqual(parsed, pd.Timestamp("2024-01-31"))
    self.assertEqual(format_date_br(parsed), "31/01/2024")

  def test_current_month_period_accepts_injected_today_at_month_turn(self):
    self.assertEqual(current_month_period("31/01/2024"), pd.Period("2024-01", "M"))
    self.assertEqual(current_month_period("01/02/2024"), pd.Period("2024-02", "M"))

  def test_current_and_next_month_comparison_is_deterministic(self):
    mes_atual = current_month_period(today="31/12/2024")
    mes_proximo = mes_atual + 1

    self.assertEqual(mes_atual, pd.Period("2024-12", "M"))
    self.assertEqual(mes_proximo, pd.Period("2025-01", "M"))
    self.assertNotEqual(mes_atual, mes_proximo)

  def test_month_period_from_date_handles_series(self):
    dates = pd.Series(["01/03/2024", "31/03/2024", "01/04/2024"])

    periods = month_period_from_date(dates)

    self.assertEqual(periods.tolist(), [pd.Period("2024-03", "M"), pd.Period("2024-03", "M"), pd.Period("2024-04", "M")])

  def test_format_data_bot_accepts_injected_today(self):
    linha = format_data_bot(
      {
        "tipo": "Gastos",
        "valor": "100",
        "descricao": "Mercado",
        "categoria": "Alimentação",
        "instituicao": "Banco",
      },
      today="15/05/2024",
    )

    self.assertEqual(linha[0], "15/05/2024")
    self.assertEqual(linha[4], "100,00")

  def test_transform_pipeline_keeps_date_columns_as_pandas_timestamps(self):
    from etl.transform import FinanceDataPipeline

    pipeline = object.__new__(FinanceDataPipeline)

    gastos = pipeline._transform_gastos(pd.DataFrame({
      "Data": ["31/01/2024", "01/02/2024"],
      "Valor": ["R$ 10,00", "R$ 20,00"],
    }))
    rendimentos = pipeline._transform_rendimentos(pd.DataFrame({
      "Data Inicio": ["01/01/2024"],
      "Data Fim": ["31/01/2024"],
      "Rendimento": ["R$ 100,00"],
    }))
    investimentos = pipeline._transform_inv(pd.DataFrame({
      "Produto": ["CDB"],
      "Indicador": ["CDI"],
      "Operação": ["aplicação"],
      "Vencimento": ["15/05/2025"],
      "Valor": ["R$ 1.000,00"],
    }))

    self.assertTrue(pd.api.types.is_datetime64_any_dtype(gastos["Data"]))
    self.assertTrue(pd.api.types.is_datetime64_any_dtype(rendimentos["Data Inicio"]))
    self.assertTrue(pd.api.types.is_datetime64_any_dtype(rendimentos["Data Fim"]))
    self.assertTrue(pd.api.types.is_datetime64_any_dtype(investimentos["Vencimento"]))
    self.assertEqual(gastos["Mês"].tolist(), [pd.Period("2024-01", "M"), pd.Period("2024-02", "M")])


if __name__ == "__main__":
  unittest.main()
