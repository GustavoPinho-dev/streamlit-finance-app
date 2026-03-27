import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from services.utils import format_data_bot


class GoogleSheetsAuthError(Exception):
  """Erro de autenticação com Google Sheets."""


class GoogleSheetsReadError(Exception):
  """Erro de leitura/escrita no Google Sheets."""

class GoogleSheetsExtractor:
  def __init__(self, sheet_id: str, credentials_dict: dict):
    self.sheet_id = sheet_id
    self.credentials_dict = credentials_dict
    self.scopes = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive"
    ]
    self.client = self._authenticate()

  def _authenticate(self):
    """Gerencia a conexão com a API do Google."""
    try:
      creds = Credentials.from_service_account_info(
        self.credentials_dict,
        scopes=self.scopes
      )
      return gspread.authorize(creds)
    except Exception as e:
      raise GoogleSheetsAuthError("Falha crítica na autenticação com Google Sheets.") from e

  def load_sheet_data(self, worksheet_name: str) -> pd.DataFrame:
    """Extrai dados de uma aba específica e retorna um DataFrame."""
    try:
      sheet = self.client.open_by_key(self.sheet_id)
      worksheet = sheet.worksheet(worksheet_name)
      data = worksheet.get_all_records()
      return pd.DataFrame(data)
    except Exception as e:
      raise GoogleSheetsReadError(f"Erro ao ler a aba {worksheet_name}.") from e

  def save_bot_data(self, data_bot: dict) -> bool:
    """Formata e salva os dados vindos do bot na aba correta."""
    try:
      sheet = self.client.open_by_key(self.sheet_id)
      
      # Lógica de mapeamento de abas
      tab_name = "Gastos" if data_bot.get('tipo') == 'Receita' else data_bot.get('tipo')
      worksheet = sheet.worksheet(tab_name)

      # Formata os dados usando a função utilitária
      data_to_save = format_data_bot(data_bot)

      # Insere na próxima linha disponível
      worksheet.append_row(data_to_save, value_input_option='USER_ENTERED')
      
      print(f"✅ Dados enviados com sucesso para a aba {tab_name}!")
      return True
    except Exception as e:
      raise GoogleSheetsReadError(f"Erro ao salvar dados na aba {tab_name}.") from e

  # ──────────────────────────────────────────────
  # PLANEJAMENTO
  # ──────────────────────────────────────────────

  PLANEJAMENTO_HEADERS = ["Mês", "Receita", "Categoria", "Percentual", "Valor"]

  def _ensure_planejamento_tab(self, sheet) -> gspread.Worksheet:
    """Garante que a aba 'Planejamento' existe; cria com cabeçalho se necessário."""
    try:
      return sheet.worksheet("Planejamento")
    except gspread.exceptions.WorksheetNotFound:
      ws = sheet.add_worksheet(title="Planejamento", rows=1000, cols=len(self.PLANEJAMENTO_HEADERS))
      ws.append_row(self.PLANEJAMENTO_HEADERS, value_input_option='USER_ENTERED')
      return ws

  def load_planejamento(self) -> pd.DataFrame:
    """Lê todos os planejamentos salvos e retorna um DataFrame."""
    try:
      sheet = self.client.open_by_key(self.sheet_id)
      ws = self._ensure_planejamento_tab(sheet)
      rows = ws.get_all_values()
      if not rows:
        return pd.DataFrame(columns=self.PLANEJAMENTO_HEADERS)

      headers = rows[0]
      data_rows = rows[1:]
      if not data_rows:
        return pd.DataFrame(columns=headers or self.PLANEJAMENTO_HEADERS)

      return pd.DataFrame(data_rows, columns=headers)
    except GoogleSheetsReadError:
      raise
    except Exception as e:
      raise GoogleSheetsReadError("Erro ao carregar a aba Planejamento.") from e

  def save_planejamento(self, mes: str, receita: float, alocacoes: list[dict]) -> bool:
    """
    Salva (ou substitui) o planejamento de um mês específico.

    Parameters
    ----------
    mes : str
        Mês no formato "MM/YYYY".
    receita : float
        Receita total base do planejamento.
    alocacoes : list[dict]
        Lista de dicts com chaves 'categoria', 'percentual', 'valor'.
    """
    try:
      sheet = self.client.open_by_key(self.sheet_id)
      ws = self._ensure_planejamento_tab(sheet)

      # Lê dados existentes para remover linhas do mesmo mês
      existing = ws.get_all_values()          # inclui cabeçalho na posição 0
      headers = existing[0] if existing else self.PLANEJAMENTO_HEADERS

      try:
        mes_col_idx = headers.index("Mês")    # índice da coluna "Mês" (0-based)
      except ValueError:
        mes_col_idx = 0

      # Determina linhas a deletar (de baixo pra cima para não deslocar índices)
      rows_to_delete = [
        i + 1  # gspread usa índice 1-based
        for i, row in enumerate(existing[1:], start=1)
        if len(row) > mes_col_idx and row[mes_col_idx] == mes
      ]
      for row_idx in reversed(rows_to_delete):
        ws.delete_rows(row_idx)

      # Monta e insere as novas linhas
      new_rows = [
        [mes, receita, a["categoria"], a["percentual"], round(a["valor"], 2)]
        for a in alocacoes
      ]
      if new_rows:
        ws.append_rows(new_rows, value_input_option='USER_ENTERED')

      print(f"✅ Planejamento de {mes} salvo com sucesso!")
      return True
    except GoogleSheetsReadError:
      raise
    except Exception as e:
      raise GoogleSheetsReadError(f"Erro ao salvar planejamento de {mes}.") from e