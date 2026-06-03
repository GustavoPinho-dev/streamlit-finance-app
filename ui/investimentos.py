import pandas as pd
import plotly.express as px
import streamlit as st


def calcular_resumo_investimentos(df_inv: pd.DataFrame) -> dict:
  """Calcula totais de investimentos por operação."""
  if df_inv.empty or "Operação" not in df_inv.columns or "Valor" not in df_inv.columns:
    return {
      "total_aplicado": 0,
      "total_retirado": 0,
      "saldo_investido": 0,
    }

  df_aplicacoes = df_inv[df_inv["Operação"] == "Aplicação"].copy()
  df_retiradas = df_inv[df_inv["Operação"] == "Retirada"].copy()

  total_aplicado = df_aplicacoes["Valor"].sum() if not df_aplicacoes.empty else 0
  total_retirado = df_retiradas["Valor"].sum() if not df_retiradas.empty else 0

  return {
    "total_aplicado": total_aplicado,
    "total_retirado": total_retirado,
    "saldo_investido": total_aplicado - total_retirado,
  }


def calcular_distribuicao_investimentos(df_inv: pd.DataFrame) -> pd.DataFrame:
  """Calcula a distribuição líquida por tipo, descontando retiradas."""
  if df_inv.empty or not {"Tipo", "Operação", "Valor"}.issubset(df_inv.columns):
    return pd.DataFrame(columns=["Tipo", "Valor Líquido"])

  df_dist = df_inv.copy()
  df_dist["Valor Líquido"] = df_dist.apply(
    lambda row: -row["Valor"] if row["Operação"] == "Retirada" else row["Valor"],
    axis=1
  )

  df_dist = (
    df_dist
    .groupby("Tipo", as_index=False)["Valor Líquido"]
    .sum()
  )

  return df_dist[df_dist["Valor Líquido"] > 0]


def render_investimentos(df_inv):
  """Renderiza a página de investimentos."""
  st.header("🏦 Investimentos")

  tab_lista, tab_div = st.tabs(["Lista", "Distribuição"])
  resumo = calcular_resumo_investimentos(df_inv)

  col_apl, col_ret, col_saldo = st.columns(3)
  col_apl.metric("Total aplicado", f"R$ {resumo['total_aplicado']:,.2f}")
  col_ret.metric("Total retirado", f"R$ {resumo['total_retirado']:,.2f}")
  col_saldo.metric("Saldo investido", f"R$ {resumo['saldo_investido']:,.2f}")

  if resumo["total_retirado"] > 0:
    st.warning(
      "Foram encontradas operações de retirada. "
      "Elas não entram na soma de investimentos aplicados e são exibidas separadamente."
    )

  with tab_lista:
    if not df_inv.empty:
      st.dataframe(
        df_inv,
        hide_index=True,
        column_config={
          "Valor": st.column_config.NumberColumn("Valor", format="R$ %f"),
          "Vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
          "Operação": st.column_config.TextColumn("Operação")
        }
      )
    else:
      st.info("Nenhum investimento encontrado.")

  with tab_div:
    if not df_inv.empty:
      df_dist = calcular_distribuicao_investimentos(df_inv)

      if not df_dist.empty:
        fig = px.pie(
          df_dist,
          names="Tipo",
          values="Valor Líquido",
          title="Distribuição dos Investimentos considerando retiradas"
        )
        st.plotly_chart(fig)
      else:
        st.info("Nenhum saldo positivo de investimento encontrado para exibir no gráfico.")
    else:
      st.info("Nenhum investimento encontrado para exibir no gráfico.")
