import asyncio
import websockets
import json
import logging
import sys

from config import CHANNELS_TO_LISTEN, ID_TO_COIN, TARGET_ID, WS_URL
from tgbot import send_whale_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("WhaleBot")

async def keepalive(websocket, worker_id, channel_name):
    while True:
        try:
            await asyncio.sleep(25)

            msg = {"type": "subscribe", "channel": channel_name}
            await websocket.send(json.dumps(msg))

        except Exception:
            break


async def socket_worker(worker_id, channels_subset):
    logger.info(f"🤖 [Worker {worker_id}] Запуск. Каналов: {len(channels_subset)}")

    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=None) as websocket:
                logger.info(f"✅ [Worker {worker_id}] Connected")

                if channels_subset:
                    asyncio.create_task(keepalive(websocket, worker_id, channels_subset[0]))

                for i, channel in enumerate(channels_subset):
                    msg = {"type": "subscribe", "channel": channel}
                    await websocket.send(json.dumps(msg))
                    if i % 10 == 0: await asyncio.sleep(0.1)

                logger.info(f"📡 [Worker {worker_id}] Все подписки отправлены.")

                while True:
                    response = await websocket.recv()
                    data = json.loads(response)

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

        except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError) as e:
            logger.error(f"❌ [Worker {worker_id}] Разрыв: {e}")
            await asyncio.sleep(5)
            continue
        except Exception as e:
            logger.error(f"❌ [Worker {worker_id}] Ошибка: {e}")
            await asyncio.sleep(5)


async def main():
    CHUNK_SIZE = 80
    chunks = [CHANNELS_TO_LISTEN[i:i + CHUNK_SIZE] for i in range(0, len(CHANNELS_TO_LISTEN), CHUNK_SIZE)]

    tasks = []
    logger.info(f"🔥 Каналов: {len(CHANNELS_TO_LISTEN)}. Воркеров: {len(chunks)}.")

    for i, chunk in enumerate(chunks):
        task = asyncio.create_task(socket_worker(i + 1, chunk))
        tasks.append(task)

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")