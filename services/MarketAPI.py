import aiohttp
import logging

logger = logging.getLogger("MarketData")


class MarketAPI:
    @staticmethod
    async def fetch_markets(api_url):
        id_to_coin = {}
        channels_to_listen = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()

                        for market in data:
                            m_index = market.get('market_index')
                            symbol = market.get('symbol')

                            if m_index is not None and symbol:
                                id_to_coin[m_index] = symbol
                                channels_to_listen.append(f"trade/{m_index}")

                        logger.info(f"✅ Successfully loaded {len(channels_to_listen)} markets.")
                        return id_to_coin, channels_to_listen
                    else:
                        logger.error(f"❌ API Error fetching markets: {response.status}")
                        return {}, []
        except Exception as e:
            logger.error(f"❌ Error fetching markets: {e}")
            return {}, []

    @staticmethod
    async def get_wallet_balance(account_id):
        url = f"https://explorer.elliot.ai/api/accounts/{account_id}/assets"
        lit_bal = 0.0
        usdc_bal = 0.0

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        assets = data.get("assets", {})

                        for asset_id, info in assets.items():
                            symbol = info.get("symbol", "").upper()
                            balance_str = info.get("balance", "0")

                            if symbol == "LIT":
                                lit_bal = float(balance_str)
                            elif symbol == "USDC":
                                usdc_bal = float(balance_str)
                    else:
                        logger.error(f"API Error fetching balance: Status {response.status}")
        except Exception as e:
            logger.error(f"Failed to fetch wallet balance: {e}")

        return lit_bal, usdc_bal