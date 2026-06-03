import pandas as pd
import plotly.express as px
import streamlit as st

from data.extract import GoogleSheetsReadError
from etl.transform import FinanceDataPipeline


ALOCACOES_PADRAO = [
  {"categoria": "Contas / Despesas", "valor": 0.0},
  {"categoria": "Investimentos", "valor": 0.0},
  {"categoria": "Reserva / Poupança", "valor": 0.0},
]


def calcular_receita_planejamento(df_rendimentos: pd.DataFrame, mes_atual: pd.Period) -> float:
  """Calcula a receita do mês atual usada como base do planejamento."""
  if df_rendimentos.empty or "Data Fim" not in df_rendimentos.columns or "Rendimento" not in df_rendimentos.columns:
    return 0.0

  mask_atual = pd.to_datetime(df_rendimentos["Data Fim"]).dt.to_period("M") == mes_atual
  return float(df_rendimentos.loc[mask_atual, "Rendimento"].sum())


def buscar_planejamento_existente(df_plan_salvo: pd.DataFrame, mes_str: str) -> pd.DataFrame:
  """Retorna o planejamento salvo para o mês informado, quando existir."""
  if df_plan_salvo.empty or "Mês" not in df_plan_salvo.columns:
    return pd.DataFrame()

  return df_plan_salvo[df_plan_salvo["Mês"] == mes_str].copy()


def montar_alocacoes_de_planejamento(plan_existente: pd.DataFrame, receita_mes: float) -> list[dict]:
  """Converte linhas salvas de planejamento para o formato da sessão."""
  if plan_existente.empty:
    return []

  receita_salva = float(plan_existente.iloc[0]["Receita"]) if "Receita" in plan_existente.columns else receita_mes
  return [
    {
      "categoria": row["Categoria"],
      "valor": float(row["Valor"]) if "Valor" in plan_existente.columns else round(float(row["Percentual"]) / 100 * receita_salva, 2)
    }
    for _, row in plan_existente.iterrows()
  ]


def calcular_resumo_planejamento(alocacoes: list[dict], receita: float) -> dict:
  """Calcula total, percentual e restante das alocações."""
  total_val = sum(a["valor"] for a in alocacoes)
  total_pct = (total_val / receita * 100) if receita > 0 else 0.0
  restante = receita - total_val

  return {
    "total_val": total_val,
    "total_pct": total_pct,
    "restante": restante,
    "salvar_disabled": abs(restante) >= 0.01 or not alocacoes,
  }


def montar_payload_alocacoes(alocacoes: list[dict], receita: float) -> list[dict]:
  """Monta o payload usado para salvar o planejamento."""
  return [
    {
      "categoria": a["categoria"],
      "percentual": round(a["valor"] / receita * 100, 2) if receita > 0 else 0.0,
      "valor": round(a["valor"], 2)
    }
    for a in alocacoes
  ]


def montar_preview_planejamento(alocacoes: list[dict], receita: float) -> pd.DataFrame:
  """Monta o DataFrame de prévia do planejamento."""
  alocacoes_preview = [
    {
      "Categoria": a["categoria"],
      "Valor (R$)": round(a["valor"], 2),
      "Percentual (%)": round(a["valor"] / receita * 100, 1) if receita > 0 else 0.0,
    }
    for a in alocacoes
    if a["categoria"].strip()
  ]

  return pd.DataFrame(alocacoes_preview)


def calcular_resumo_historico_planejamento(df_hist: pd.DataFrame) -> dict:
  """Calcula os indicadores do histórico de planejamento."""
  return {
    "receita_hist": float(df_hist.iloc[0]["Receita"]) if "Receita" in df_hist.columns else 0.0,
    "total_alocado": df_hist["Valor"].sum() if "Valor" in df_hist.columns else 0.0,
    "categorias": len(df_hist),
  }


def _inicializar_alocacoes():
  if "plan_alocacoes" not in st.session_state:
    st.session_state.plan_alocacoes = [aloc.copy() for aloc in ALOCACOES_PADRAO]


def _render_formulario_planejamento(receita_mes, mes_periodo, mes_proximo, mes_str, sheet_id, dados_key, plan_mes_key):
  st.subheader(f"Configurar alocações — {mes_str}")

  receita_input = st.number_input(
    "💵 Receita do mês (R$)",
    min_value=0.0,
    value=receita_mes,
    step=100.0,
    format="%.2f",
    key="plan_receita"
  )
  if mes_periodo == mes_proximo:
    st.caption("📌 Estimativa baseada nas receitas do mês atual. Ajuste conforme necessário.")

  st.divider()
  st.markdown("**Categorias e valores**")

  alocacoes_atuais = st.session_state.plan_alocacoes
  alocacoes_novas = []
  indices_remover = []

  for idx, aloc in enumerate(alocacoes_atuais):
    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
    cat = c1.text_input(
      "Categoria",
      value=aloc["categoria"],
      key=f"plan_cat_{idx}",
      label_visibility="collapsed",
      placeholder="Nome da categoria"
    )
    val = c2.number_input(
      "R$ ",
      min_value=0.0,
      value=float(aloc.get("valor", 0.0)),
      step=50.0,
      format="%.2f",
      key=f"plan_val_{idx}",
      label_visibility="collapsed"
    )
    pct_calc = (val / receita_input * 100) if receita_input > 0 else 0.0
    c3.markdown(f"<div style='padding-top:8px; color: gray; font-size:0.85rem'>{pct_calc:.1f}%</div>", unsafe_allow_html=True)

    remover = c4.button("✕", key=f"plan_rm_{idx}", help="Remover categoria")
    if remover:
      indices_remover.append(idx)
    else:
      alocacoes_novas.append({"categoria": cat, "valor": val})

  if indices_remover:
    st.session_state.plan_alocacoes = alocacoes_novas
    st.rerun()

  if st.button("➕ Adicionar categoria"):
    st.session_state.plan_alocacoes.append({"categoria": "Nova categoria", "valor": 0.0})
    st.rerun()

  resumo = calcular_resumo_planejamento(alocacoes_novas, receita_input)

  if alocacoes_novas:
    if abs(resumo["restante"]) < 0.01:
      st.success(f"✅ Total alocado: R$ {resumo['total_val']:,.2f} (100%)")
    elif resumo["restante"] > 0:
      st.warning(f"⚠️ Faltam R$ {resumo['restante']:,.2f} ({100 - resumo['total_pct']:.1f}%) para alocar")
    else:
      st.error(f"⚠️ Excedeu em R$ {abs(resumo['restante']):,.2f} ({resumo['total_pct']:.1f}% da receita)")

  st.divider()

  if st.button(
    "💾 Salvar Planejamento",
    type="primary",
    disabled=resumo["salvar_disabled"],
    width='stretch'
  ):
    st.session_state.plan_alocacoes = alocacoes_novas
    alocacoes_payload = montar_payload_alocacoes(alocacoes_novas, receita_input)

    try:
      pipeline = FinanceDataPipeline(
        sheet_id=sheet_id,
        credentials_dict=st.secrets["gcp_service_account"]
      )
      pipeline.extractor.save_planejamento(
        mes=mes_str,
        receita=receita_input,
        alocacoes=alocacoes_payload
      )

      del st.session_state[dados_key]
      if plan_mes_key in st.session_state:
        del st.session_state[plan_mes_key]

      st.success(f"Planejamento de {mes_str} salvo com sucesso! 🎉")
      st.rerun()

    except GoogleSheetsReadError as e:
      st.error("Erro ao salvar o planejamento na planilha.")
      st.exception(e)

  return alocacoes_novas, receita_input


def _render_preview_planejamento(alocacoes_novas, receita_input, mes_str):
  st.subheader("Prévia")
  df_preview = montar_preview_planejamento(alocacoes_novas, receita_input)

  if not df_preview.empty:
    cols_metric = st.columns(min(len(df_preview), 3))
    for i, row in df_preview.iterrows():
      cols_metric[i % len(cols_metric)].metric(
        label=row["Categoria"],
        value=f"R$ {row['Valor (R$)']:,.2f}",
        delta=f"{row['Percentual (%)']:.1f}%"
      )

    st.divider()

    st.dataframe(
      df_preview,
      hide_index=True,
      width='stretch',
      column_config={
        "Percentual (%)": st.column_config.NumberColumn(format="%.1f %%"),
        "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
      }
    )

    if df_preview["Valor (R$)"].sum() > 0:
      fig = px.pie(
        df_preview,
        values="Valor (R$)",
        names="Categoria",
        title=f"Distribuição — {mes_str}",
        hole=0.4,
      )
      fig.update_traces(textinfo="percent+label")
      st.plotly_chart(fig, width='stretch')
  else:
    st.info("Adicione categorias ao planejamento para visualizar a prévia.")


def _render_historico_planejamento(df_plan_salvo):
  st.subheader("📂 Histórico de Planejamentos Salvos")

  if df_plan_salvo.empty or "Mês" not in df_plan_salvo.columns:
    st.info("Nenhum planejamento salvo encontrado.")
  else:
    meses_salvos = sorted(df_plan_salvo["Mês"].unique(), reverse=True)

    mes_hist = st.selectbox(
      "Selecione o mês",
      meses_salvos,
      key="plan_hist_mes"
    )
    df_hist = df_plan_salvo[df_plan_salvo["Mês"] == mes_hist].copy()

    if not df_hist.empty:
      resumo = calcular_resumo_historico_planejamento(df_hist)
      col_m1, col_m2, col_m3 = st.columns(3)
      col_m1.metric("Receita base", f"R$ {resumo['receita_hist']:,.2f}")
      col_m2.metric("Total alocado", f"R$ {resumo['total_alocado']:,.2f}")
      col_m3.metric("Categorias", resumo["categorias"])

      st.divider()

      col_tabela, col_grafico = st.columns([1, 1], gap="large")

      with col_tabela:
        st.markdown("**Distribuição por categoria**")
        st.dataframe(
          df_hist[["Categoria", "Valor", "Percentual"]],
          hide_index=True,
          width='stretch',
          column_config={
            "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            "Percentual": st.column_config.NumberColumn("Percentual (%)", format="%.1f %%"),
          }
        )

      with col_grafico:
        if "Valor" in df_hist.columns and df_hist["Valor"].sum() > 0:
          fig_hist = px.pie(
            df_hist,
            values="Valor",
            names="Categoria",
            title=f"Distribuição — {mes_hist}",
            hole=0.4,
          )
          fig_hist.update_traces(textinfo="percent+label")
          st.plotly_chart(fig_hist, width='stretch')
        else:
          st.info("Sem valores para exibir no gráfico.")


def render_planejamento(df_rendimentos, df_plan_salvo, sheet_id, dados_key):
  """Renderiza a página de planejamento mensal."""
  st.header("📋 Planejamento Mensal")
  _inicializar_alocacoes()

  mes_atual = pd.Period(pd.Timestamp.today(), "M")
  mes_proximo = mes_atual + 1

  opcoes_mes = {
    mes_atual.strftime("%m/%Y"): mes_atual,
    mes_proximo.strftime("%m/%Y"): mes_proximo,
  }

  with st.sidebar:
    st.subheader("Filtros")
    mes_label = st.radio(
      "Mês de referência",
      list(opcoes_mes.keys()),
      format_func=lambda x: f"{'Este mês' if x == mes_atual.strftime('%m/%Y') else 'Próximo mês'} ({x})",
      key="plan_mes_sel"
    )
    mes_periodo = opcoes_mes[mes_label]
    mes_str = mes_periodo.strftime("%m/%Y")

  receita_mes = calcular_receita_planejamento(df_rendimentos, mes_atual)
  plan_existente = buscar_planejamento_existente(df_plan_salvo, mes_str)

  plan_mes_key = f"plan_loaded_{mes_str}"
  if not plan_existente.empty and plan_mes_key not in st.session_state:
    receita_mes = float(plan_existente.iloc[0]["Receita"]) if "Receita" in plan_existente.columns else receita_mes
    st.session_state.plan_alocacoes = montar_alocacoes_de_planejamento(plan_existente, receita_mes)
    st.session_state[plan_mes_key] = True

  tab_plan, tab_hist = st.tabs(["📝 Planejamento", "📂 Histórico"])

  with tab_plan:
    col_form, col_preview = st.columns([1, 1], gap="large")

    with col_form:
      alocacoes_novas, receita_input = _render_formulario_planejamento(
        receita_mes,
        mes_periodo,
        mes_proximo,
        mes_str,
        sheet_id,
        dados_key,
        plan_mes_key
      )

    with col_preview:
      _render_preview_planejamento(alocacoes_novas, receita_input, mes_str)

  with tab_hist:
    _render_historico_planejamento(df_plan_salvo)
