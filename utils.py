import streamlit as st
import pandas as pd
import math
import requests
from datetime import date, timedelta

@st.cache_data
def get_selic():
    """Obtém dados históricos da taxa SELIC do Banco Central"""
    url = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"
    resp = requests.get(url)
    df = pd.DataFrame(resp.json()["conteudo"])

    df["DataInicioVigencia"] = pd.to_datetime(df["DataInicioVigencia"]).dt.date
    df["DataFimVigencia"] = pd.to_datetime(df["DataFimVigencia"]).dt.date
    df["DataFimVigencia"] = df["DataFimVigencia"].fillna(date.today())

    return df

@st.cache_data
def get_ipca():
    """Obtém dados históricos do IPCA do Banco Central"""
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.10844/dados?formato=json"
    resp = requests.get(url)
    df = pd.DataFrame(resp.json())

    return df

@st.cache_data
def get_cdi():
    """Obtém dados do CDI do último ano"""
    data_inicio = (date.today() - timedelta(days=365)).strftime("%d/%m/%Y")
    data_final = date.today().strftime("%d/%m/%Y")

    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.4392/dados?formato=json&dataInicial={data_inicio}&dataFinal={data_final}"
    resp = requests.get(url)
    df = pd.DataFrame(resp.json())

    return df

def calcular_investimento(valor_inicial, aporte_mensal, meses, taxa_selic_anual):
  # taxa mensal equivalente
  r = (1 + taxa_selic_anual)**(1/12) - 1

  def ir_rate(age_days):
      if age_days <= 180:
          return 0.225
      elif age_days <= 360:
          return 0.20
      elif age_days <= 720:
          return 0.175
      else:
          return 0.15

  total_investido = valor_inicial + aporte_mensal * meses
  total_ir = 0
  valor_final_liquido = 0

  # --- cálculo do aporte inicial ---
  fv_init = valor_inicial * (1 + r)**meses
  lucro_init = fv_init - valor_inicial
  ir_init = lucro_init * ir_rate(meses * 30.4167)
  total_ir += ir_init
  valor_final_liquido += fv_init - ir_init

  # --- cálculo de cada aporte mensal ---
  for k in range(meses):
      idade_meses = meses - k
      idade_dias = idade_meses * 30.4167
      
      fv = aporte_mensal * (1 + r)**idade_meses
      lucro = fv - aporte_mensal
      ir = lucro * ir_rate(idade_dias)

      total_ir += ir
      valor_final_liquido += fv - ir

  valor_bruto = valor_inicial * (1+r)**meses + aporte_mensal * (((1+r)**meses - 1) / r)
  rendimento_bruto = valor_bruto - total_investido
  rendimento_liquido = valor_final_liquido - total_investido

  # --- montar DataFrame ---
  df = pd.DataFrame({
      "Descrição": [
          "Valor bruto acumulado",
          "Valor final líquido",
          "Rendimento bruto",
          "Rendimento líquido",
          "IR total pago"
      ],
      "Valor": [
          valor_bruto,
          valor_final_liquido,
          rendimento_bruto,
          rendimento_liquido,
          total_ir
      ]
  })

  return df

def format_moeda_to_numeric(df):
  """
  Converte colunas monetárias ('Valor' ou 'Rendimento') de string
  no formato brasileiro para float.
  """

  colunas_moeda = ["Valor", "Rendimento"]

  for col in colunas_moeda:
    if col in df.columns:
      df[col] = (
        df[col]
        .astype(str)
        .str.replace(r"[^\d,.-]", "", regex=True)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
      )

      df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

  return df
