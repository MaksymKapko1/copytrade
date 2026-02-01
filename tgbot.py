import logging
import aiohttp
from datetime import datetime
from config import BOT_TOKEN, CHANNEL_ID, TARGET_ID

logger = logging.getLogger("Notifier")

async def send_telegram_request(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"⚠️ Ошибка Telegram: {await response.text()}")
    except Exception as e:
        logger.error(f"⚠️ Не удалось отправить: {e}")

async def send_whale_alert(trade, coin_name):
    asker = trade.get('ask_account_id')
    bidder = trade.get('bid_account_id')

    if bidder == TARGET_ID:
        header = "🟢 <b>WHALE BOUGHT (LONG)</b>"
    else:
        header = "🔴 <b>WHALE SOLD (SHORT)</b>"

    amount_usd = trade.get('usd_amount')
    price = trade.get('price')
    size = trade.get('size')
    tx_hash = trade.get('tx_hash')

    raw_ts = trade.get('timestamp')
    human_time = "Unknown"
    if raw_ts:
        # Фикс микросекунд/миллисекунд
        if raw_ts > 100000000000000:
            raw_ts /= 1000000
        elif raw_ts > 10000000000:
            raw_ts /= 1000
        human_time = datetime.fromtimestamp(raw_ts).strftime('%H:%M:%S %d.%m.%Y')

        message = (
            f"{header}\n\n"
            f"🪙 <b>Asset:</b> {coin_name}\n"
            f"💰 <b>Value:</b> ${amount_usd}\n"
            f"📉 <b>Price:</b> {price}\n"
            f"📦 <b>Size:</b> {size}\n"
            f"🕒 <b>Time:</b> {human_time}\n\n"
        )

        await send_telegram_request(message)
        logger.info(f"📤 Уведомление отправлено: {coin_name} | ${amount_usd}")