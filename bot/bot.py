from typing import Final
import streamlit as st
from data.google_sheets import save_data_sheets
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)

# Configurações extraídas do Streamlit
TOKEN: Final = st.secrets['bot_token']
SHEET_ID = st.secrets["SHEET_ID"] 

# Definição dos Estados da Conversa
(TIPO, VALOR, CATEGORIA, INSTITUICAO, DESCRICAO, 
 PRODUTO, TIPO_INVEST, VENCIMENTO, INDICADOR) = range(9)

async def start_financeiro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Opções atualizadas conforme solicitado
    reply_keyboard = [['Gastos', 'Investimentos', 'Receita', 'Rendimentos']]
    await update.message.reply_text(
        '💰 **Novo Registro Financeiro**\nO que vamos lançar agora?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return TIPO

async def get_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['tipo'] = update.message.text
    await update.message.reply_text(
        f'Selecionado: **{update.message.text}**\nQual o valor? (Ex: 100)',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    return VALOR

async def get_valor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['valor'] = update.message.text 
    tipo = context.user_data['tipo']

    # Ajuste na lógica de roteamento para o plural
    if tipo == 'Receita':
        return await finalizar_registro(update, context)
    elif tipo == 'Investimentos':
        await update.message.reply_text('Qual o **produto**? (Ex: CDB, Tesouro)', parse_mode='Markdown')
        return PRODUTO
    else: # Gastos ou Rendimentos
        await update.message.reply_text('Qual a **categoria**? (Ex: Consumo, Fixo, Variável)', parse_mode='Markdown')
        return CATEGORIA

# --- FLUXO A: GASTOS / RENDIMENTOS ---
async def get_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['categoria'] = update.message.text
    await update.message.reply_text('Qual a **instituição**? (Ex: BTG, Itaú, Caixa)', parse_mode='Markdown')
    return INSTITUICAO

# --- FLUXO B: INVESTIMENTOS ---
async def get_produto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Aplicação', 'Retirada']]
    context.user_data['produto'] = update.message.text
    await update.message.reply_text(
        'Qual o **tipo**? (Aplicação ou Retirada)',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return TIPO_INVEST

async def get_tipo_invest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['tipo_invest'] = update.message.text
    await update.message.reply_text('Qual o **vencimento**?', parse_mode='Markdown')
    return VENCIMENTO

async def get_vencimento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['vencimento'] = update.message.text
    await update.message.reply_text('Qual o **indicador/taxa**?', parse_mode='Markdown')
    return INDICADOR

async def get_indicador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['indicador'] = update.message.text
    await update.message.reply_text('Qual a **instituição** onde o investimento foi feito?', parse_mode='Markdown')
    return INSTITUICAO

# --- CONVERGÊNCIA: INSTITUIÇÃO ---
async def get_instituicao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['instituicao'] = update.message.text 
    tipo = context.user_data['tipo']

    # Ajuste na verificação para o plural
    if tipo == 'Investimentos':
        return await finalizar_registro(update, context)
    
    await update.message.reply_text('Para finalizar, qual a **descrição**?', parse_mode='Markdown')
    return DESCRICAO

async def get_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['descricao'] = update.message.text
    return await finalizar_registro(update, context)

# --- CARGA (LOAD) ---
async def finalizar_registro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dados = context.user_data
    tipo = dados['tipo']
    
    resumo = f"✅ **{tipo} registrado!**\n💰 Valor: R$ {dados['valor']}\n🏦 Instituição: {dados.get('instituicao', 'N/A')}\n"
    
    if tipo == 'Investimentos':
        resumo += (f"📦 Produto: {dados.get('produto')}\n🏷️ Tipo: {dados.get('tipo_invest')}\n"
                   f"📅 Vencimento: {dados.get('vencimento')}\n📈 Taxa: {dados.get('indicador')}")
    elif tipo != 'Receita':
        resumo += f"📂 Categoria: {dados.get('categoria')}\n📝 Descrição: {dados.get('descricao')}"

    print(f"DEBUG: {dados}")
    save_data_sheets(SHEET_ID, dados) 

    await update.message.reply_text(resumo, parse_mode='Markdown')
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('❌ Registro cancelado.', reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

def run_bot():
    print('Bot iniciado...')
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('registrar', start_financeiro)],
        states={
            # REGEX atualizado para refletir o plural
            TIPO: [MessageHandler(filters.Regex('^(Gastos|Investimentos|Receita|Rendimentos)$'), get_tipo)],
            VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_valor)],
            CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_categoria)],
            INSTITUICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_instituicao)],
            DESCRICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_descricao)],
            PRODUTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_produto)],
            TIPO_INVEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tipo_invest)],
            VENCIMENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_vencimento)],
            INDICADOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_indicador)],
        },
        fallbacks=[CommandHandler('cancelar', cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
    