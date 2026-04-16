import asyncio
from loguru import logger
# Импортируй свои функции (укажи правильные пути)
from app.core.http_client import init_http_session, close_http_session, get_http_session
# Импортируй ту функцию, которая делает сам запрос (внутри _loop_binance_f_check_prices)
# Допустим, она называется get_binance_current_f_price

async def quick_check():
    # 1. Заводим сессию
    await init_http_session()
    session = get_http_session()
    
    logger.info("Пробую отправить тестовый запрос к Binance...")
    
    try:
        # 2. Делаем одиночный запрос цены
        # Замени на свою реальную функцию запроса
        # Если ее нет под рукой, можно протестировать через прямой запрос:
        async def fetch_direct():
            url = "https://fapi.binance.com/fapi/v1/ticker/price?symbol=BTCUSDT"
            async with session.get(url) as resp:
                return resp.status, await resp.json()

        status, data = await fetch_direct()
        
        if status == 200:
            logger.success(f"Успех! Статус: {status}, Данные: {data}")
        else:
            logger.error(f"Binance ответил ошибкой: {status}, Тело: {data}")

    except Exception as e:
        logger.exception(f"Запрос не удался. Ошибка: {e}")
    
    finally:
        # 3. Закрываем сессию
        await close_http_session()

if __name__ == "__main__":
    asyncio.run(quick_check())