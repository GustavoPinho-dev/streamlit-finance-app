import streamlit as st
import pandas as pd
import plotly.express as px
from data.google_sheets import read_sheet_by_name
from config.auth import autenticar
from google.oauth2 import service_account
from services.utils import format_moeda_to_numeric, normalize_df_inv

# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
  page_title="Finanças",
  page_icon="💰",
  layout="wide"
)

SHEET_ID = "1dRWdt00sFQe5WnNMm6C4NZg1X5GBzfi6YH1npO908Uk"

credentials = service_account.Credentials.from_service_account_info(
  st.secrets["gcp_service_account"]
)

# ==============================
# CACHE DE DADOS
# ==============================
@st.cache_data(show_spinner="Carregando dados financeiros...")
def carregar_dados(sheet_id):
  return {
    "rendimentos": read_sheet_by_name(sheet_id, "Rendimentos"),
    "investimentos": read_sheet_by_name(sheet_id, "Investimentos"),
    "gastos": read_sheet_by_name(sheet_id, "Gastos"),
  }

# ==============================
# AUTENTICAÇÃO
# ==============================
authenticator = autenticar()

if st.session_state["authentication_status"]:

  # ==============================
  # CARREGA DADOS
  # ==============================
  if "dados" not in st.session_state:
    st.session_state["dados"] = carregar_dados(SHEET_ID)

  df = format_moeda_to_numeric(st.session_state["dados"]["rendimentos"])
  df_inv = format_moeda_to_numeric(st.session_state["dados"]["investimentos"])
  df_gastos = format_moeda_to_numeric(st.session_state["dados"]["gastos"])

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
      ]
    )

  # ==============================
  # 📈 RENDIMENTOS
  # ==============================
  if pagina == "📈 Rendimentos":
    st.header("📈 Rendimentos")

    df["Data Inicio"] = pd.to_datetime(df["Data Inicio"], dayfirst=True).dt.date
    df["Data Fim"] = pd.to_datetime(df["Data Fim"], dayfirst=True).dt.date

    tab_dados, tab_hist = st.tabs(["Dados", "Histórico"])

    with tab_dados:
      st.dataframe(
        df,
        hide_index=True,
        column_config={
          "Rendimento": st.column_config.NumberColumn("Rendimento", format="R$ %f"),
          "Data Inicio": st.column_config.DateColumn("Data Início", format="DD/MM/YYYY"),
          "Data Fim": st.column_config.DateColumn("Data Fim", format="DD/MM/YYYY")
        }
      )

    with tab_hist:
      st.line_chart(df, x="Data Fim", y="Rendimento")

  # ==============================
  # 🏦 INVESTIMENTOS
  # ==============================
  elif pagina == "🏦 Investimentos":
    st.header("🏦 Investimentos")

    df_inv = normalize_df_inv(df_inv)

    tab_lista, tab_div = st.tabs(["Lista", "Distribuição"])

    with tab_lista:
      st.dataframe(
        df_inv,
        hide_index=True,
        column_config={
          "Valor": st.column_config.NumberColumn("Valor", format="R$ %f"),
          "Vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY")
        }
      )

    with tab_div:
      fig = px.pie(
        df_inv,
        names="Tipo",
        values="Valor",
        title="Distribuição dos Investimentos"
      )
      st.plotly_chart(fig, use_container_width=True)

  # ==============================
  # 💸 GASTOS
  # ==============================
  elif pagina == "💸 Gastos":
    st.header("💸 Gastos")

    # Datas
    df_gastos["Data"] = pd.to_datetime(df_gastos["Data"], dayfirst=True)
    df_gastos["Mês"] = df_gastos["Data"].dt.to_period("M")

    # ------------------------------
    # FILTROS NO SIDEBAR
    # ------------------------------
    with st.sidebar:
      st.subheader("Filtros")

      meses = sorted(df_gastos["Mês"].unique())

      mes_selecionado = st.selectbox(
        "Mês",
        meses,
        index=len(meses) - 1,
        format_func=lambda x: x.strftime("%m/%Y"),
        key="mes_gastos_global"
      )

      tipo_filtro = st.radio(
        "Período",
        ["Mês inteiro", "Até o dia atual"],
        key="tipo_filtro_global"
      )

    # Aplica filtros
    df_filtro = df_gastos[df_gastos["Mês"] == mes_selecionado].copy()

    if tipo_filtro == "Até o dia atual":
      hoje = pd.Timestamp.today().normalize()
      df_filtro = df_filtro[df_filtro["Data"] <= hoje]

    # ------------------------------
    # TABS
    # ------------------------------
    tab_resumo, tab_div, tab_plan = st.tabs(
      ["Resumo Mensal", "Divisão", "Planejamento"]
    )

    # 🔹 RESUMO MENSAL
    with tab_resumo:
      total_receitas = df_filtro[df_filtro["Tipo"] == "Receita"]["Valor"].sum()
      total_despesas = df_filtro[df_filtro["Tipo"] == "Despesa"]["Valor"].sum()
      total_investido = df_filtro[df_filtro["Categoria"] == "Investimentos"]["Valor"].sum()
      saldo_anterior = df_filtro[df_filtro["Tipo"] == "Saldo"]["Valor"].sum()

      saldo = saldo_anterior + (total_receitas - (total_despesas + total_investido))

      col1, col2 = st.columns(2)
      col3, col4 = st.columns(2)

      col1.metric("Receitas", f"R$ {total_receitas:,.2f}")
      col2.metric("Despesas", f"R$ {total_despesas:,.2f}")
      col3.metric("Saldo", f"R$ {saldo:,.2f}")
      col4.metric("Total Investido", f"R$ {total_investido:,.2f}")

    # 🔹 DIVISÃO DE GASTOS
    with tab_div:
      df_desp = df_filtro[df_filtro["Tipo"] == "Despesa"]

      if not df_desp.empty:
        fig = px.pie(
          df_desp,
          values="Valor",
          names="Categoria",
          title="Distribuição das Despesas"
        )
        st.plotly_chart(fig, use_container_width=True)
      else:
        st.info("Nenhuma despesa encontrada para o período selecionado.")

      st.dataframe(
        df_desp,
        use_container_width=True,
        hide_index=True,
        column_config={
          "Valor": st.column_config.NumberColumn("Valor", format="R$ %f"),
          "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY")
        }
      )

    # 🔹 PLANEJAMENTO
    with tab_plan:
      col_plan_renda, col_plan_despesa = st.columns(2)
      col_plan_invest, col_plan_sobra = st.columns(2)

      renda = col_plan_renda.number_input("Renda Mensal", value=float(total_receitas))
      despesa = col_plan_despesa.number_input("Despesa Mensal", value=float(total_despesas))
      invest = col_plan_invest.number_input("Valor Investido", value=float(total_investido))

      sobra = renda - (despesa + invest)
      col_plan_sobra.metric("Valor disponível", f"R$ {sobra:,.2f}")

      if "objetivos" not in st.session_state:
        st.session_state.objetivos = []

      with st.form("form_objetivos"):
        nome = st.text_input("Objetivo")
        valor = st.number_input("Valor mensal", min_value=0.0)
        prazo = st.number_input("Prazo (meses)", min_value=1, step=1)

        submitted = st.form_submit_button("Adicionar")

        if submitted and nome:
          st.session_state["objetivos"].append({
              "Objetivo": nome,
              "Valor mensal": valor,
              "Prazo": prazo,
              "Total": valor * prazo
          })

      if st.session_state.objetivos:
        df_plan = pd.DataFrame(st.session_state.objetivos)

        st.dataframe(
          df_plan,
          use_container_width=True,
          hide_index=True,
          column_config={
            "Valor mensal": st.column_config.NumberColumn(format="R$ %f"),
            "Total": st.column_config.NumberColumn(format="R$ %f")
          }
        )

        fig = px.pie(
          df_plan,
          values="Valor mensal",
          names="Objetivo",
          title="Distribuição da sobra"
        )
        st.plotly_chart(fig, use_container_width=True)

# ==============================
# ERROS DE LOGIN
# ==============================
elif st.session_state["authentication_status"] is False:
  st.error("Usuário ou senha inválidos.")
elif st.session_state["authentication_status"] is None:
  st.info("Informe usuário e senha para continuar.")
