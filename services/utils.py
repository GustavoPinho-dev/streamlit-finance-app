import pandas as pd
from datetime import datetime

# função para formatar um valor em moeda para apenas númerico
def format_moeda_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
  df = df.copy()
  
  # Definimos quais colunas queremos transformar
  colunas_financeiras = ["Valor", "Rendimento"]

  for col in df.columns:
    # Verifica se o nome da coluna (ou parte dele) está na nossa lista alvo
    if any(alvo in col for alvo in colunas_financeiras):
      if df[col].dtype == object:
        df[col] = (
          df[col]
          .astype(str)
          .str.replace("R$", "", regex=False)
          .str.replace(".", "", regex=False)
          .str.replace(",", ".", regex=False)
          .str.strip()
        )
        
      # Converte para numérico, tratando erros caso a célula esteja vazia
      df[col] = pd.to_numeric(df[col], errors='coerce')

  return df

# Formata dados recebidos pelo bot para salvar na planilha
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

  elif tipo_entrada == "Rendimentos":
    tipo_exibicao = "Rendimentos" 
    
    data_to_save = [
      data_bot.get('data_inicio', datetime.now().strftime("%d/%m/%Y")),    # Data Início
      data_bot.get('data_fim', datetime.now().strftime("%d/%m/%Y")),       # Descrição
      f"R$ {str(data_bot.get('valor', '')).replace(',', '.')}", # Valor do rendimento
      data_bot.get('instituicao', '')      # Instituição
    ]
      
  else:
    # Caso receba algo fora do padrão, retorna uma lista vazia ou erro
    return []

  print(f'Dados salvos: {data_to_save}')

  return data_to_save

def get_data_resumo(df: pd.DataFrame, instituicao: str):
  df_instituicao = df[df["Instituição"] == instituicao]

  total_receitas = df_instituicao[df_instituicao["Tipo"] == "Receita"]["Valor"].sum()
  total_despesas = df_instituicao[df_instituicao["Tipo"] == "Despesa"]["Valor"].sum()
  total_investido = df_instituicao[df_instituicao["Categoria"] == "Investimentos"]["Valor"].sum()
  saldo_anterior = df_instituicao[df_instituicao["Tipo"] == "Saldo"]["Valor"].sum()

  saldo = saldo_anterior + (total_receitas - (total_despesas + total_investido))

  return total_receitas, total_despesas, total_investido, saldo_anterior, saldo
