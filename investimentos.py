import streamlit as st
import pandas as pd
import plotly.express as px
from google_sheets import connect_to_sheets, read_sheet_by_name
from google.oauth2 import service_account
from utils import format_moeda_to_numeric

st.set_page_config(page_title="Finanças", page_icon="💰")

SHEET_ID = "1dRWdt00sFQe5WnNMm6C4NZg1X5GBzfi6YH1npO908Uk"
#CREDENTIALS_FILE = "service_account.json"

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

@st.cache_resource
def get_client():
    return connect_to_sheets()

client = get_client()

df = read_sheet_by_name(client, SHEET_ID, "Rendimentos")
df = format_moeda_to_numeric(df)

df["Data Inicio"] = pd.to_datetime(df["Data Inicio"], dayfirst=True).dt.date
df["Data Fim"] = pd.to_datetime(df["Data Fim"], dayfirst=True).dt.date

# Exibição dos dados no App
exp1 = st.expander("Rendimentos")
tab_data, tab_stats = exp1.tabs(tabs=["Dados", "Histórico de Rendimento"])

with tab_data:
  columns_fmt = {"Rendimento": st.column_config.NumberColumn("Rendimento", format="R$ %f")}
  st.dataframe(df, hide_index=True, column_config=columns_fmt)

with tab_stats:
  st.line_chart(df, x='Data Fim', y="Rendimento")

# Leitura da aba de investimentos
exp2 = st.expander("Investimentos")
tab_data_inv, tab_div_inv = exp2.tabs(tabs=["Investimentos", "Divisão dos Investimentos"])

df_inv = read_sheet_by_name(client, SHEET_ID, "Investimentos")
df_inv = format_moeda_to_numeric(df_inv)

df_inv["Vencimento"] = pd.to_datetime(df_inv["Vencimento"], dayfirst=True).dt.date

# Cria o par Produto x Indicador
df_inv['Tipo'] = df_inv.apply(
  lambda r: f"{r['Produto']} - {r['Indicador']}" if pd.notnull(r['Indicador']) else str(r['Produto']),
  axis=1
).astype(str)

total_selic = df_inv.query("Indicador == 'SELIC'")["Valor"].sum()

with tab_data_inv:
  invest_columns_fmt = {"Valor": st.column_config.NumberColumn("Valor", format="R$ %f")}
  st.dataframe(df_inv, hide_index=True, column_config=invest_columns_fmt)

with tab_div_inv:
  # Criação do gráfico de divisão dos rendimentos
  fig = px.pie(
    df_inv, 
    names="Tipo", 
    values="Valor", 
    title="Distribuição dos Investimentos"
  )

  # Exibir no Streamlit
  st.plotly_chart(fig)

exp3 = st.expander("Gastos")
with exp3:
  df_gastos = read_sheet_by_name(client, SHEET_ID, "Gastos")

  # Converter datas
  df_gastos["Data"] = pd.to_datetime(df_gastos["Data"], dayfirst=True)
  df_gastos["Mês"] = df_gastos["Data"].dt.to_period("M")

  # ================================
  # FILTRO FIXO (APARECE EM TODAS AS TABS)
  # ================================
  col_f1, col_f2 = st.columns(2)

  meses = sorted(df_gastos["Mês"].astype(str).unique())
  mes_selecionado = col_f1.selectbox(
      "Selecione o mês",
      meses,
      key="mes_gastos_global"
  )

  tipo_filtro = col_f2.radio(
      "Filtrar dados por:",
      ["Mês inteiro", "Até o dia atual"],
      horizontal=True,
      key="tipo_filtro_global"
  )

  # ================================
  # APLICA FILTRO UMA ÚNICA VEZ
  # ================================
  df_filtro = df_gastos[df_gastos["Mês"] == mes_selecionado].copy()

  df_filtro = format_moeda_to_numeric(df_filtro)

  if tipo_filtro == "Até o dia atual":
      hoje = pd.Timestamp.today().normalize()
      df_filtro = df_filtro[df_filtro["Data"] <= hoje]

  # ================================
  # TABS
  # ================================
  tab_gastos_mensais, tab_div_gastos, tab_est_gastos = st.tabs(
      ["Gastos Mensais", "Divisão de Gastos", "Estimativa de Gastos"]
  )

# Converter datas
df_gastos["Data"] = pd.to_datetime(df_gastos["Data"], dayfirst=True)
df_gastos["Mês"] = df_gastos["Data"].dt.to_period("M")

df_gastos = format_moeda_to_numeric(df_gastos)

with tab_gastos_mensais:
  total_receitas = df_filtro[df_filtro["Tipo"] == "Receita"]["Valor"].sum()
  total_despesas = df_filtro[df_filtro["Tipo"] == "Despesa"]["Valor"].sum()
  total_investido = df_filtro[df_filtro["Categoria"] == "Investimentos"]["Valor"].sum()
  saldo = total_receitas - (total_despesas + total_investido)

  col1, col2 = st.columns(2)
  col3, col4 = st.columns(2)
  col1.metric("Receitas", f"R$ {total_receitas:,.2f}")
  col2.metric("Despesas", f"R$ {total_despesas:,.2f}")
  col3.metric("Saldo", f"R$ {saldo:,.2f}", delta=saldo)
  col4.metric("Total Investido", f"R$ {total_investido:,.2f}")

with tab_div_gastos:
  st.header("📊 Despesas por categoria")

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
      df_filtro,
      use_container_width=True,
      column_config={"Valor": st.column_config.NumberColumn("Valor", format="R$ %f")}
  )

with tab_est_gastos:
  st.subheader("📈 Planejamento Financeiro")

  col_renda, col_despesa, col_sobra = st.columns(3)

  renda_mensal = col_renda.number_input(
      "Renda Mensal",
      min_value=0.0,
      value=float(total_receitas),
      format="%.2f"
  )

  despesa_mensal = col_despesa.number_input(
      "Despesa Mensal",
      min_value=0.0,
      value=float(total_despesas),
      format="%.2f"
  )

  valor_a_ser_investido = st.number_input(
      "Valor investido",
      min_value=0.0,
      format="%.2f"
  )

  sobra = renda_mensal - (despesa_mensal + valor_a_ser_investido)

  col_sobra.metric(
      "Valor disponível para planejamento",
      f"R$ {sobra:,.2f}",
      delta=sobra
  )

  st.divider()

  st.markdown("### 🎯 Destinos do dinheiro que sobra")

  if "objetivos" not in st.session_state:
    st.session_state.objetivos = []

  with st.form("form_objetivos"):
    col1, col2, col3 = st.columns(3)

    nome = col1.text_input("Objetivo")
    valor_mensal = col2.number_input("Valor mensal destinado", min_value=0.0)
    prazo = col3.number_input("Prazo (meses)", min_value=1, step=1)

    adicionar = st.form_submit_button("Adicionar objetivo")

    if adicionar and nome and valor_mensal > 0:
      st.session_state.objetivos.append({
        "Objetivo": nome,
        "Valor mensal": valor_mensal,
        "Prazo (meses)": prazo,
        "Total acumulado": valor_mensal * prazo
      })
  
    if st.session_state.objetivos:
      df_plan = pd.DataFrame(st.session_state.objetivos)

      total_planejado = df_plan["Valor mensal"].sum()

      st.markdown("### 📊 Resumo do planejamento")

      col_a, col_b = st.columns(2)
      col_a.metric("Total destinado por mês", f"R$ {total_planejado:,.2f}")
      col_b.metric(
          "Saldo após planejamento",
          f"R$ {(sobra - total_planejado):,.2f}",
          delta=sobra - total_planejado
      )

      if total_planejado > sobra:
          st.error("⚠️ O valor planejado é maior que a sobra mensal.")
      else:
          st.success("✅ Planejamento dentro do limite da sobra.")

      st.dataframe(
          df_plan,
          use_container_width=True,
          column_config={
              "Valor mensal": st.column_config.NumberColumn("Valor mensal", format="R$ %f"),
              "Total acumulado": st.column_config.NumberColumn("Total acumulado", format="R$ %f")
          }
      )
    
      fig = px.pie(
          df_plan,
          values="Valor mensal",
          names="Objetivo",
          title="Distribuição da sobra por objetivo"
      )
      st.plotly_chart(fig, use_container_width=True)