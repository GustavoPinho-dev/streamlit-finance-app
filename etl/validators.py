import logging
from typing import Any, Optional

import pandas as pd


logger = logging.getLogger(__name__)


DATASET_CONTRACTS = {
  "Gastos": {
    "required_columns": ["Data", "Descrição", "Categoria", "Tipo", "Valor", "Instituição"],
    "mandatory_fields": ["Data", "Descrição", "Categoria", "Tipo", "Valor", "Instituição"],
    "numeric_non_negative": ["Valor"],
    "date_columns": ["Data"],
    "expected_columns": ["Data", "Descrição", "Categoria", "Tipo", "Valor", "Instituição", "Mês"],
  },
  "Investimentos": {
    "required_columns": ["Produto", "Operação", "Vencimento", "Valor", "Indicador", "Instituição"],
    "mandatory_fields": ["Produto", "Operação", "Valor", "Instituição"],
    "numeric_non_negative": ["Valor"],
    "date_columns": ["Vencimento"],
    "expected_columns": ["Produto", "Operação", "Vencimento", "Valor", "Indicador", "Instituição"],
  },
  "Rendimentos": {
    "required_columns": ["Data Inicio", "Data Fim", "Rendimento", "Instituição"],
    "mandatory_fields": ["Data Inicio", "Data Fim", "Rendimento", "Instituição"],
    "numeric_non_negative": ["Rendimento"],
    "date_columns": ["Data Inicio", "Data Fim"],
    "expected_columns": ["Data Inicio", "Data Fim", "Rendimento", "Instituição"],
  },
}


def build_error_payload(dataset: str, reason: str, details: dict[str, Any]) -> dict[str, Any]:
  return {
    "event": "dataset_validation_failed",
    "dataset": dataset,
    "reason": reason,
    "details": details,
  }


def build_empty_with_error(dataset: str, error_payload: dict[str, Any]) -> pd.DataFrame:
  expected_columns = DATASET_CONTRACTS[dataset]["expected_columns"]
  empty_df = pd.DataFrame(columns=expected_columns)
  empty_df.attrs["validation_error"] = error_payload
  return empty_df


def _invalid_mandatory_rows(df: pd.DataFrame, mandatory_fields: list[str]) -> dict[str, int]:
  invalid_fields: dict[str, int] = {}

  for col in mandatory_fields:
    if col not in df.columns:
      continue

    series = df[col]
    invalid_mask = series.isna()
    if pd.api.types.is_object_dtype(series):
      invalid_mask = invalid_mask | series.astype(str).str.strip().eq("")

    invalid_count = int(invalid_mask.sum())
    if invalid_count > 0:
      invalid_fields[col] = invalid_count

  return invalid_fields


def _to_numeric_series(series: pd.Series) -> pd.Series:
  if pd.api.types.is_numeric_dtype(series):
    return pd.to_numeric(series, errors="coerce")

  normalized = (
    series.astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(" ", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
  )
  return pd.to_numeric(normalized, errors="coerce")


def validate_dataset(df: pd.DataFrame, dataset: str) -> tuple[bool, Optional[dict[str, Any]]]:
  if dataset == "Investimentos" and "Operação" not in df.columns and "Tipo" in df.columns:
    df = df.rename(columns={"Tipo": "Operação"})

  contract = DATASET_CONTRACTS[dataset]
  required_columns = contract["required_columns"]

  missing_columns = [col for col in required_columns if col not in df.columns]
  if missing_columns:
    error_payload = build_error_payload(
      dataset=dataset,
      reason="missing_required_columns",
      details={"missing_columns": missing_columns},
    )
    logger.error(error_payload)
    return False, error_payload

  invalid_fields = _invalid_mandatory_rows(df, contract["mandatory_fields"])
  if invalid_fields:
    error_payload = build_error_payload(
      dataset=dataset,
      reason="empty_mandatory_fields",
      details={"invalid_fields": invalid_fields},
    )
    logger.error(error_payload)
    return False, error_payload

  for date_col in contract["date_columns"]:
    raw_series = df[date_col]
    empty_mask = raw_series.isna()
    if pd.api.types.is_object_dtype(raw_series):
      empty_mask = empty_mask | raw_series.astype(str).str.strip().eq("")

    parsed = pd.to_datetime(raw_series, dayfirst=True, errors="coerce")
    invalid_dates = int((parsed.isna() & ~empty_mask).sum())
    if invalid_dates > 0:
      error_payload = build_error_payload(
        dataset=dataset,
        reason="invalid_dates",
        details={"column": date_col, "invalid_rows": invalid_dates},
      )
      logger.error(error_payload)
      return False, error_payload

  for num_col in contract["numeric_non_negative"]:
    numeric_series = _to_numeric_series(df[num_col])
    invalid_numeric = int(numeric_series.isna().sum())
    if invalid_numeric > 0:
      error_payload = build_error_payload(
        dataset=dataset,
        reason="invalid_numeric_values",
        details={"column": num_col, "invalid_rows": invalid_numeric},
      )
      logger.error(error_payload)
      return False, error_payload

    negative_values = int((numeric_series < 0).sum())
    if negative_values > 0:
      error_payload = build_error_payload(
        dataset=dataset,
        reason="negative_values_not_allowed",
        details={"column": num_col, "invalid_rows": negative_values},
      )
      logger.error(error_payload)
      return False, error_payload

  return True, None
