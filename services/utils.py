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

def format_data_bot(data_bot: dict) -> list:
  # 1. Identifica o tipo de entrada
  tipo_entrada = data_bot.get('tipo', '')
  
  # 2. Formatação comum de valor para "R$ 200"
  valor_raw = data_bot.get('valor', '0')
  valor_limpo = str(valor_raw).replace(',', '.')
  valor_formatado = f"R$ {valor_limpo}"
  
  # 3. Lógica condicional para montagem da linha (tabelas diferentes)
  if tipo_entrada == "Gastos":
    # Estrutura: Data, Descrição, Categoria, Tipo, Valor, Instituição
    # Mapeamos 'Gastos' para aparecer como 'Despesa' na coluna Tipo
    tipo_exibicao = "Despesa" 
    
    data_to_save = [
      datetime.now().strftime("%d/%m/%Y"), # Data
      data_bot.get('descricao', ''),       # Descrição
      data_bot.get('categoria', 'Trabalho'),       # Categoria
      tipo_exibicao,                       # Tipo (Mapeado)
      valor_formatado,                     # Valor
      data_bot.get('instituicao', '')      # Instituição
    ]
      
  elif tipo_entrada == "Investimentos":
    # Estrutura: Produto, Tipo, Vencimento, Valor, Indicador, Instituição
    data_to_save = [
      data_bot.get('produto', ''),         # Produto
      data_bot.get('tipo_invest', ''),     # Tipo (Ex: Aplicação)
      data_bot.get('vencimento', ''),      # Vencimento
      valor_formatado,                     # Valor
      data_bot.get('indicador', ''),       # Indicador (Ex: SELIC)
      data_bot.get('instituicao', '')      # Instituição
    ]

  elif tipo_entrada == "Receita":
    tipo_exibicao = "Receita" 
    
    data_to_save = [
      datetime.now().strftime("%d/%m/%Y"), # Data
      data_bot.get('descricao', ''),       # Descrição
      data_bot.get('categoria', ''),       # Categoria
      tipo_exibicao,                       # Tipo (Mapeado)
      valor_formatado,                     # Valor
      data_bot.get('instituicao', '')      # Instituição
    ]
      
  else:
    # Caso receba algo fora do padrão, retorna uma lista vazia ou erro
    return []

  return data_to_save
