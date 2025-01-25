# import os  # Add this import at the top

# # other imports
# from telegram import Update
# from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# import asyncio
# from config import TELEGRAM_API_KEY
# from TelegramAgentOps import DialogueDeskAgent

# agent = DialogueDeskAgent()

# # start command definition
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.effective_user
#     await update.message.reply_text(
#         f"Hi {user.first_name}! 👋\n"
#         "How can I help you?"
#     )

# # Define the /help command
# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text(
#         "Available commands:\n\n"
#         "/start - Start the bot\n"
#         "/help - Get help\n"
#         "/make_report - Type your complaint/report\n"
#         "/report_update - Get the status update of your report (with id if multiple)\n"
#         "/cancel_notifications - Stop receiving notifications about your report progress (one or all)\n"
#         "/receive_notifications - Resume receiving notifications about your report progress (one or all)\n"
#         "\n\nBetter yet, just send me message regarding any of the above, and I'll reply!\n"
#     )


# async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user_message = update.message.text
#     message_date = str(update.message.date.strftime('%Y-%m-%d'))
#     users_first_name = str(update.effective_user.first_name)

#     try:
#         # Call the AsyncAgent's answer method to get a response
#         agent_response = agent.handle_message(
#             f"{user_message}.",
#             f"This message was sent on date: {message_date}. ",
#             users_first_name
#         )
#         agent_response = agent_response.replace("!", "\!").replace(".", "\.").replace("-", "\-")
#         await update.message.reply_text(agent_response, parse_mode="MarkdownV2")
    
#     except Exception as e:
#         print(f"Error in generating response: {e}")
#         await update.message.reply_text(
#             "Oh ohh... I can't respond right now. Please try again later 🤧😷"
#         )


# async def main():
#     print("Starting bot...")
#     application = ApplicationBuilder().token(TELEGRAM_API_KEY).build()
    
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("help", help_command))
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
    
#     print("Bot running...")

#     # Set the port from environment variable
#     port = int(os.environ.get('PORT', 8000))  # Default to 8000 if PORT isn't set

#     await application.initialize()
#     await application.start()
#     await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

#     # Start the bot on the specified port (not usually required for Telegram bot but for HTTP apps)
#     print(f"Running on port {port}")

#     try:
#         await asyncio.Event().wait()
#     finally:
#         await application.stop()

# if __name__ == "__main__":
#     asyncio.run(main())


from flask import Flask
import os
import asyncio
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_API_KEY
from TelegramAgentOps import DialogueDeskAgent

app = Flask(__name__)

# Health check route
@app.route('/')
def health_check():
    return 'Bot is running', 200

# Telegram bot setup
agent = DialogueDeskAgent()

# Bot command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f"Hi {user.first_name}! 👋\nHow can I help you?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Available commands: ...")

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    users_first_name = str(update.effective_user.first_name)
    print(f"Received message from {users_first_name}: {user_message}")  # Log the input
    
    try:
        agent_response = agent.handle_message(f"{user_message}.", users_first_name)
        print(f"Generated response: {agent_response}")  # Log the output
        await update.message.reply_text(agent_response)
    except Exception as e:
        print(f"Error in generating response: {e}")
        await update.message.reply_text("Oh ohh... I can't respond right now. Please try again later 🤧😷")


WEBHOOK_URL = "https://dialoguedesk-system.onrender.com/webhook"

async def run_bot():
    try:
        print("Starting Telegram bot...")
        application = ApplicationBuilder().token(TELEGRAM_API_KEY).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
        
        print("Setting webhook...")
        await application.initialize()
        await application.start()
        await application.updater.start_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 10000)),
            webhook_url=WEBHOOK_URL,
        )
    except Exception as e:
        print(f"Telegram bot startup error: {e}")


def run_flask_app():
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)

def start_telegram_bot():
    asyncio.run(run_bot())

async def main():
    loop = asyncio.get_event_loop()
    # Run Flask app
    flask_task = loop.run_in_executor(None, lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))))
    
    # Run Telegram bot
    bot_task = run_bot()

    await asyncio.gather(flask_task, bot_task)

if __name__ == "__main__":
    asyncio.run(main())