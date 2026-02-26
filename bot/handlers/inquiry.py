from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from bot.services.constants import CONS_TIPO, CONS_INSTITUICAO
from bot.services.finance_service import consultar_resumo

async def start_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Gastos', 'Valor investido', 'Saldo restante']]
    await update.message.reply_text(
        '🔍 **Nova Consulta**\nO que gostaria de consultar?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return CONS_TIPO

async def get_tipo_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['consulta_tipo'] = update.message.text
    await update.message.reply_text(
        f'De qual **instituição** deseja ver os dados?',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    return CONS_INSTITUICAO

async def exibir_resultado_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    instituicao = update.message.text
    tipo_consulta = context.user_data.get('consulta_tipo')
    
    valor_retornado = consultar_resumo(instituicao)

    resumo = (
        f"📊 **Resultado da Consulta**\n\n"
        f"🔹 **Tipo:** {tipo_consulta}\n"
        f"🏦 **Instituição:** {instituicao}\n"
        f"💰 **Valor:** R$ {valor_retornado}"
    )

    await update.message.reply_text(resumo, parse_mode='Markdown')
    context.user_data.clear()
    return ConversationHandler.END