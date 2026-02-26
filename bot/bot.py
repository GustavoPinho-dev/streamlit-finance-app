import streamlit as st
from datetime import datetime
from typing import Final
from data.extract import save_data_sheets 
from services.utils import is_valid_format_date
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)

# --- CONFIGURAÇÕES ---
TOKEN: Final = st.secrets['bot_token']
SHEET_ID = st.secrets["SHEET_ID"] 

# Definição dos Estados da Conversa (Adicionado DATA_INICIO e DATA_FIM)
(TIPO, VALOR, CATEGORIA, INSTITUICAO, DESCRICAO, 
 PRODUTO, TIPO_INVEST, VENCIMENTO, INDICADOR, DATA_INICIO, DATA_FIM) = range(11)

(TIPO_CONSULTA) = range(1)

# --- INÍCIO ---
async def start_financeiro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Gastos', 'Investimentos', 'Receita', 'Rendimentos']]
    await update.message.reply_text(
        '💰 **Novo Registro Financeiro**\nO que vamos lançar agora?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return TIPO

async def start_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Gastos', 'Valor investido', 'Saldo restante']]
    await update.message.reply_text(
        'Nova consulta\nO que gostaria de consultar?',
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
        await update.message.reply_text('Qual a **descrição** da receita? (Ex: Salário, Freelance)', parse_mode='Markdown')
        return DESCRICAO
    elif tipo == 'Investimentos':
        await update.message.reply_text('Qual o **produto**? (Ex: CDB, Tesouro)', parse_mode='Markdown')
        return PRODUTO
    elif tipo == 'Rendimentos':
        await update.message.reply_text('Qual a **Data de Início**? (Ex: 01/01/2024)', parse_mode='Markdown')
        return DATA_INICIO
    else: # Gastos
        await update.message.reply_text('Qual a **categoria**? (Ex: Consumo, Fixo, Variável)', parse_mode='Markdown')
        return CATEGORIA

# --- FLUXO RENDIMENTOS (NOVO) ---
async def get_data_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  data_input = update.message.text
  
  # Validação da data
  if not is_valid_format_date(data_input):
    await update.message.reply_text(
      '⚠️ *Formato de data inválido.*\nPor favor, digite a **Data de Início** novamente (Ex: 01/01/2024):', 
      parse_mode='Markdown'
    )
    return DATA_INICIO # Retorna para o mesmo estado para tentar novamente

  context.user_data['data_inicio'] = data_input
  await update.message.reply_text('Qual a **Data de Fim**? (Ex: 31/01/2024)', parse_mode='Markdown')
  return DATA_FIM

async def get_data_fim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  data_input = update.message.text
  
  # Validação da data
  if not is_valid_format_date(data_input):
    await update.message.reply_text(
      '⚠️ *Formato de data inválido.*\nPor favor, digite a **Data de Fim** novamente (Ex: 31/01/2024):', 
      parse_mode='Markdown'
    )
    return DATA_FIM # Retorna para o mesmo estado

  context.user_data['data_fim'] = data_input
  await update.message.reply_text('Qual a **instituição** pagadora?', parse_mode='Markdown')
  return INSTITUICAO

# --- FLUXO GASTOS ---
async def get_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['categoria'] = update.message.text
    await update.message.reply_text('Qual a **instituição**? (Ex: BTG, Itaú, Caixa)', parse_mode='Markdown')
    return INSTITUICAO

# --- FLUXO INVESTIMENTOS ---
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
  
  # Validação da data (permitindo a exceção 'N/A' sugerida no seu prompt)
  if data_input.strip().upper() != 'N/A' and not is_valid_format_date(data_input):
    await update.message.reply_text(
      '⚠️ *Formato inválido.*\nPor favor, digite o **vencimento** novamente (Ex: 12/12/2026 ou N/A):', 
      parse_mode='Markdown'
    )
    return VENCIMENTO # Retorna para o mesmo estado

  context.user_data['vencimento'] = data_input
  await update.message.reply_text('Qual o **indicador/taxa**? (Ex: 100% CDI)', parse_mode='Markdown')
  return INDICADOR

async def get_indicador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['indicador'] = update.message.text
    await update.message.reply_text('Qual a **instituição** do investimento?', parse_mode='Markdown')
    return INSTITUICAO

# --- LOGICA COMPARTILHADA ---
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

# --- FINALIZAÇÃO ---
async def finalizar_registro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dados = context.user_data
    tipo = dados['tipo']
    
    resumo = f"✅ **{tipo} registrado!**\n💰 Valor: R$ {dados['valor']}\n🏦 Instituição: {dados.get('instituicao', '')}\n"
    
    if tipo == 'Investimentos':
        resumo += (f"📦 Produto: {dados.get('produto')}\n🏷️ Tipo: {dados.get('tipo_invest')}\n"
                   f"📅 Vencimento: {dados.get('vencimento')}\n📈 Taxa: {dados.get('indicador')}")
    elif tipo == 'Rendimentos':
        resumo += f"🗓️ Período: {dados.get('data_inicio')} a {dados.get('data_fim')}"
    elif tipo == 'Receita':
        resumo += f"📝 Descrição: {dados.get('descricao')}"
    else: # Gastos
        resumo += f"📂 Categoria: {dados.get('categoria')}\n📝 Descrição: {dados.get('descricao')}"

    # Salva no Google Sheets
    print(f'Dados recebidos: {dados}')
    sucesso = save_data_sheets(SHEET_ID, dados) 

    if sucesso:
        await update.message.reply_text(resumo, parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ Erro ao salvar na planilha.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('❌ Registro cancelado.', reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

def run_bot():
    app = Application.builder().token(TOKEN).build()
    print('Bot iniciado...')

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('registrar', start_financeiro)],
        states={
            TIPO: [MessageHandler(filters.Regex('^(Gastos|Investimentos|Receita|Rendimentos)$'), get_tipo)],
            VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_valor)],
            DATA_INICIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_data_inicio)],
            DATA_FIM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_data_fim)],
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