import pandas as pd


DATE_FORMAT_BR = "%d/%m/%Y"


def parse_date_br(value):
  """Converte valores de data no padrão brasileiro para ``pd.Timestamp``.

  Aceita escalares ou séries/índices do pandas. Em entradas inválidas, retorna
  ``pd.NaT`` (ou uma série com ``NaT``), mantendo um único tipo interno para datas.
  """
  parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")

  if isinstance(parsed, pd.Timestamp):
    return parsed.normalize() if not pd.isna(parsed) else pd.NaT

  if isinstance(parsed, (pd.Series, pd.DatetimeIndex)):
    return parsed.dt.normalize() if isinstance(parsed, pd.Series) else parsed.normalize()

  if pd.isna(parsed):
    return pd.NaT

  return pd.Timestamp(parsed).normalize()


def format_date_br(value):
  """Formata uma data como ``DD/MM/AAAA``."""
  parsed = parse_date_br(value)

  if isinstance(parsed, pd.Series):
    return parsed.dt.strftime(DATE_FORMAT_BR).fillna("")

  if isinstance(parsed, pd.DatetimeIndex):
    return parsed.strftime(DATE_FORMAT_BR)

  if pd.isna(parsed):
    return ""

  return parsed.strftime(DATE_FORMAT_BR)


def month_period_from_date(value):
  """Retorna o período mensal (``pd.Period`` com frequência M) de uma data."""
  parsed = parse_date_br(value)

  if isinstance(parsed, pd.Series):
    return parsed.dt.to_period("M")

  if isinstance(parsed, pd.DatetimeIndex):
    return parsed.to_period("M")

  if pd.isna(parsed):
    return pd.NaT

  return parsed.to_period("M")


def current_month_period(today=None):
  """Retorna o período do mês atual, permitindo injetar ``today`` em testes."""
  reference_date = parse_date_br(today) if today is not None else pd.Timestamp.today().normalize()
  return month_period_from_date(reference_date)
