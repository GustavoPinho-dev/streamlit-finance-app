import streamlit as st

from bot.services.logger import get_logger
from config.auth import autenticar
from config.sheets import get_sheet_id_for_user
from data.extract import GoogleSheetsAuthError, GoogleSheetsReadError
from etl.transform import FinanceDataPipeline
from ui.gastos import render_gastos
from ui.investimentos import render_investimentos
from ui.planejamento import render_planejamento
from ui.rendimentos import render_rendimentos


logger = get_logger(__name__)


# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
  page_title="Finanças",
  page_icon="💰",
  layout="wide"
)

# ==============================
# AUTENTICAÇÃO
# ==============================
authenticator = autenticar()

if st.session_state["authentication_status"]:

  username = st.session_state.get("username")
  sheet_id = get_sheet_id_for_user(username)
  dados_key = f"dados_{username}" if username else "dados"

  # ==============================
  # CARREGA DADOS
  # ==============================
  if dados_key not in st.session_state:
    try:
      pipeline = FinanceDataPipeline(
        sheet_id=sheet_id,
        credentials_dict=st.secrets["gcp_service_account"]
      )
      st.session_state[dados_key] = pipeline.run()
      logger.info("Dados carregados e salvos na sessão para cache_key=%s", dados_key)
    except GoogleSheetsAuthError as e:
      st.error("Falha na autenticação com Google Sheets. Verifique as credenciais.")
      st.exception(e)
      logger.exception("Falha de autenticação no carregamento dos dados.")
      st.stop()
    except GoogleSheetsReadError as e:
      st.error("Não foi possível carregar os dados da planilha.")
      st.exception(e)
      logger.exception("Falha de leitura no carregamento dos dados.")
      st.stop()

  df = st.session_state[dados_key]["rendimentos"]
  df_inv = st.session_state[dados_key]["investimentos"]
  df_gastos = st.session_state[dados_key]["gastos"]
  df_plan_salvo = st.session_state[dados_key]["planejamento"]
  logger.info(
    "DataFrames em sessão -> rendimentos=%s, investimentos=%s, gastos=%s, planejamento=%s",
    len(df),
    len(df_inv),
    len(df_gastos),
    len(df_plan_salvo)
  )

  # ==============================
  # MENU LATERAL
  # ==============================
  with st.sidebar:
    if authenticator.logout():
      st.cache_data.clear()
      st.session_state.clear()
      st.rerun()

    st.divider()
    st.caption(f"👤 Olá, {st.session_state['name']}")

    st.title("💰 Finanças")

    pagina = st.radio(
      "Navegação",
      [
        "📈 Rendimentos",
        "🏦 Investimentos",
        "💸 Gastos",
        "📋 Planejamento",
      ]
    )

  # ==============================
  # DESPACHO DA PÁGINA SELECIONADA
  # ==============================
  if pagina == "📈 Rendimentos":
    render_rendimentos(df)
  elif pagina == "🏦 Investimentos":
    render_investimentos(df_inv)
  elif pagina == "💸 Gastos":
    render_gastos(df_gastos)
  elif pagina == "📋 Planejamento":
    render_planejamento(df, df_plan_salvo, sheet_id, dados_key)


# ==============================
# ERROS DE LOGIN
# ==============================
elif st.session_state["authentication_status"] is False:
  st.error("Usuário ou senha inválidos.")
elif st.session_state["authentication_status"] is None:
  st.info("Informe usuário e senha para continuar.")
