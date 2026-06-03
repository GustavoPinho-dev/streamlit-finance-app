import pandas as pd
import plotly.express as px
import streamlit as st

from services.dates import parse_date_br
from services.utils import get_data_resumo, padronizar_string


CATEGORIAS_CONTAS = ["Contas - Fixo", "Contas - Variável"]


def calcular_totais_gastos(df_filtro: pd.DataFrame, df_gastos: pd.DataFrame, instituicao: str) -> dict:
  """Calcula os indicadores exibidos no resumo mensal de gastos."""
  data_resumo = get_data_resumo(df_filtro, instituicao)
  dados_acumulados = get_data_resumo(df_gastos, instituicao)
  reserva_disponivel = dados_acumulados["Receita Total"] - (
    dados_acumulados["Gastos"] + dados_acumulados["Total Investido"]
  )
  saldo_mes_disponivel = data_resumo["Receita Total"] - (
    data_resumo["Gastos"] + data_resumo["Total Investido"]
  )
  despesas_contas = df_filtro[df_filtro["Categoria"].isin(CATEGORIAS_CONTAS)]

  total_despesas = despesas_contas["Valor"].sum()
  total_outros = (
    df_filtro
    .loc[~df_filtro["Categoria"].isin(CATEGORIAS_CONTAS), "Valor"]
    .sum()
  )

  return {
    "data_resumo": data_resumo,
    "reserva_disponivel": reserva_disponivel,
    "saldo_mes_disponivel": saldo_mes_disponivel,
    "total_despesas": total_despesas,
    "total_outros": total_outros,
  }


def filtrar_gastos_por_periodo(df_gastos: pd.DataFrame, mes_selecionado, tipo_filtro: str, today=None) -> pd.DataFrame:
  """Filtra gastos pelo mês e, opcionalmente, até a data atual."""
  df_filtro = df_gastos[df_gastos["Mês"] == mes_selecionado].copy()

  if tipo_filtro == "Até o dia atual":
    hoje = parse_date_br(today if today is not None else pd.Timestamp.today())
    df_filtro = df_filtro[df_filtro["Data"] <= hoje]

  return df_filtro


def render_gastos(df_gastos):
  """Renderiza a página de gastos."""
  st.header("💸 Gastos")

  instituicoes = pd.unique(df_gastos["Instituição"])

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

  df_filtro = filtrar_gastos_por_periodo(df_gastos, mes_selecionado, tipo_filtro)
  tab_resumo, tab_div = st.tabs(["Resumo Mensal", "Divisão"])

  with tab_resumo:
    for instituicao in instituicoes:
      totais = calcular_totais_gastos(df_filtro, df_gastos, instituicao)
      data_resumo = totais["data_resumo"]

      with st.container(border=True):
        st.image(f"images/{padronizar_string(instituicao)}_logo.png", width=70)

        col_receita, col_despesas, col_reserva = st.columns(3)
        col_saldo, col_total_investido, col_saldo_mes = st.columns(3)

        col_receita.metric("Receitas", f"R$ {data_resumo['Receita Total']:,.2f}")
        col_despesas.metric(
          "Despesas",
          f"R$ {data_resumo['Gastos']:,.2f}",
          help=f"{totais['total_despesas']:,.2f} (Contas) + {(data_resumo['Gastos'] - totais['total_despesas']):,.2f} (Outros)"
        )
        col_saldo.metric("Saldo em Conta", f"R$ {data_resumo['Saldo Conta']:,.2f}")
        col_total_investido.metric("Total Investido", f"R$ {data_resumo['Total Investido']:,.2f}")
        col_reserva.metric(
          "Reserva Total Disponível",
          f"R$ {totais['reserva_disponivel']:,.2f}",
          f"{totais['saldo_mes_disponivel']:,.2f}"
        )
        col_saldo_mes.metric("Saldo Mês Disponível", f"R$ {totais['saldo_mes_disponivel']:,.2f}")

  with tab_div:
    inst_selected = st.selectbox(
      "Instituição",
      instituicoes,
    )

    df_desp = df_filtro[(df_filtro["Tipo"] == "Despesa") & (df_filtro["Instituição"] == inst_selected)]

    if not df_desp.empty:
      fig = px.pie(
        df_desp,
        values="Valor",
        names="Categoria",
        title="Distribuição das Despesas"
      )
      st.plotly_chart(fig)
    else:
      st.info("Nenhuma despesa encontrada para o período selecionado.")

    st.dataframe(
      df_desp,
      hide_index=True,
      column_config={
        "Valor": st.column_config.NumberColumn("Valor", format="R$ %f"),
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY")
      }
    )
