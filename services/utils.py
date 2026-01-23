import pandas as pd

def format_moeda_to_numeric(df):
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

def normalize_df_inv(df_inv):
  df_inv["Vencimento"] = pd.to_datetime(df_inv["Vencimento"], dayfirst=True).dt.date

  df_inv["Tipo"] = df_inv.apply(
    lambda r: f"{r['Produto']} - {r['Indicador']}"
    if pd.notnull(r["Indicador"]) else str(r["Produto"]),
    axis=1
  )

  return df_inv
