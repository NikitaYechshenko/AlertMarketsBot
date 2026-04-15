from loguru import logger
from app.bot.middlewares.db import DbSessionMiddleware
from app.core.database import async_session_maker, init_db
from aiogram import Bot, Dispatcher
import asyncio
from app.core.config import settings
from app.core.redis_db import init_redis
# Import exchange checkers
from app.exchanges.Binance.binance_spot import start_binance_spot_checkers
from app.exchanges.Binance.binance_f import start_binance_f_checkers
# from app.exchanges.Binance.binance_f import start_binance_spot_checkers
# Import workers
from app.workers.Binance.spot import binance_spot_worker
from app.workers.Binance.futures import binance_futures_worker

# Import Routers
from app.bot.handlers.alert import alert
# Note: user.py router is not included; user registration is handled in alert router
# Import alert services
from app.bot.services.alert_serv import load_all_alerts_to_redis


bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


def _log_worker_task_failure(task: asyncio.Task) -> None:
    try:
        task.result()
    except Exception as e:
        logger.error(f"Worker task failed: {e}")


async def on_startup():
    logger.info("Bot is starting up...")
    logger.info("Initializing redis...")
    await init_redis()
    logger.info("Loading active alerts from database to Redis...")
    await load_all_alerts_to_redis(async_session_maker)

    # logger.info("Fetching available coins from exchanges...")
    # AVAILABLE_COINS["binance_futures"] = set(await check_binance_f())
    # AVAILABLE_COINS["binance_spot"] = set(await check_binance_spot())
    # Start workers for each exchange
    # await check_binance_f()

    start_binance_spot_checkers(prices_interval_seconds=10, symbols_interval_seconds=3600)
    spot_task = asyncio.create_task(binance_spot_worker(bot))
    spot_task.add_done_callback(_log_worker_task_failure)

    start_binance_f_checkers(prices_interval_seconds=10, symbols_interval_seconds=3600)
    futures_task = asyncio.create_task(binance_futures_worker(bot))
    futures_task.add_done_callback(_log_worker_task_failure)
    logger.info("Bot startup complete!")


async def main():
    await init_db()
    dp.startup.register(on_startup)

    # Register middleware for messages
    dp.message.middleware(DbSessionMiddleware(session_pool=async_session_maker))
    # Register middleware for callback queries (inline buttons)
    dp.callback_query.middleware(DbSessionMiddleware(session_pool=async_session_maker))

    # Include routers
    dp.include_router(alert)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Starting bot")
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Bot stopped!")
