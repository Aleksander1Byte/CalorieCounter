import os

from dotenv import load_dotenv
from aiogram.types import ReactionTypeEmoji

load_dotenv()

TG_BOT_KEY = os.getenv("TG_BOT_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")
backend_url = f"http://{BACKEND_URL}:{BACKEND_PORT}/v1"
REACTION_EMOJIS = [
    ReactionTypeEmoji(emoji=i)
    for i in [
        "❤",
        "👍",
        "🔥",
        "🥰",
        "👏",
        "😁",
        "🤔",
        "👌",
        "🕊",
        "👌",
        "🕊",
        "❤‍🔥",
        "🍌",
        "🏆",
        "🌚",
        "🌭",
    ]
]
