import streamlit as st


def render_rendimentos(df):
  """Renderiza a página de rendimentos."""
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
