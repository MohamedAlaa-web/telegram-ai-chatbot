import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API keys and configure Gemini
API_KEY = os.getenv('API_KEY')
genai.configure(api_key=API_KEY)

# Store conversations
conversations = {}

# Async def for /start command with welcome message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Welcome to the Telegram AI Chatbot!')

# Async def for /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('This is a help message.')

# Async def for /clear command
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conversations.clear()
    await update.message.reply_text('Conversations cleared.')

# Async def to process user messages and get Gemini responses
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    response = await genai.chat(user_message)
    await update.message.reply_text(response)

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f'Update {update} caused error {context.error}')

# Main function to run the bot with polling
if __name__ == '__main__':
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('clear', clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    # Run the bot
    application.run_polling()