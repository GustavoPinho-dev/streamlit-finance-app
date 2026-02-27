from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from bot.services.constants import CONS_TIPO, CONS_INSTITUICAO
from bot.services.finance_service import FinanceService
import streamlit as st


def get_sheet_id_by_username(username: str) -> str:
  users = st.secrets.get('auth', {}).get('credentials', {}).get('usernames', {})
  if username and username in users and 'sheet_id' in users[username]:
    return users[username]['sheet_id']

  return st.secrets['SHEET_ID']

async def start_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Gastos', 'Total Investido', 'Saldo Conta', 'Saldo Mês']]
    await update.message.reply_text(
        '🔍 **Nova Consulta**\nO que gostaria de consultar?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return CONS_TIPO

async def get_tipo_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['consulta_tipo'] = update.message.text

    username = update.effective_user.username if update.effective_user else None
    sheet_id = get_sheet_id_by_username(username)
    finance_service = FinanceService(sheet_id)
    
    instituicoes = finance_service.get_instituicoes()
    reply_keyboard = [list(instituicoes)]

    await update.message.reply_text(
        f'De qual **instituição** deseja ver os dados?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return CONS_INSTITUICAO

async def exibir_resultado_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    instituicao = update.message.text
    tipo_consulta = context.user_data.get('consulta_tipo')
    
    username = update.effective_user.username if update.effective_user else None
    sheet_id = get_sheet_id_by_username(username)
    finance_service = FinanceService(sheet_id)

    result_consulta = finance_service.consultar_resumo(instituicao)

    resumo = (
        f"📊 **Resultado da Consulta (Mês atual)**\n\n"
        f"🔹 **Tipo:** {tipo_consulta}\n"
        f"🏦 **Instituição:** {instituicao}\n"
        f"💰 **Valor:** R$ {result_consulta[tipo_consulta]:,.2f}"
    )

    await update.message.reply_text(resumo, parse_mode='Markdown')
    context.user_data.clear()
    return ConversationHandler.END