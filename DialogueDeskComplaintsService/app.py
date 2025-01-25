# Telegram rerlated
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# others
import asyncio
from config import TELEGRAM_API_KEY
from TelegramAgentOps import DialogueDeskAgent

agent = DialogueDeskAgent()

# start command definition
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! 👋\n"
        "How can I help you?"
    )

# Define the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Available commands:\n\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/make_report - Type your complaint/report\n"
        "/report_update - Get the status update of your report (with id if multiple)\n"
        "/cancel_notifications - Stop receiving notifications about your report progress (one or all)\n"
        "/receive_notifications - Resume receiving notifications about your report progress (one or all)\n"
        "\n\nBetter yet, just send me message regarding any of the above, and I'll reply!\n"
    )



async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    message_date = str(update.message.date.strftime('%Y-%m-%d'))
    # user_id = str(update.effective_user.id)
    users_first_name = str(update.effective_user.first_name)

    try:
        # Call the AsyncAgent's answer method to get a response
        agent_response = agent.handle_message(
            f"{user_message}.",
            f"This message was sent on date: {message_date}. ",
            users_first_name
        )
        agent_response = agent_response.replace("!", "\!").replace(".", "\.").replace("-", "\-")
        await update.message.reply_text(agent_response, parse_mode="MarkdownV2")
    
    except Exception as e:
        print(f"Error in generating response: {e}")
        await update.message.reply_text(
            "Oh ohh... I can't respond right now. Please try again later 🤧😷"
        )


async def main():
    print("Starting bot...")
    application = ApplicationBuilder().token(TELEGRAM_API_KEY).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
    
    print("Bot running...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    # Keep the bot running until interrupted
    try:
        await asyncio.Event().wait()
    finally:
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())