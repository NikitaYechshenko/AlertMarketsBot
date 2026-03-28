import asyncio
import json
from aiogram import Bot
import aiohttp
from typing import List, Optional
from loguru import logger
import loguru

async def get_binance_all_spot_symbols() -> List[str]:
    """
    Получает актуальный список всех торгуемых пар к USDT на Споте Binance.
    Возвращает список строк: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', ...]
    """
    url = "https://api.binance.com/api/v3/exchangeInfo"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                binance_spot_active_symbols = []
                for item in data["symbols"]:
                    # Берем только торгуемые монеты в паре с USDT (отсеиваем мусор)
                    if item["status"] == "TRADING" :
                        binance_spot_active_symbols.append(item["symbol"])
                        
                return binance_spot_active_symbols
            else:
                logger.error(f"Binance API Error (Spot symbols): {response.status}")
                return []


async def get_binance_current_spot_price(symbol: str) -> Optional[float]:
    """
    Делает один запрос к Binance API для получения текущей цены на СПОТОВОМ рынке.
    Возвращает цену (float) или None, если монета не найдена.
    """
    symbol = symbol.upper()
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return float(data["price"])
            else:
                # Тикер не найден или ошибка API
                return None



async def check_binance_spot():
    """
    Функция для проверки работоспособности Спот-API при старте бота.
    """
    # 1. Проверка списка монет
    symbols = await get_binance_all_spot_symbols()
    if symbols:
        logger.info(f"Binance | Spot symbols loaded: {len(symbols)} pairs. E.g.: {symbols[:5]}")
    else:
        logger.error("Binance | Failed to fetch spot symbols.")
        raise Exception("Binance | Failed to fetch spot symbols.")
        
    # 2. Проверка получения цены
    price = await get_binance_current_spot_price("BTCUSDT")
    if price is not None:
        logger.info(f"Binance | Current price of BTCUSDT on Spot: {price}")
    else:
        logger.error("Binance | Failed to fetch spot price.")
        raise Exception("Binance | Failed to fetch spot price.")
    return symbols


# Блок для локального тестирования файла (не сработает при импорте в бота)
if __name__ == "__main__":
    asyncio.run(check_binance_spot())