import aiohttp
from typing import List, Optional
from loguru import logger


async def get_binance_all_f_symbols() -> List[str]:
    """
    Get current list of all traded pairs (PERPETUAL FUTURES) on Binance.
    Returns list of strings: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', ...]
    """
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                binance_f_active_symbols = []
                for item in data["symbols"]:
                    # Added contractType == "PERPETUAL" condition
                    if (
                        item["status"] == "TRADING"
                        and item["contractType"] == "PERPETUAL"
                    ):
                        binance_f_active_symbols.append(item["symbol"])

                return binance_f_active_symbols
            else:
                logger.error(f"Error fetching futures symbols: {response.status}")
                return []


async def get_binance_current_f_price(symbol: str) -> Optional[float]:
    """
    Make one fast request to Binance API to get current futures price.
    """
    symbol = symbol.upper()
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return float(data["price"])
            else:
                return None


async def check_binance_f():
    # check binance f all symbols
    symbols = await get_binance_all_f_symbols()
    if symbols:
        logger.info(f"Binance | Futures symbols loaded: {len(symbols)} pairs")
    else:
        logger.error("Binance | Failed to fetch futures symbols.")
        raise Exception("Binance | Failed to fetch futures symbols.")

    # check binance f current price
    price = await get_binance_current_f_price("BTCUSDT")
    if price is not None:
        logger.info(f"Binance | Current price of BTCUSDT on Futures: {price}")
    else:
        logger.error("Binance | Failed to fetch futures price.")
        raise Exception("Binance | Failed to fetch futures price.")

    return symbols
