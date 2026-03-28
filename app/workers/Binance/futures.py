
from app.core.redis_db import redis_client
from app.bot.services.alert_serv import send_alert_message, disable_alert_in_db
from app.core.database import async_session_maker
import loguru
import json
import asyncio
from aiogram import Bot
import aiohttp

async def check_alerts_for_symbol(symbol: str, current_price: float, bot: Bot):
    """
    Проверяет, есть ли сработавшие алерты для конкретной монеты.
    """
    exchange = "binance_futures"
    redis_key = f"alerts:{exchange}:{symbol}"
    
    # Получаем все алерты по этой монете из списка в Redis
    # lrange вернет пустой список [], если алертов на эту монету нет
    alerts = await redis_client.lrange(redis_key, 0, -1)
    
    if not alerts:
        return # Если алертов нет, сразу выходим (экономим ресурсы)

    for alert_str in alerts:
        # alert_str приходит в виде байт-строки или строки (зависит от настроек Redis)
        alert_data = json.loads(alert_str)
        
        target_price = alert_data["target_price"]
        direction = alert_data["direction"]
        telegram_id = alert_data["telegram_id"]
        alert_id = alert_data["alert_id"]
        
        triggered = False
        
        # Логика срабатывания
        if direction == "ABOVE" and current_price >= target_price:
            triggered = True
        elif direction == "BELOW" and current_price <= target_price:
            triggered = True
            
        if triggered:

            # 1. Отправляем сообщение пользователю
            await send_alert_message(bot, telegram_id, current_price, symbol, exchange, target_price)

            # 2. Удаляем именно ЭТОТ сработавший алерт из списка Redis
            # lrem(key, count, value) - удаляет 1 вхождение строки alert_str
            await redis_client.lrem(redis_key, 1, alert_str)
            
            # 3. (Опционально) Меняем статус алерта в PostgreSQL на is_active=False
            try:
                async with async_session_maker() as session:
                    await disable_alert_in_db(alert_id, session)
            except Exception as e:
                loguru.logger.error(f"Failed to disable alert in database: {e}")


async def binance_futures_worker(bot: Bot):
    """
    Фоновый процесс, который держит WebSocket соединение с Binance Futures.
    """
    # Эндпоинт стрима всех тикеров (All Market Tickers Stream)
    url = "wss://fstream.binance.com/ws/!ticker@arr"
    
    while True: # Бесконечный цикл для авто-переподключения при ошибках
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    loguru.logger.info("🟢 Успешно подключились к WebSocket Binance Futures!")
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            
                            # Binance присылает список словарей. 
                            # 's' - symbol (BTCUSDT), 'c' - current close price
                            for item in data:
                                symbol = item['s']
                                current_price = float(item['c'])
                                
                                # Запускаем проверку (без await перед asyncio.create_task, 
                                # чтобы проверка шла параллельно и не тормозила чтение вебсокета)
                                asyncio.create_task(
                                    check_alerts_for_symbol(symbol, current_price, bot)
                                )
                                
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            loguru.logger.warning("🔴 WebSocket FUTURES закрыт биржей.")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            loguru.logger.error("🔴 Ошибка WebSocket FUTURES.")
                            break
                            
        except Exception as e:
            loguru.logger.error(f"⚠️ Ошибка соединения в Binance FUTURES Worker: {e}. Переподключение через 5 секунд...")
            await asyncio.sleep(5) # Пауза перед попыткой переподключиться


