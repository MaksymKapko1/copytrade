import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

try:
    BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
    CHANNEL_ID = os.environ["TG_CHANNEL_ID"]
    TARGET_ID = int(os.environ["TARGET_WHALE_ID"])
    WS_URL = os.environ["WEBSOCKET_URL"]
    API_URL = os.environ["API_MARKETS_URL"]
except KeyError as e:
    print(f"❌ ОШИБКА: Не найдена переменная окружения {e}. Проверь файл .env")
    sys.exit(1)

def load_all_markets():
    try:
        response = requests.get(API_URL, timeout=5)
        data = response.json()

        id_to_coin = {}
        channels_to_listen = []

        for market in data:
            m_index = market['market_index']
            symbol = market['symbol']

            if m_index is not None and symbol:
                id_to_coin[m_index] = symbol
                channels_to_listen.append(f"trade/{m_index}")
        print(f"✅ Успешно загружено {len(channels_to_listen)} маркетов.")
        return id_to_coin, channels_to_listen
    except Exception as e:
        print(f"❌ Ошибка при загрузке маркетов: {e}")
        sys.exit(1)
ID_TO_COIN, CHANNELS_TO_LISTEN = load_all_markets()