# Telegram rerlated
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# others
from TelegramAgentOps import AsyncAgent
from config import TELEGRAM_API_KEY

agent = AsyncAgent()

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



# Defining message handler that responds to any text
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_id = update.effective_user.id  # Get the user's ID (if needed)

    try:
        # Call the AsyncAgent's answer method to get a response
        agent_response = await agent.answer(user_message)
        
        # Reply to the user with the agent's response
        await update.message.reply_text(agent_response.get("output", "Oh ohh... I can't respond right now. Please try again later 🤧😷"))
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Oh ohh... I can't respond right now. Please try again later 🤧😷")

# Main function to run the bot
if __name__ == "__main__":
    print("Starting bot...")

    # Create the application
    app = ApplicationBuilder().token(TELEGRAM_API_KEY).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Add message handler for all text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))

    print("Bot running...")
    app.run_polling()