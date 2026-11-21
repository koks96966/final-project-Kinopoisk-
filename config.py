import os
from dotenv import load_dotenv
from pathlib import Path

# Ищем .env в корне проекта, где бы ни запускался pytest
load_dotenv(Path(__file__).resolve().parent / ".env")

BASE_URL = "https://api.kinopoisk.dev"
SITE_URL = "https://www.kinopoisk.ru"
API_TOKEN = os.getenv("KINOPOISK_API_KEY", "")
REQUEST_TIMEOUT = 15