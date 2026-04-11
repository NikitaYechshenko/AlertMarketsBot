import asyncio
import json
from aiogram import Bot
import aiohttp
from typing import List, Optional
from loguru import logger
import loguru


async def get_binance_all_spot_symbols() -> List[str]:
    """
    Get current list of all traded pairs to USDT on Binance Spot.
    Returns list of strings: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', ...]
    """
    url = "https://api.binance.com/api/v3/exchangeInfo"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                binance_spot_active_symbols = []
                for item in data["symbols"]:
                    # Take only traded coins paired with USDT (filter out junk)
                    if item["status"] == "TRADING":
                        binance_spot_active_symbols.append(item["symbol"])

                return binance_spot_active_symbols
            else:
                logger.error(f"Binance API Error (Spot symbols): {response.status}")
                return []


async def get_binance_current_spot_price(symbol: str) -> Optional[float]:
    """
    Make one request to Binance API to get current price on SPOT market.
    Returns price (float) or None if coin not found.
    """
    symbol = symbol.upper()
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return float(data["price"])
            else:
                # Ticker not found or API error
                return None


async def check_binance_spot():
    """
    Function to check Spot API health on bot startup.
    """
    # 1. Check symbols list
    symbols = await get_binance_all_spot_symbols()
    if symbols:
        logger.info(
            f"Binance | Spot symbols loaded: {len(symbols)} pairs. E.g.: {symbols[:5]}"
        )
    else:
        logger.error("Binance | Failed to fetch spot symbols.")
        raise Exception("Binance | Failed to fetch spot symbols.")

    # 2. Check price fetching
    price = await get_binance_current_spot_price("BTCUSDT")
    if price is not None:
        logger.info(f"Binance | Current price of BTCUSDT on Spot: {price}")
    else:
        logger.error("Binance | Failed to fetch spot price.")
        raise Exception("Binance | Failed to fetch spot price.")
    return symbols


# Block for local file testing (won't work when imported into bot)
if __name__ == "__main__":
    asyncio.run(check_binance_spot())
