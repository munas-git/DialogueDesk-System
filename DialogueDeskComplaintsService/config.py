import os
from dotenv import load_dotenv


load_dotenv()
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_PASSWORD")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")