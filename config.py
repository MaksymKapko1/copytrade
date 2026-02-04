import os
import sys
from dotenv import load_dotenv

load_dotenv()

TARGET_BUYER_ID = 0

try:
    BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
    CHANNEL_ID = os.environ["TG_CHANNEL_ID"]
    TARGET_ID = int(os.environ["TARGET_WHALE_ID"])
    WS_URL = os.environ["WEBSOCKET_URL"]
    API_URL = os.environ["API_MARKETS_URL"]
except KeyError as e:
    print(f"❌ ОШИБКА: Не найдена переменная окружения {e}. Проверь файл .env")
    sys.exit(1)