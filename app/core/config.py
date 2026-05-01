import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

SECRET_KEY = os.getenv("SECRET_KEY")
GEMMA_KEY = os.getenv("GEMMA_API_KEY")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY")
ADMIN_ID_TG = int(os.getenv("ADMIN_ID_TG") or 1)
