# telegram related
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes
from TelegramAgentOps import DialogueDeskAgent

# flask related
from flask import Flask, request

# others
import os
from config import TELEGRAM_API_KEY

app = Flask(__name__)
agent = DialogueDeskAgent()
bot = Bot(token=TELEGRAM_API_KEY)

# Define your Telegram handlers here
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! 👋\n"
        "How can I help you?"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Available commands:\n\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/make_report - Type your complaint/report\n"
        "/report_update - Get the status update of your report\n"
        "/cancel_notifications - Stop receiving notifications\n"
        "/receive_notifications - Resume receiving notifications\n"
    )

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    message_date = str(update.message.date.strftime('%Y-%m-%d'))
    users_first_name = str(update.effective_user.first_name)
    print(user_message)

    try:
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

# Flask route for the webhook to process updates
@app.route(f'/{TELEGRAM_API_KEY}', methods=['POST'])
async def webhook():
    json_update = request.get_json()
    update = Update.de_json(json_update, bot)
    # Use Application's process_update method to handle the update
    await ApplicationBuilder().token(TELEGRAM_API_KEY).build().process_update(update)
    return 'OK'

# Set webhook URL
def set_webhook():
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_URL')}/{TELEGRAM_API_KEY}"
    bot.set_webhook(url=webhook_url)

# Start the Flask app and webhook
if __name__ == "__main__":
    set_webhook()
    # Start the Flask server on the appropriate port (Render provides this via the PORT environment variable)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
