from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  await update.message.reply_text(
    '❌ Ação cancelada.', 
    reply_markup=ReplyKeyboardRemove()
  )
  context.user_data.clear()
  return ConversationHandler.END