# Third-party
from dotenv import load_dotenv

# Standard
import os

load_dotenv()  # Load environment variables from .env

BASE = os.path.dirname(os.path.abspath(__file__))

project = {"base": BASE, "storage": BASE + "/storage"}

bot = {
    "token": os.getenv("BOT_TOKEN"),
}

database = {
    "host": os.getenv("DATABASE_HOST"),
    "port": os.getenv("DATABASE_PORT"),
    "user": os.getenv("DATABASE_USER"),
    "password": os.getenv("DATABASE_PASSWORD"),
}

# Канал (можно отключить, поставив DEFAULT_CHANNEL_ID = 0)
DEFAULT_CHANNEL_ID = int(os.getenv("DEFAULT_CHANNEL_ID", 0))
DEFAULT_CHANNEL_URL = os.getenv("DEFAULT_CHANNEL_URL", "")

# Главный админ (твой Telegram ID)
admin_id = int(os.getenv("ADMIN_ID", 0))
