import pandas as pd
from datetime import datetime
import unicodedata
import re
from bot.services.logger import get_logger


logger = get_logger(__name__)


def padronizar_valor_recebido(valor) -> str:
  """
  Garante o padrão de valor com duas casas decimais e separador ",".

  Exemplos:
  - "68,90" -> "68,90"
  - "100" -> "100,00"
  - 100 -> "100,00"
  """
  if valor is None or str(valor).strip() == "":
    return "0,00"

  valor_str = str(valor).strip()

  if "," in valor_str and "." in valor_str:
    valor_limpo = valor_str.replace(".", "").replace(",", ".")
  elif "," in valor_str:
    valor_limpo = valor_str.replace(",", ".")
  else:
    valor_limpo = valor_str

  valor_float = float(valor_limpo)

  return f"{valor_float:.2f}".replace(".", ",")

# função para formatar um valor em moeda para apenas númerico
def format_moeda_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
  df = df.copy()
  
  # Definimos quais colunas queremos transformar
  colunas_financeiras = ["Valor", "Rendimento"]

  for col in df.columns:
    # Verifica se o nome da coluna (ou parte dele) está na nossa lista alvo
    if any(alvo in col for alvo in colunas_financeiras):
      amostra_original = df[col].head(5).tolist()
      def _parse_currency(value):
        if pd.isna(value):
          return pd.NA

        text = str(value).strip()
        if not text:
          return pd.NA

        # Mantém apenas dígitos e separadores numéricos
        text = re.sub(r"[^\d,.\-]", "", text)
        if not text:
          return pd.NA

        # Trata formato pt-BR e en-US
        if "," in text and "." in text:
          text = text.replace(".", "").replace(",", ".")
        elif "," in text:
          text = text.replace(",", ".")

        return pd.to_numeric(text, errors='coerce')

      df[col] = df[col].apply(_parse_currency)
      total_nulos = int(df[col].isna().sum())
      if total_nulos > 0:
        logger.warning(
          "Conversão numérica da coluna '%s' gerou %s valores nulos. Amostra original: %s",
          col,
          total_nulos,
          amostra_original
        )
      else:
        logger.info("Conversão numérica da coluna '%s' concluída sem nulos.", col)

  return df

# Formata dados recebidos pelo bot para salvar na planilha
def format_data_bot(data_bot: dict) -> list:
  # 1. Identifica o tipo de entrada
  tipo_entrada = data_bot.get('tipo', '')
  
  # 2. Formatação comum de valor para "100,00"
  valor_padronizado = padronizar_valor_recebido(data_bot.get('valor', '0'))
  
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
      valor_padronizado,                              # Valor
      data_bot.get('instituicao', '')      # Instituição
    ]
      
  elif tipo_entrada == "Investimentos":
    # Estrutura: Produto, Operação, Vencimento, Valor, Indicador, Instituição
    data_to_save = [
      data_bot.get('produto', ''),         # Produto
      data_bot.get('tipo_invest', ''),     # Operação (Ex: Aplicação)
      data_bot.get('vencimento', ''),      # Vencimento
      valor_padronizado,                              # Valor
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
      valor_padronizado,                              # Valor
      data_bot.get('instituicao', '')      # Instituição
    ]

  elif tipo_entrada == "Rendimentos":
    tipo_exibicao = "Rendimentos" 
    
    data_to_save = [
      data_bot.get('data_inicio', datetime.now().strftime("%d/%m/%Y")),    # Data Início
      data_bot.get('data_fim', datetime.now().strftime("%d/%m/%Y")),       # Descrição
      f"R$ {valor_padronizado}",                      # Valor do rendimento
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
  saldo_mes = total_receitas - (total_despesas + total_investido)

  return {
    "Receita Total": total_receitas, 
    "Gastos": total_despesas, 
    "Total Investido": total_investido, 
    "Saldo Anterior": saldo_anterior, 
    "Saldo Conta": saldo,
    "Saldo Mês": saldo_mes
  }

def padronizar_string(texto: str) -> str:
  if texto is None:
    return None

  # Normaliza para separar letras de acentos
  texto_normalizado = unicodedata.normalize('NFD', texto)

  # Remove os acentos
  texto_sem_acentos = ''.join(
    char for char in texto_normalizado
    if unicodedata.category(char) != 'Mn'
  )

  # Converte para uppercase
  return texto_sem_acentos.upper()
