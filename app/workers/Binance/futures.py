from app.core.redis_db import redis_client
from app.bot.services.alert_serv import send_alert_message, disable_alert_in_db
from app.core.database import async_session_maker
from loguru import logger
import json
import asyncio
from aiogram import Bot
import aiohttp
from app.core.config import settings


def _log_task_exception(task: asyncio.Task) -> None:
    try:
        task.result()
    except Exception as e:
        logger.error(f"Alert check task failed: {e}")


async def check_alerts_for_symbol(symbol: str, current_price: float, bot: Bot):
    """
    Check if there are any triggered alerts for a specific coin.
    """
    exchange = "binance_futures"
    redis_key = f"alerts:{exchange}:{symbol}"

    # Get all alerts for this coin from Redis list
    # lrange returns empty list [] if no alerts for this coin
    alerts = await redis_client.lrange(redis_key, 0, -1)

    if not alerts:
        return  # If no alerts, exit early (save resources)

    for alert_str in alerts:
        if isinstance(alert_str, bytes):
            try:
                alert_str = alert_str.decode("utf-8")
            except UnicodeDecodeError as e:
                logger.error(f"Invalid alert encoding for {symbol}: {e}")
                continue

        # alert_str comes as bytes or string (depends on Redis settings)
        try:
            alert_data = json.loads(alert_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid alert JSON for {symbol}: {e}")
            continue

        target_price = alert_data.get("target_price")
        direction = alert_data.get("direction")
        telegram_id = alert_data.get("telegram_id")
        alert_id = alert_data.get("alert_id")

        # Type conversion for target_price
        try:
            target_price = float(target_price) if target_price is not None else None
        except (TypeError, ValueError):
            logger.error(f"Invalid target_price for alert {alert_id}: {target_price}")
            # Remove malformed alert from Redis to prevent infinite loop
            await redis_client.lrem(redis_key, 1, alert_str)
            continue

        if (
            target_price is None
            or direction not in {"ABOVE", "BELOW"}
            or telegram_id is None
            or alert_id is None
        ):
            logger.error(f"Incomplete alert payload for {symbol}: {alert_data}")
            # Remove malformed alert from Redis to prevent infinite loop
            await redis_client.lrem(redis_key, 1, alert_str)
            continue

        triggered = False

        # Trigger logic
        if direction == "ABOVE" and current_price >= target_price:
            triggered = True
        elif direction == "BELOW" and current_price <= target_price:
            triggered = True

        if triggered:
            try:
                async with async_session_maker() as session:
                    was_disabled = await disable_alert_in_db(alert_id, session)

                # Always send message and cleanup Redis, regardless of DB state
                # This ensures we don't get stuck with stale Redis entries
                try:
                    await send_alert_message(
                        bot, telegram_id, current_price, symbol, exchange, target_price
                    )
                except Exception as e:
                    logger.error(f"Failed to send alert message: {e}")

                # Always cleanup Redis (even if DB update failed or message failed)
                await redis_client.lrem(redis_key, 1, alert_str)

                if not was_disabled:
                    logger.warning(
                        f"Alert {alert_id} was already inactive, but removed from Redis cache"
                    )
            except Exception as e:
                logger.error(f"Failed to process triggered alert {alert_id}: {e}")


async def binance_futures_worker(bot: Bot):
    """
    Background process that maintains WebSocket connection with Binance Futures.
    """
    # Endpoint for all tickers stream (All Market Tickers Stream)
    url = "wss://fstream.binance.com/ws/!miniTicker@arr"
    while True:  # Infinite loop for auto-reconnect on errors
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    logger.info("🟢 Successfully connected to Binance Futures WebSocket!")

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                            except json.JSONDecodeError as e:
                                logger.error(f"Invalid futures WS JSON: {e}")
                                continue
                            # Binance sends a list of dictionaries.
                            if not data:
                                logger.error("Received empty data from spot WS")
                                await bot.send_message(
                                    chat_id=settings.CHAT_ID,
                                    text="Received empty data from spot WS",
                                )
                                break

                            # Binance sends a list of dictionaries.
                            # 's' - symbol (BTCUSDT), 'c' - current close price
                            for item in data:
                                symbol = item.get("s")
                                raw_price = item.get("c")
                                if symbol is None or raw_price is None:
                                    continue
                                try:
                                    current_price = float(raw_price)
                                except (TypeError, ValueError):
                                    continue

                                # Start check without await for asyncio.create_task,
                                # so check runs in parallel and doesn't block websocket reading
                                task = asyncio.create_task(
                                    check_alerts_for_symbol(symbol, current_price, bot)
                                )
                                task.add_done_callback(_log_task_exception)

                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            logger.warning("🔴 WebSocket FUTURES closed by exchange.")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error("🔴 WebSocket FUTURES error.")
                            break

        except Exception as e:
            logger.error(
                f"⚠️ Connection error in Binance FUTURES Worker: {e}. Reconnecting in 5 seconds..."
            )
            await asyncio.sleep(5)  # Pause before reconnection attempt
