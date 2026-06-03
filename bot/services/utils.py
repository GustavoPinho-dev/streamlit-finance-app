import pandas as pd

from services.dates import parse_date_br


def is_valid_format_date(date_text, format_string="%d/%m/%Y"):
  parsed = parse_date_br(date_text)
  return not pd.isna(parsed) and parsed.strftime(format_string) == str(date_text).strip()
