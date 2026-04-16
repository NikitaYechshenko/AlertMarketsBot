import json
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.globals import AVAILABLE_COINS, URLS
from app.core.redis_db import redis_client
from app.core.http_client import get_http_session
from app.models.alert import Alert
from sqlalchemy import desc, update, delete, select
from aiogram import Bot
from app.models.user import User
from app.exchanges.Binance.binance_spot import get_binance_current_spot_price
from app.exchanges.Binance.binance_f import get_binance_current_f_price
from aiogram.types import LinkPreviewOptions

PRICE_FETCHERS = {
    "binance_spot": get_binance_current_spot_price,
    "binance_futures": get_binance_current_f_price,
}


# 1. Search where the asset is traded
async def find_exchanges_for_symbol(symbol: str) -> list[dict]:
    exchanges = []
    for exchange_name, coins in AVAILABLE_COINS.items():
        if symbol in coins:
            # Formatting the name for UI (e.g., "binance_futures" -> "Binance Futures")
            display_name = exchange_name.replace("_", " ").title()
            exchanges.append(
                {
                    "name": display_name,
                    "data": exchange_name,
                }
            )
    return exchanges


# 2. Get current price from exchanges
async def get_current_price(symbol: str, exchange: str) -> float:
    fetch_func = PRICE_FETCHERS.get(exchange)
    if not fetch_func:
        raise ValueError(f"Unknown exchange: {exchange}")
    return await fetch_func(get_http_session(), symbol)


# 3. Save alert to PostgreSQL
async def post_alert_to_database(
    user_id: int,
    symbol: str,
    exchange: str,
    direction: str,
    target_price: float,
    session: AsyncSession,
) -> Alert:
    # Check if user exists
    user_exists = await session.execute(select(User).where(User.id == user_id))
    if not user_exists.scalar_one_or_none():
        raise ValueError(f"User with id {user_id} does not exist")

    direction = direction.upper()
    if direction not in ["ABOVE", "BELOW"]:
        raise ValueError("Direction must be either 'ABOVE' or 'BELOW'")

    new_alert = Alert(
        user_id=user_id,
        symbol=symbol,
        exchange=exchange,
        direction=direction,
        target_price=target_price,
    )
    session.add(new_alert)
    await session.commit()
    await session.refresh(new_alert)

    return new_alert


# 4. Push alert to Redis for fast worker access
async def put_alert_in_redis(
    user_id: int,
    telegram_id: int,
    symbol: str,
    exchange: str,
    target_price: float,
    direction: str,
    alert_id: int,
):
    alert_data = {
        "alert_id": alert_id,
        "user_id": user_id,
        "telegram_id": telegram_id,
        "symbol": symbol,
        "exchange": exchange,
        # Cast to float in case SQLAlchemy returns a Decimal object
        "target_price": float(target_price),
        "direction": direction,
    }

    redis_key = f"alerts:{exchange}:{symbol}"
    json_data = json.dumps(alert_data)
    await redis_client.rpush(redis_key, json_data)


# 5. LOAD ALL ALERTS FROM DB TO REDIS ON STARTUP
async def load_all_alerts_to_redis(session_maker):
    """Load all active alerts from database into Redis on bot startup."""
    try:
        async with session_maker() as session:
            # Get all active alerts from database
            result = await session.execute(select(Alert).where(Alert.is_active == True))
            alerts = result.scalars().all()

            loaded_count = 0
            for alert in alerts:
                # Get the associated user to retrieve telegram_id
                user_result = await session.execute(
                    select(User).where(User.id == alert.user_id)
                )
                user = user_result.scalar_one_or_none()

                if not user:
                    logger.warning(
                        f"Alert {alert.id} has no associated user (user_id: {alert.user_id}). Skipping."
                    )
                    continue

                try:
                    await put_alert_in_redis(
                        user_id=user.id,
                        telegram_id=user.telegram_id,
                        symbol=alert.symbol,
                        exchange=alert.exchange,
                        target_price=alert.target_price,
                        direction=alert.direction,
                        alert_id=alert.id,
                    )
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"Failed to load alert {alert.id} to Redis: {e}")
                    continue

            logger.success(
                f"REDIS | Loaded {loaded_count} active alerts from database to REDIS"
            )
    except Exception as e:
        logger.error(f"Error loading alerts from database to Redis: {e}")


# ALERT TRIGERED - DISABLE IN DB


async def disable_alert_in_db(alert_id: int, session: AsyncSession) -> bool:
    result = await session.execute(
        update(Alert)
        .where(Alert.id == alert_id, Alert.is_active == True)
        .values(is_active=False)
    )
    await session.commit()
    updated_rows = result.rowcount or 0
    if updated_rows:
        logger.info(f"Alert {alert_id} disabled in database.")
        return True

    logger.warning(f"Alert {alert_id} is already inactive or missing.")
    return False


# --- VIEW ACTIVE ALERTS ---
async def get_all_active_alerts(telegram_id: int, session: AsyncSession):
    """Get all active alerts for a user. Returns empty list if user doesn't exist."""
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()

    if not user:
        logger.warning(f"User with telegram_id {telegram_id} does not exist")
        return None

    result = await session.execute(
        select(Alert).where(Alert.user_id == user.id, Alert.is_active == True)
        # Sorting from NEW to OLD (most recent will be first in list)
        .order_by(desc(Alert.created_at))
    )

    return result.scalars().all()


# --- GET SINGLE ALERT BY ID ---
async def get_alert_by_id(alert_id: int, session: AsyncSession) -> Alert | None:
    result = await session.execute(select(Alert).where(Alert.id == alert_id))
    return result.scalar_one_or_none()


# --- DELETE ALERT (mark as inactive + remove from Redis) ---
async def delete_alert(alert_id: int, session: AsyncSession):
    """Delete alert from database and remove from Redis."""
    # First get the alert to know its exchange and symbol for Redis key
    alert_obj = await get_alert_by_id(alert_id, session)

    if not alert_obj:
        logger.warning(f"Attempted to delete non-existent alert {alert_id}")
        return

    # Remove from Redis
    redis_key = f"alerts:{alert_obj.exchange}:{alert_obj.symbol}"
    try:
        # Get all alerts from this key and find the one to delete
        all_alerts = await redis_client.lrange(redis_key, 0, -1)
        for alert_json in all_alerts:
            alert_data = json.loads(alert_json)
            if alert_data.get("alert_id") == alert_id:
                await redis_client.lrem(redis_key, 1, alert_json)
                logger.info(f"Removed alert {alert_id} from Redis key {redis_key}")
                break
    except Exception as e:
        logger.error(f"Error removing alert {alert_id} from Redis: {e}")

    # Delete from database (physically remove the record)
    await session.execute(delete(Alert).where(Alert.id == alert_id))
    await session.commit()
    logger.info(f"Alert {alert_id} deleted from database.")


# send message to user when alert is triggered
async def send_alert_message(
    bot: Bot,
    telegram_id: int,
    current_price: float,
    symbol: str,
    exchange: str,
    target_price: float,
):
    try:
        
        exchange_display = exchange.replace("_", " ").title()

        # Calculate percentage difference
        if target_price != 0:
            percent_diff = abs(((current_price - target_price) / target_price) * 100)
        else:
            percent_diff = 0  # Skip percent calculation if target is 0

        # Format prices
        def format_price(price: float) -> str:
            if price >= 1:
                return f"{price:,.2f}"
            elif price >= 0.01:
                return f"{price:.4f}"
            else:
                return f"{price:.8f}"
            
        #"binance_spot": "https://api.binance.com/api/v3/ticker/price?symbol={symbol}",
        url = URLS.get(exchange)
        url = url.format(symbol=symbol)

        message = (
            f"🚨 <b>ALERT!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>{symbol}</b> • {exchange_display}\n\n"
            f"🎯 Target: <code>${format_price(target_price)}</code>\n"
            f"{'📈' if current_price >= target_price else '📉'} Current: <code>${format_price(current_price)}</code>\n\n"
            f"🔗 <a href='{url}'>View on {exchange_display}</a>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>Target reached!</b>"
        )

        await bot.send_message(chat_id=telegram_id,
                                text=message,
                                parse_mode="HTML", 
                               disable_web_page_preview=True,
                               link_preview_options=LinkPreviewOptions(is_disabled=True))

        logger.success(f"Alert sent to {telegram_id} for {symbol} at {current_price}")
    except Exception as e:
        logger.error(f"Failed to send alert to {telegram_id}: {e}")
