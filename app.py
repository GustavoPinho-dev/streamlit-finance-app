import streamlit as st
import pandas as pd
import plotly.express as px
from config.auth import autenticar
from config.sheets import get_sheet_id_for_user
from services.utils import get_data_resumo, padronizar_string
from etl.transform import FinanceDataPipeline
from data.extract import GoogleSheetsAuthError, GoogleSheetsReadError
from bot.services.logger import get_logger


logger = get_logger(__name__)


def _mask_sheet_id(sheet_id: str) -> str:
  if not sheet_id:
    return "<vazio>"
  if len(sheet_id) <= 8:
    return "***"
  return f"{sheet_id[:4]}...{sheet_id[-4:]}"

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
  # 📈 RENDIMENTOS
  # ==============================
  if pagina == "📈 Rendimentos":
    st.header("📈 Rendimentos")

    tab_dados, tab_hist = st.tabs(["Dados", "Histórico"])

    with tab_dados:
      if not df.empty:
        st.dataframe(
          df,
          hide_index=True,
          column_config={
            "Rendimento": st.column_config.NumberColumn("Rendimento", format="R$ %f"),
            "Data Inicio": st.column_config.DateColumn("Data Início", format="DD/MM/YYYY"),
            "Data Fim": st.column_config.DateColumn("Data Fim", format="DD/MM/YYYY")
          }
        )
      else:
        st.info("Nenhum rendimento encontrado.")

    with tab_hist:
      if not df.empty:
        st.line_chart(df, x="Data Fim", y="Rendimento")
      else:
        st.info("Nenhum rendimento encontrado.")

  # ==============================
  # 🏦 INVESTIMENTOS
  # ==============================
  elif pagina == "🏦 Investimentos":
    st.header("🏦 Investimentos")

    tab_lista, tab_div = st.tabs(["Lista", "Distribuição"])
    df_aplicacoes = df_inv[df_inv["Operação"] == "Aplicação"].copy()
    df_retiradas = df_inv[df_inv["Operação"] == "Retirada"].copy()

    total_aplicado = df_aplicacoes["Valor"].sum() if not df_aplicacoes.empty else 0
    total_retirado = df_retiradas["Valor"].sum() if not df_retiradas.empty else 0
    saldo_investido = total_aplicado - total_retirado

    col_apl, col_ret, col_saldo = st.columns(3)
    col_apl.metric("Total aplicado", f"R$ {total_aplicado:,.2f}")
    col_ret.metric("Total retirado", f"R$ {total_retirado:,.2f}")
    col_saldo.metric("Saldo investido", f"R$ {saldo_investido:,.2f}")

    if total_retirado > 0:
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
      if not df_aplicacoes.empty:
        fig = px.pie(
          df_aplicacoes,
          names="Tipo",
          values="Valor",
          title="Distribuição dos Investimentos (somente aplicações)"
        )
        st.plotly_chart(fig)
      else:
        st.info("Nenhuma aplicação encontrada para exibir no gráfico.")


  # ==============================
  # 💸 GASTOS
  # ==============================
  elif pagina == "💸 Gastos":
    st.header("💸 Gastos")

    # Instituições
    instituicoes = pd.unique(df_gastos["Instituição"])

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
    tab_resumo, tab_div = st.tabs(
      ["Resumo Mensal", "Divisão"]
    )

    # 🔹 RESUMO MENSAL
    with tab_resumo:
      for i in instituicoes:
        data_resumo = get_data_resumo(df_filtro, i)
        dados_acumulados = get_data_resumo(df_gastos, i)
        reserva_disponivel = dados_acumulados['Receita Total'] - (dados_acumulados['Gastos'] + dados_acumulados["Total Investido"])
        saldo_mes_disponivel = data_resumo['Receita Total'] - (data_resumo['Gastos'] + data_resumo['Total Investido'])
        despesas_contas = df_filtro[df_filtro['Categoria'].isin(['Contas - Fixo', 'Contas - Variável'])]

        total_despesas = despesas_contas['Valor'].sum()
        total_outros = (
          df_filtro
          .loc[~df_filtro['Categoria'].isin(['Contas - Fixo', 'Contas - Variável']), 'Valor']
          .sum()
        )

        with st.container(border=True):
          st.image(f"images/{padronizar_string(i)}_logo.png", width=70)

          col_receita, col_despesas, col_reserva = st.columns(3)
          col_saldo, col_total_investido, col_saldo_mes = st.columns(3)

          col_receita.metric("Receitas", f"R$ {data_resumo['Receita Total']:,.2f}")
          col_despesas.metric("Despesas", f"R$ {data_resumo['Gastos']:,.2f}", help=f"{total_despesas:,.2f} (Contas) + {(data_resumo['Gastos'] - total_despesas):,.2f} (Outros)")
          col_saldo.metric("Saldo em Conta", f"R$ {data_resumo['Saldo Conta']:,.2f}")
          col_total_investido.metric("Total Investido", f"R$ {data_resumo['Total Investido']:,.2f}")
          col_reserva.metric("Reserva Total Disponível", f"R$ {reserva_disponivel:,.2f}", f"{saldo_mes_disponivel:,.2f}")
          col_saldo_mes.metric("Saldo Mês Disponível", f"R$ {saldo_mes_disponivel:,.2f}")

    # 🔹 DIVISÃO DE GASTOS
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

  # ==============================
  # 📋 PLANEJAMENTO (página dedicada)
  # ==============================
  elif pagina == "📋 Planejamento":
    st.header("📋 Planejamento Mensal")

    # ── Inicializa estado das alocações ──────────────────────────────────────
    if "plan_alocacoes" not in st.session_state:
      st.session_state.plan_alocacoes = [
        {"categoria": "Contas / Despesas", "valor": 0.0},
        {"categoria": "Investimentos",      "valor": 0.0},
        {"categoria": "Reserva / Poupança", "valor": 0.0},
      ]

    # ── SIDEBAR: seleção de mês (apenas mês atual e próximo) ─────────────────
    mes_atual  = pd.Period(pd.Timestamp.today(), "M")
    mes_proximo = mes_atual + 1

    opcoes_mes = {
      mes_atual.strftime("%m/%Y"):   mes_atual,
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
      mes_str = mes_periodo.strftime("%m/%Y")   # "MM/YYYY" — chave no Sheets

    # ── Receita base ─────────────────────────────────────────────────────────
    # Para o mês atual: soma das receitas do próprio mês no Sheets.
    # Para o próximo mês: usa a soma do mês atual como estimativa (melhor proxy disponível).
    receita_mes = 0.0
    if not df.empty and "Data Fim" in df.columns and "Rendimento" in df.columns:
      mask_atual = pd.to_datetime(df["Data Fim"]).dt.to_period("M") == mes_atual
      receita_mes_atual = float(df.loc[mask_atual, "Rendimento"].sum())

      if mes_periodo == mes_atual:
        receita_mes = receita_mes_atual
      else:
        # Próximo mês: sem receitas reais ainda → replica o mês atual
        receita_mes = receita_mes_atual

    # Carrega planejamento existente para o mês (se houver)
    print(df_plan_salvo)
    plan_existente = pd.DataFrame()
    if not df_plan_salvo.empty and "Mês" in df_plan_salvo.columns:
      plan_existente = df_plan_salvo[df_plan_salvo["Mês"] == mes_str].copy()

    # Pré-carrega alocações salvas ao mudar de mês
    plan_mes_key = f"plan_loaded_{mes_str}"
    if not plan_existente.empty and plan_mes_key not in st.session_state:
      receita_salva = float(plan_existente.iloc[0]["Receita"]) if "Receita" in plan_existente.columns else receita_mes
      receita_mes = receita_salva
      st.session_state.plan_alocacoes = [
        {
          "categoria": row["Categoria"],
          "valor": float(row["Valor"]) if "Valor" in plan_existente.columns else round(float(row["Percentual"]) / 100 * receita_salva, 2)
        }
        for _, row in plan_existente.iterrows()
      ]
      st.session_state[plan_mes_key] = True

    # ── Tabs principais ───────────────────────────────────────────────────────
    tab_plan, tab_hist = st.tabs(["📝 Planejamento", "📂 Histórico"])

    # ── TAB: Planejamento ─────────────────────────────────────────────────────
    with tab_plan:
      col_form, col_preview = st.columns([1, 1], gap="large")

      with col_form:
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

        # Renderiza campos para cada alocação existente
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
          # Percentual calculado dinamicamente
          pct_calc = (val / receita_input * 100) if receita_input > 0 else 0.0
          c3.markdown(f"<div style='padding-top:8px; color: gray; font-size:0.85rem'>{pct_calc:.1f}%</div>", unsafe_allow_html=True)

          remover = c4.button("✕", key=f"plan_rm_{idx}", help="Remover categoria")
          if remover:
            indices_remover.append(idx)
          else:
            alocacoes_novas.append({"categoria": cat, "valor": val})

        # Aplica remoções
        if indices_remover:
          st.session_state.plan_alocacoes = alocacoes_novas
          st.rerun()

        # Botão para adicionar nova categoria
        if st.button("➕ Adicionar categoria"):
          st.session_state.plan_alocacoes.append({"categoria": "Nova categoria", "valor": 0.0})
          st.rerun()

        # Validação: soma dos valores vs receita
        total_val = sum(a["valor"] for a in alocacoes_novas)
        total_pct = (total_val / receita_input * 100) if receita_input > 0 else 0.0
        restante = receita_input - total_val

        if alocacoes_novas:
          if abs(restante) < 0.01:
            st.success(f"✅ Total alocado: R$ {total_val:,.2f} (100%)")
          elif restante > 0:
            st.warning(f"⚠️ Faltam R$ {restante:,.2f} ({100 - total_pct:.1f}%) para alocar")
          else:
            st.error(f"⚠️ Excedeu em R$ {abs(restante):,.2f} ({total_pct:.1f}% da receita)")

        st.divider()

        # ── Botão Salvar ────────────────────────────────────────────────────
        salvar_disabled = abs(restante) >= 0.01 or not alocacoes_novas
        if st.button(
          "💾 Salvar Planejamento",
          type="primary",
          disabled=salvar_disabled,
          width='stretch'
        ):
          st.session_state.plan_alocacoes = alocacoes_novas

          alocacoes_payload = [
            {
              "categoria": a["categoria"],
              "percentual": round(a["valor"] / receita_input * 100, 2) if receita_input > 0 else 0.0,
              "valor": round(a["valor"], 2)
            }
            for a in alocacoes_novas
          ]

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

            # Invalida cache para recarregar planejamento atualizado
            del st.session_state[dados_key]
            if plan_mes_key in st.session_state:
              del st.session_state[plan_mes_key]

            st.success(f"Planejamento de {mes_str} salvo com sucesso! 🎉")
            st.rerun()

          except GoogleSheetsReadError as e:
            st.error("Erro ao salvar o planejamento na planilha.")
            st.exception(e)

      # ── Preview / Visualização ──────────────────────────────────────────────
      with col_preview:
        st.subheader("Prévia")

        # Monta lista de alocações com valores calculados
        alocacoes_preview = [
          {
            "Categoria": a["categoria"],
            "Valor (R$)": round(a["valor"], 2),
            "Percentual (%)": round(a["valor"] / receita_input * 100, 1) if receita_input > 0 else 0.0,
          }
          for a in alocacoes_novas
          if a["categoria"].strip()
        ]

        if alocacoes_preview:
          df_preview = pd.DataFrame(alocacoes_preview)

          # Métricas rápidas
          cols_metric = st.columns(min(len(alocacoes_preview), 3))
          for i, row in df_preview.iterrows():
            cols_metric[i % len(cols_metric)].metric(
              label=row["Categoria"],
              value=f"R$ {row['Valor (R$)']:,.2f}",
              delta=f"{row['Percentual (%)']:.1f}%"
            )

          st.divider()

          # Tabela resumo
          st.dataframe(
            df_preview,
            hide_index=True,
            width='stretch',
            column_config={
              "Percentual (%)": st.column_config.NumberColumn(format="%.1f %%"),
              "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
            }
          )

          # Gráfico de pizza
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

    # ── TAB: Histórico ────────────────────────────────────────────────────────
    with tab_hist:
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
          receita_hist = float(df_hist.iloc[0]["Receita"]) if "Receita" in df_hist.columns else 0.0

          # Métricas de resumo
          total_alocado = df_hist["Valor"].sum() if "Valor" in df_hist.columns else 0.0
          col_m1, col_m2, col_m3 = st.columns(3)
          col_m1.metric("Receita base", f"R$ {receita_hist:,.2f}")
          col_m2.metric("Total alocado", f"R$ {total_alocado:,.2f}")
          col_m3.metric("Categorias", len(df_hist))

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


# ==============================
# ERROS DE LOGIN
# ==============================
elif st.session_state["authentication_status"] is False:
  st.error("Usuário ou senha inválidos.")
elif st.session_state["authentication_status"] is None:
  st.info("Informe usuário e senha para continuar.")