import logging
import aiohttp
from config import BOT_TOKEN, CHANNEL_ID

logger = logging.getLogger("TelegramService")

class TelegramBot:
    def __init__(self, token, channel_id):
        self.url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.channel_id = channel_id

    async def send_message(self, text, parse_mode="html"):
        payload = {
            "chat_id": self.channel_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"⚠️ Ошибка TG {response.status}: {await response.text()}")
        except Exception as e:
            logger.error(f"❌ Network Error TG: {e}")
bot = TelegramBot(BOT_TOKEN, CHANNEL_ID)
