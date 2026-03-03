from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from bot.services.constants import *
from bot.services.utils import is_valid_format_date
from bot.services.finance_service import FinanceService
import streamlit as st

def get_sheet_id_by_username(username: str) -> str:
  users = st.secrets.get('auth', {}).get('credentials', {}).get('usernames', {})
  if username and username in users and 'sheet_id' in users[username]:
    return users[username]['sheet_id']

  return st.secrets['SHEET_ID']


# --- INÍCIO REGISTRO ---
async def start_financeiro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    if tipo == 'Receita':
        await update.message.reply_text('Qual a **descrição**?', parse_mode='Markdown')
        return DESCRICAO
    elif tipo == 'Investimentos':
        await update.message.reply_text('Qual o **produto**? (Ex: CDB)', parse_mode='Markdown')
        return PRODUTO
    elif tipo == 'Rendimentos':
        await update.message.reply_text('Qual a **Data de Início**? (Ex: 01/01/2024)', parse_mode='Markdown')
        return DATA_INICIO
    else:
        await update.message.reply_text('Qual a **categoria**?', parse_mode='Markdown')
        return CATEGORIA

async def get_data_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data_input = update.message.text
    if not is_valid_format_date(data_input):
        await update.message.reply_text('⚠️ *Formato inválido.* (Ex: 01/01/2024):', parse_mode='Markdown')
        return DATA_INICIO
    context.user_data['data_inicio'] = data_input
    await update.message.reply_text('Qual a **Data de Fim**? (Ex: 31/01/2024)', parse_mode='Markdown')
    return DATA_FIM

async def get_data_fim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data_input = update.message.text
    if not is_valid_format_date(data_input):
        await update.message.reply_text('⚠️ *Formato inválido.* (Ex: 31/01/2024):', parse_mode='Markdown')
        return DATA_FIM
    context.user_data['data_fim'] = data_input
    await update.message.reply_text('Qual a **instituição** pagadora?', parse_mode='Markdown')
    return INSTITUICAO

async def get_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['categoria'] = update.message.text
    await update.message.reply_text('Qual a **instituição**? (Ex: BTG, Itaú, Caixa)', parse_mode='Markdown')
    return INSTITUICAO

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
    await update.message.reply_text('Qual o **vencimento**? (Ex: 12/12/2026 ou N/A)', parse_mode='Markdown')
    return VENCIMENTO

async def get_vencimento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data_input = update.message.text
    if data_input.strip().upper() != 'N/A' and not is_valid_format_date(data_input):
        await update.message.reply_text('⚠️ *Formato inválido.* (Ex: 12/12/2026 ou N/A):', parse_mode='Markdown')
        return VENCIMENTO
    context.user_data['vencimento'] = data_input
    await update.message.reply_text('Qual o **indicador/taxa**? (Ex: 100% CDI)', parse_mode='Markdown')
    return INDICADOR

async def get_indicador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['indicador'] = update.message.text
    await update.message.reply_text('Qual a **instituição** do investimento?', parse_mode='Markdown')
    return INSTITUICAO

async def get_instituicao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['instituicao'] = update.message.text 
    tipo = context.user_data['tipo']
    if tipo in ['Investimentos', 'Receita', 'Rendimentos']:
        return await finalizar_registro(update, context)
    await update.message.reply_text('Para finalizar, qual a **descrição**?', parse_mode='Markdown')
    return DESCRICAO

async def get_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['descricao'] = update.message.text
    tipo = context.user_data['tipo']
    if tipo == 'Receita':
        await update.message.reply_text('Qual a **instituição** da receita?', parse_mode='Markdown')
        return INSTITUICAO
    return await finalizar_registro(update, context)

async def finalizar_registro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dados = context.user_data
    tipo = dados['tipo']
    resumo = f"✅ **{tipo} registrado!**\n💰 Valor: R$ {dados['valor']}\n🏦 Instituição: {dados.get('instituicao', '')}\n"
    
    if tipo == 'Investimentos':
        resumo += f"📦 Produto: {dados.get('produto')}\n🏷️ Tipo: {dados.get('tipo_invest')}\n📅 Vencimento: {dados.get('vencimento')}\n📈 Taxa: {dados.get('indicador')}"
    elif tipo == 'Rendimentos':
        resumo += f"🗓️ Período: {dados.get('data_inicio')} a {dados.get('data_fim')}"
    elif tipo == 'Receita':
        resumo += f"📝 Descrição: {dados.get('descricao')}"
    else: 
        resumo += f"📂 Categoria: {dados.get('categoria')}\n📝 Descrição: {dados.get('descricao')}"

    username = update.effective_user.username if update.effective_user else None
    sheet_id = get_sheet_id_by_username(username)
    finance_service = FinanceService(sheet_id, st.secrets["gcp_service_account"])
    
    sucesso = finance_service.salvar_registro(dados)
    if sucesso:
        await update.message.reply_text(resumo, parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ Erro ao salvar na planilha.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('❌ Ação cancelada.', reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END