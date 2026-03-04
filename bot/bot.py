from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from bot.services.constants import *
from bot.handlers import registration, inquiry, common
from bot.services.logger import get_logger
import streamlit as st

logger = get_logger(__name__)


def run_bot():
    TOKEN = st.secrets['bot_token']
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('registrar', registration.start_financeiro),
            CommandHandler('consultar', inquiry.start_consulta)
        ],
        states={
            # Fluxo Registro
          TIPO: [MessageHandler(filters.Regex('^(Gastos|Investimentos|Receita|Rendimentos)$'), registration.get_tipo)],
          VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration.get_valor)],
          DATA_INICIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration.get_data_inicio)],
          DATA_FIM: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration.get_data_fim)],
          CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration.get_categoria)],
          INSTITUICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration.get_instituicao)],
          DESCRICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration.get_descricao)],
          PRODUTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration.get_produto)],
          TIPO_INVEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration.get_tipo_invest)],
          VENCIMENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration.get_vencimento)],
          INDICADOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration.get_indicador)],
  
          # Fluxo Consulta
          CONS_TIPO: [MessageHandler(filters.Regex('^(Gastos|Total Investido|Saldo Conta|Saldo Mês)$'), inquiry.get_tipo_consulta)],
          CONS_INSTITUICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, inquiry.exibir_resultado_consulta)],
        
        },
        fallbacks=[CommandHandler('cancelar', common.cancel)],
    )

    app.add_handler(conv_handler)
    logger.info('Bot iniciado e aguardando mensagens via polling.')
    app.run_polling()        