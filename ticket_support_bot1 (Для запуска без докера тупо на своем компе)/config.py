# Third-party
from dotenv import load_dotenv

# Standard
import os


load_dotenv()  # Load environment variables from .env

BASE = os.path.dirname(os.path.abspath(__file__))

project = {
    'base': BASE,
    'storage': BASE + '/storage'
}

bot = {
    'token': os.getenv('BOT_TOKEN'),
}

database = {
    'host': os.getenv('DATABASE_HOST'),
    'port': os.getenv('DATABASE_PORT'),
    'user': os.getenv('DATABASE_USER'),
    'password': os.getenv('DATABASE_PASSWORD'),
}


DEFAULT_CHANNEL_ID = -1002146462642 # channel Telegram ID
DEFAULT_CHANNEL_URL = 'https://t.me/channel' # channel Telegram URL

admin_id = 5874045758 # admin Telegram ID
