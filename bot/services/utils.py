from datetime import datetime

def is_valid_format_date(date_text, format_string="%d/%m/%Y"):
  try:
    datetime.strptime(date_text, format_string)
    return True
  except ValueError:
    return False