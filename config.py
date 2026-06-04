import os
from dotenv import load_dotenv

load_dotenv() # Загружает переменные из .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_TOKEN = os.getenv("GEMINI_TOKEN")
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
DATABASE_NAME = os.getenv("DATABASE_NAME")