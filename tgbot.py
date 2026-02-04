import logging
from datetime import datetime
from config import BOT_TOKEN, CHANNEL_ID, TARGET_ID
from services.telegram import TelegramBot  # Импортируем наш класс

logger = logging.getLogger("Notifier")

# Инициализируем бота ОДИН раз
bot = TelegramBot(BOT_TOKEN, CHANNEL_ID)


async def send_buyback_report(message_text):
    # Используем метод класса, Markdown для отчетов
    await bot.send_message(message_text, parse_mode="Markdown")


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

    raw_ts = trade.get('timestamp')
    human_time = "Unknown"

    if raw_ts:
        # Твоя логика конвертации времени
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

    # Отправляем через сервис (HTML по умолчанию)
    await bot.send_message(message)
    logger.info(f"📤 Уведомление отправлено: {coin_name} | ${amount_usd}")