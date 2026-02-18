import pandas as pd
from datetime import datetime

def format_moeda_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
  df = df.copy()

  for col in df.columns:
    if df[col].dtype == object:
      df[col] = (
        df[col]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
      )

    df[col] = pd.to_numeric(df[col], errors="ignore")

  return df

def normalize_df_inv(df_inv: pd.DataFrame) -> pd.DataFrame:
  df_inv["Vencimento"] = pd.to_datetime(df_inv["Vencimento"], dayfirst=True).dt.date

  df_inv["Tipo"] = df_inv.apply(
    lambda r: f"{r['Produto']} - {r['Indicador']}"
    if pd.notnull(r["Indicador"]) else str(r["Produto"]),
    axis=1
  )

  return df_inv

def format_data_bot(data_bot: dict) -> dict:
  categoria = data_bot.get('tipo', '')

  mapeamento = {
    "Gastos": "Despesa"
  }

  tipo = mapeamento.get(categoria, "Outros")

  valor_raw = data_bot.get('valor', '0')
  # Remove vírgulas para garantir que a conversão funcione se necessário
  valor_limpo = str(valor_raw).replace(',', '.')
  valor_formatado = f"R$ {valor_limpo}"

  data_to_save = [
    datetime.now().strftime("%d/%m/%Y"), # Timestamp
    data_bot.get('descricao', ''),
    data_bot.get('categoria', ''),
    tipo,
    valor_formatado,
    data_bot.get('instituicao', ''),
    data_bot.get('produto', ''),
    data_bot.get('tipo_invest', ''),
    data_bot.get('vencimento', ''),
    data_bot.get('indicador', '')
  ]

  return data_to_save
