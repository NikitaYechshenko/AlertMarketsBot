import aiohttp
from typing import List, Optional
from loguru import logger
import asyncio

from app.core.http_client import get_http_session, _retry_with_backoff


async def get_binance_all_f_symbols(session: aiohttp.ClientSession) -> List[str]:
    """
    Get current list of all traded pairs (PERPETUAL FUTURES) on Binance.
    Returns list of strings: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', ...]
    """
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"

    result = await _retry_with_backoff(session, url, max_retries=3)
    if result is None:
        logger.error("Failed to fetch futures symbols after retries")
        return []
    
    if result["status"] == 200:
        data = result["data"]

        binance_f_active_symbols = []
        for item in data["symbols"]:
            # Added contractType == "PERPETUAL" condition
            if item["status"] == "TRADING" and item["contractType"] == "PERPETUAL":
                binance_f_active_symbols.append(item["symbol"])

        return binance_f_active_symbols

    logger.error(f"Error fetching futures symbols: {result['status']}")
    return []


async def get_binance_current_f_price(
    session: aiohttp.ClientSession, symbol: str
) -> Optional[float]:
    """
    Make one fast request to Binance API to get current futures price.
    """
    symbol = symbol.upper()
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"

    result = await _retry_with_backoff(session, url, max_retries=2)
    if result is None:
        return None
    
    if result["status"] == 200:
        data = result["data"]
        return float(data["price"])
    return None


# API CHECKERS -------------------------------------------------------------------------


async def _loop_binance_f_update_symbols(interval_seconds: int):
    from app.core.globals import AVAILABLE_COINS

    while True:
        try:
            session = get_http_session()
            symbols = await get_binance_all_f_symbols(session)
            if symbols:
                logger.success(
                    f"⛳ BINANCE FUTURES | Futures symbols loaded: {len(symbols)} pairs ⛳"
                )
                AVAILABLE_COINS["binance_futures"].clear()
                AVAILABLE_COINS["binance_futures"].update(symbols)
            else:
                logger.error("BINANCE FUTURES | Failed to fetch futures symbols.")
        except Exception as e:
            logger.error(f"BINANCE FUTURES | Exception while fetching symbols: {e}")

        # Засыпаем до следующей проверки
        await asyncio.sleep(interval_seconds)


async def _loop_binance_f_check_prices(interval_seconds: int):
    """Фоновая задача: проверяет доступность цен каждые N секунд."""
    while True:
        try:
            session = get_http_session()
            price = await get_binance_current_f_price(session, "BTCUSDT")
            if price is not None:
                pass
                #logger.success(f"💲BINANCE FUTURES | Current price of BTCUSDT on Futures: {price} 💲")
            else:
                logger.error("BINANCE FUTURES | Failed to fetch futures price.")
        except Exception as e:
            logger.error(f"BINANCE FUTURES | Exception while fetching price: {e}")

        await asyncio.sleep(interval_seconds)


def start_binance_f_checkers(
    symbols_interval_seconds: float = 10.0,
    prices_interval_seconds: float = 10.0,
):
    """
    check 1)binance futures symbols list every N hours, 2)binance futures price fetch every N seconds
    """
    logger.info("BINANCE FUTURES | Starting background market checkers")
    # Сохраняем ссылки на таски, чтобы сборщик мусора их не убил (важно для новых версий Python)
    global background_tasks
    background_tasks = set()

    task1 = asyncio.create_task(
        _loop_binance_f_update_symbols(symbols_interval_seconds)
    )
    task2 = asyncio.create_task(_loop_binance_f_check_prices(prices_interval_seconds))

    background_tasks.add(task1)
    background_tasks.add(task2)

    # Очищаем сет от завершенных тасок (на всякий случай)
    task1.add_done_callback(background_tasks.discard)
    task2.add_done_callback(background_tasks.discard)
