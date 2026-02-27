import streamlit as st


def _get_global_sheet_id() -> str:
  return st.secrets.get("SHEET_ID")


def _get_sheet_id_from_auth_credentials(username: str) -> str:
  auth = st.secrets.get("auth", {})
  credentials = auth.get("credentials", {})
  users = credentials.get("usernames", {})
  user = users.get(username, {})
  return user.get("sheet_id")


def _get_sheet_id_from_mapping(username: str) -> str:
  mapping = st.secrets.get("sheet_ids", {})
  return mapping.get(username)


def get_sheet_id_for_user(username: str) -> str:
  """Resolve o Google Sheet ID considerando usuário autenticado e fallback global."""
  if username:
    return (
      _get_sheet_id_from_mapping(username)
      or _get_sheet_id_from_auth_credentials(username)
      or _get_global_sheet_id()
    )

  global_sheet_id = _get_global_sheet_id()
  if global_sheet_id:
    return global_sheet_id

  raise ValueError(
    "Nenhum SHEET_ID configurado. Defina um SHEET_ID global ou um mapeamento por usuário."
  )
