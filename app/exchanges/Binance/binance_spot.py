import asyncio
from aiogram import Bot
import aiohttp
from typing import List, Optional
from loguru import logger
import websockets


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


# API CHECKERS -------------------------------------------------------------------------

import asyncio

async def _loop_binance_spot_update_symbols(interval_seconds: int):
    from app.core.globals import AVAILABLE_COINS

    while True:
        try:
            symbols = await get_binance_all_spot_symbols()
            if symbols:
                logger.info(f"Binance | Spot symbols loaded: {len(symbols)} pairs ----------------------- ⛳")
                AVAILABLE_COINS["binance_spot"].clear()
                AVAILABLE_COINS["binance_spot"].update(symbols)
            else:
                logger.error("Binance | Failed to fetch spot symbols.")
        except Exception as e:
            logger.error(f"Binance | Exception while fetching symbols: {e}")
        
        # Засыпаем до следующей проверки
        await asyncio.sleep(interval_seconds)


async def _loop_binance_spot_check_prices(interval_seconds: int):
    """Фоновая задача: проверяет доступность цен каждые N секунд."""
    while True:
        try:
            price = await get_binance_current_spot_price("BTCUSDT")
            if price is not None:
                logger.info(f"Binance | Current price of BTCUSDT on Spot: {price} 💲")
            else:
                logger.error("Binance | Failed to fetch spot price.")
        except Exception as e:
            logger.error(f"Binance | Exception while fetching price: {e}")
        
        await asyncio.sleep(interval_seconds)


# async def _loop_binance_spot_check_worker(interval_seconds: int):
#     #check this ursl https://stream.binance.com/ws/!miniTicker@arr
#     url = "wss://stream.binance.com/ws/!miniTicker@arr"
    
#     while True:
#         try:
#             logger.info("Binance spot WS | Starting connection check... 🔍")
#             async with websockets.connect(url) as ws:
#                 # Ожидаем получения хотя бы одного сообщения с таймаутом 5 секунд
#                 # Это гарантирует, что биржа не просто приняла соединение, но и шлет данные
#                 message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                
#                 logger.info("Binance spot WS | Ping success! Stream is alive. 🧑‍🔧")
#                 # Если нужно посмотреть, что пришло, можно раскомментировать:
#                 # logger.debug(f"Received data: {message[:100]}...") 
                
#         except asyncio.TimeoutError:
#             logger.error("Binance spot WS | Ping failed: Connection established, but no data received (Timeout).")
#         except websockets.exceptions.WebSocketException as e:
#             logger.error(f"Binance spot WS | Ping failed: WebSocket error: {e}")
#         except Exception as e:
#             logger.error(f"Binance spot WS | Ping failed: Unexpected error: {e}")
        
#         # Спим до следующей проверки
#         await asyncio.sleep(interval_seconds)

def start_binance_spot_checkers(
    symbols_interval_seconds: float = 10.0, 
    prices_interval_seconds: float = 10.0,
):
    """
    check 1)binance spot symbols list every N hours, 2)binance spot price fetch every N seconds
"""
    logger.info("Starting background market checkers...")
    # Сохраняем ссылки на таски, чтобы сборщик мусора их не убил (важно для новых версий Python)
    global background_tasks 
    background_tasks = set()

    task1 = asyncio.create_task(_loop_binance_spot_update_symbols(symbols_interval_seconds))
    task2 = asyncio.create_task(_loop_binance_spot_check_prices(prices_interval_seconds))
    
    background_tasks.add(task1)
    background_tasks.add(task2)

    # Очищаем сет от завершенных тасок (на всякий случай)
    task1.add_done_callback(background_tasks.discard)
    task2.add_done_callback(background_tasks.discard)