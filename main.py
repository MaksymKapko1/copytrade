import asyncio
import websockets
import json
import logging
import sys
import time

from config import TARGET_ID, WS_URL, TARGET_BUYER_ID, API_URL
from tgbot import send_whale_alert, send_buyback_report
from services.MarketAPI import MarketAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("WhaleBot")

ID_TO_COIN = {}
CHANNELS_TO_LISTEN = []

class BuybackStats:
    def __init__(self):
        self.processed_ids = set()
        self.reset()

    def reset(self):
        self.total_tokens = 0.0  # Общее кол-во токенов
        self.total_usdc = 0.0  # Общий объем в $
        self.count = 0  # Кол-во сделок
        self.start_time = time.time()
        self.coin_name = "Unknown"
        self.tx_hash = None
        self.processed_ids.clear()# Список монет (если их несколько)

    def add_trade(self, trade, coin_name):
        try:
            unique_id = trade.get('tx_hash')
            if unique_id in self.processed_ids:
                return
            if unique_id:
                self.processed_ids.add(unique_id)

            size = float(trade.get('size', 0))
            price = float(trade.get('price', 0))
            usd_val = float(trade.get('usd_amount', 0))
            if usd_val == 0:
                usd_val = size * price

            self.total_tokens += size
            self.total_usdc += usd_val
            self.count += 1

            self.coin_name = coin_name
            self.tx_hash = trade.get('tx_hash', '')
        except Exception as e:
            logger.error(f"Ошибка при подсчете статистики: {e}")

stats = BuybackStats()

async def socket_worker(worker_id, channels_subset):
    logger.info(f"🤖 [Worker {worker_id}] Запуск. Каналов: {len(channels_subset)}")

    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=None) as websocket:
                logger.info(f"✅ [Worker {worker_id}] Connected")

                for i, channel in enumerate(channels_subset):
                    msg = {"type": "subscribe", "channel": channel}
                    await websocket.send(json.dumps(msg))
                    if i % 10 == 0: await asyncio.sleep(0.1)

                logger.info(f"📡 [Worker {worker_id}] Все подписки отправлены.")

                while True:
                    response = await websocket.recv()
                    data = json.loads(response)

                    msg_type = data.get('type')

                    if msg_type == 'ping':
                        logger.info(f"❤️ [Worker {worker_id}] PING получен -> PONG отправлен")
                        pong_msg = {"type": "pong"}
                        await websocket.send(json.dumps(pong_msg))
                        continue

                    trades = data.get('trades')
                    if trades:
                        for trade in trades:
                            asker = trade.get('ask_account_id')
                            bidder = trade.get('bid_account_id')

                            if asker == TARGET_ID or bidder == TARGET_ID:
                                m_id = trade.get('market_id')
                                coin_name = ID_TO_COIN.get(m_id, f"Market #{m_id}")

                                logger.info(f"🔔 [Worker {worker_id}] СДЕЛКА!")
                                await send_whale_alert(trade, coin_name)
                            elif bidder == TARGET_BUYER_ID:
                                #logger.info(f"BUYBACKS FOUND")
                                m_id = trade.get('market_id')
                                coin_name = ID_TO_COIN.get(m_id, f"Market #{m_id}")
                                stats.add_trade(trade, coin_name)

        except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError) as e:
            logger.error(f"❌ [Worker {worker_id}] Разрыв: {e}")
            await asyncio.sleep(5)
            continue
        except Exception as e:
            logger.error(f"❌ [Worker {worker_id}] Ошибка: {e}")
            await asyncio.sleep(5)


async def report_loop(interval_minutes=10):
    logger.info(f"⏳ Запущен репортер байбеков (интервал {interval_minutes} мин)")

    while True:
        await asyncio.sleep(interval_minutes * 60)

        if stats.count > 0:
            duration = int((time.time() - stats.start_time) / 60)
            avg_price = stats.total_usdc / stats.total_tokens if stats.total_tokens > 0 else 0
            coins_str = ", ".join(stats.coins)

            current_lit, current_usdc = await MarketAPI.get_wallet_balance(TARGET_BUYER_ID)
            message = (
                f"🛒 **ОТЧЕТ ПО БАЙБЕКАМ (TWAP)**\n"
                f"⏱ За последние {duration} мин\n"
                f"{20*'-'}\n"
                f"💎 Токен: {stats.coin_name}\n"
                f"📊 Всего сделок: {stats.count}\n"
                f"💰 Выкуплено на: **${stats.total_usdc:,.2f}**\n"
                f"📦 Объем токенов: {stats.total_tokens:,.4f}\n"
                f"📉 Средняя цена входа: ${avg_price:.4f}\n"
                f"{20*'-'}\n"
                f"🏦 **Текущий баланс Buyer:**\n"
                f"🔥 LIT: `{current_lit:,.2f}`\n"
                f"💵 USDC: `{current_usdc:,.2f}`\n\n"
                f"{20*'-'}\n"
                f"🔗 [Last TX Explorer](https://app.lighter.xyz/explorer/logs/{stats.tx_hash})"
            )

            from tgbot import send_buyback_report
            await send_buyback_report(message)

            logger.info(f"📉 Отчет отправлен. Сумма: ${stats.total_usdc}")

            stats.reset()
        else:
            logger.info("📉 Байбеков за период не было, отчет пропущен.")

async def main():
    global ID_TO_COIN, CHANNELS_TO_LISTEN
    logger.info("⏳ Fetching markets from API...")
    ID_TO_COIN, CHANNELS_TO_LISTEN = await MarketAPI.fetch_markets(API_URL)

    if not CHANNELS_TO_LISTEN:
        logger.error("❌ Failed to load markets or empty list. Exiting.")
        return

    CHUNK_SIZE = 80
    chunks = [CHANNELS_TO_LISTEN[i:i + CHUNK_SIZE] for i in range(0, len(CHANNELS_TO_LISTEN), CHUNK_SIZE)]

    tasks = []
    logger.info(f"🔥 Каналов: {len(CHANNELS_TO_LISTEN)}. Воркеров: {len(chunks)}.")

    for i, chunk in enumerate(chunks):
        task = asyncio.create_task(socket_worker(i + 1, chunk))
        tasks.append(task)

    reporter_task = asyncio.create_task(report_loop(interval_minutes=10))
    tasks.append(reporter_task)

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")