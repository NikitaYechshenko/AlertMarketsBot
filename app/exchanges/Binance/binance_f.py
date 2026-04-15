import aiohttp
from typing import List, Optional
from loguru import logger
import asyncio

from app.exchanges.Binance.binance_spot import _loop_binance_spot_check_prices, _loop_binance_spot_update_symbols, get_binance_current_spot_price

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


# API CHECKERS -------------------------------------------------------------------------

import asyncio

async def _loop_binance_f_update_symbols(interval_seconds: int):
    from app.core.globals import AVAILABLE_COINS

    while True:
        try:
            symbols = await get_binance_all_f_symbols()
            if symbols:
                logger.info(f"Binance | Futures symbols loaded: {len(symbols)} pairs ----------------------- ⛳")
                AVAILABLE_COINS["binance_futures"].clear()
                AVAILABLE_COINS["binance_futures"].update(symbols)
            else:
                logger.error("Binance | Failed to fetch futures symbols.")
        except Exception as e:
            logger.error(f"Binance | Exception while fetching symbols: {e}")
        
        # Засыпаем до следующей проверки
        await asyncio.sleep(interval_seconds)


async def _loop_binance_f_check_prices(interval_seconds: int):
    """Фоновая задача: проверяет доступность цен каждые N секунд."""
    while True:
        try:
            price = await get_binance_current_f_price("BTCUSDT")
            if price is not None:
                logger.info(f"Binance F | Current price of BTCUSDT on Futures: {price} 💲")
            else:
                logger.error("Binance F | Failed to fetch futures price.")
        except Exception as e:
            logger.error(f"Binance F | Exception while fetching price: {e}")
        
        await asyncio.sleep(interval_seconds)


def start_binance_f_checkers(
    symbols_interval_seconds: float = 10.0, 
    prices_interval_seconds: float = 10.0,
):
    """
    check 1)binance futures symbols list every N hours, 2)binance futures price fetch every N seconds
"""
    logger.info("Starting background market checkers...")
    # Сохраняем ссылки на таски, чтобы сборщик мусора их не убил (важно для новых версий Python)
    global background_tasks 
    background_tasks = set()

    task1 = asyncio.create_task(_loop_binance_f_update_symbols(symbols_interval_seconds))
    task2 = asyncio.create_task(_loop_binance_f_check_prices(prices_interval_seconds))
    
    background_tasks.add(task1)
    background_tasks.add(task2)

    # Очищаем сет от завершенных тасок (на всякий случай)
    task1.add_done_callback(background_tasks.discard)
    task2.add_done_callback(background_tasks.discard)
