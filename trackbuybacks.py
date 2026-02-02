# import asyncio
# import os
# import sys
# import json
# import websockets
# import logging
# from dotenv import load_dotenv
# from tgbot import send_buyback_alert
#
# TARGET_BUYER_ID = '32734'
# COIN_NAME = 'LIT'
# load_dotenv()
#
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(message)s',
#     datefmt='%H:%M:%S',
#     handlers=[logging.StreamHandler(sys.stdout)]
# )
# logger = logging.getLogger("Buybacks")
#
# try:
#     WS_URL = os.environ["WEBSOCKET_URL"]
# except KeyError:
#     print("❌ ОШИБКА: Нет WEBSOCKET_URL в .env")
#     sys.exit(1)
#
#
# async def track_buyback_wallet():
#     reconnect_delay = 2
#
#     logger.info(f"🚀 Запуск трекера. Цель: {TARGET_BUYER_ID}")
#
#     while True:
#         try:
#             async with websockets.connect(WS_URL, ping_interval=None) as websocket:
#                 logger.info(f"✅ Подключено к серверу")
#                 reconnect_delay = 2
#
#                 msg = {"type": "subscribe", "channel": "trade/2049"}
#                 await websocket.send(json.dumps(msg))
#                 logger.info("📩 Подписка отправлена")
#
#                 while True:
#                     response = await websocket.recv()
#                     data = json.loads(response)
#                     msg_type = data.get('type')
#
#                     if msg_type == 'ping':
#                         logger.info("❤️ Получен PING, отправляю PONG...")
#                         pong_msg = {"type": "pong"}
#                         await websocket.send(json.dumps(pong_msg))
#                         continue
#                     trades = data.get('trades')
#
#                     if trades and isinstance(trades, list):
#                         for trade in trades:
#                             bid_account_id = str(trade.get('bid_account_id'))
#
#                             if bid_account_id == TARGET_BUYER_ID:
#                                 logger.info(f"СДЕЛКА НАЙДЕНА")
#                                 await send_buyback_alert(trade)
#
#         except (websockets.exceptions.ConnectionClosedError, OSError) as e:
#             logger.warning(f"⚠️ Разрыв соединения: {e}")
#             logger.info(f"⏳ Реконнект через {reconnect_delay} сек...")
#             await asyncio.sleep(reconnect_delay)
#
#             reconnect_delay = min(reconnect_delay * 2, 60)
#
#         except Exception as e:
#             logger.error(f"❌ Критическая ошибка: {e}")
#             await asyncio.sleep(5)
#
#
# if __name__ == "__main__":
#     try:
#         asyncio.run(track_buyback_wallet())
#     except KeyboardInterrupt:
#         print("🛑 Стоп.")