import json
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.globals import AVAILABLE_COINS, PRICE_FETCHERS
from app.core.redis_db import redis_client
from app.models.alert import Alert
from sqlalchemy import desc, update, delete, select
from aiogram import Bot
from app.models.user import User

# 1. Search where the asset is traded
async def find_exchanges_for_symbol(symbol: str) -> list[dict]:
    exchanges = []
    for exchange_name, coins in AVAILABLE_COINS.items():
        if symbol in coins:
            # Formatting the name for UI (e.g., "binance_futures" -> "Binance Futures")
            display_name = exchange_name.replace("_", " ").title()
            exchanges.append({
                "name": display_name, 
                "data": exchange_name, 
            })
    return exchanges

# 2. Get current price from exchanges
async def get_current_price(symbol: str, exchange: str) -> float:
    fetch_func = PRICE_FETCHERS.get(exchange)
    if not fetch_func:
        raise ValueError(f"Unknown exchange: {exchange}")
    return await fetch_func(symbol)
 
# 3. Save alert to PostgreSQL
async def post_alert_to_database(user_id: int,
                                 symbol: str,
                                 exchange: str,
                                 direction: str,
                                 target_price: float,
                                 session: AsyncSession) -> Alert:
    # Check if user exists
    user_exists = await session.execute(
        select(User).where(User.id == user_id)
    )
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
        target_price=target_price
    )
    session.add(new_alert)
    await session.commit()
    await session.refresh(new_alert)

    return new_alert

# 4. Push alert to Redis for fast worker access
async def put_alert_in_redis(user_id: int,
                             telegram_id: int, 
                             symbol: str, 
                             exchange: str, 
                             target_price: float,
                             direction: str,
                             alert_id: int):
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



# ALERT TRIGERED - DISABLE IN DB

async def disable_alert_in_db(alert_id: int, session: AsyncSession):
    result = await session.execute(
        update(Alert)
        .where(Alert.id == alert_id)
        .values(is_active=False)
    )
    await session.commit()
    logger.info(f"Alert {alert_id} disabled in database.")



# --- VIEW ACTIVE ALERTS ---
async def get_all_active_alerts(telegram_id: int, session: AsyncSession):
    """Get all active alerts for a user. Returns empty list if user doesn't exist."""
    user = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user.scalar_one_or_none()

    if not user:
        logger.warning(f"User with telegram_id {telegram_id} does not exist")
        return None

    result = await session.execute(
        select(Alert)
        .where(
            Alert.user_id == user.id,
            Alert.is_active == True
        )
        # Сортировка от НОВЫХ к СТАРЫМ (самые свежие будут первыми в списке)
        .order_by(desc(Alert.created_at))
    )

    return result.scalars().all()


# --- GET SINGLE ALERT BY ID ---
async def get_alert_by_id(alert_id: int, session: AsyncSession) -> Alert | None:
    result = await session.execute(
        select(Alert).where(Alert.id == alert_id)
    )
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
        # Get all alerts from this key
        all_alerts = await redis_client.lrange(redis_key, 0, -1)
        for alert_json in all_alerts:
            alert_data = json.loads(alert_json)
            if alert_data.get("alert_id") == alert_id:
                await redis_client.lrem(redis_key, 1, alert_json)
                logger.info(f"Removed alert {alert_id} from Redis key {redis_key}")
                break
    except Exception as e:
        logger.error(f"Error removing alert {alert_id} from Redis: {e}")

    # Delete from database (or mark as inactive)
    await session.execute(
        delete(Alert).where(Alert.id == alert_id)
    )
    await session.commit()
    logger.info(f"Alert {alert_id} deleted from database.")


# send message to user when alert is triggered
async def send_alert_message(bot: Bot,
                              telegram_id: int,
                              current_price: float,
                              symbol: str,
                              exchange: str,
                              target_price: float):
    try:
        exchange_display = exchange.replace("_", " ").title()

        # Determine direction based on prices
        direction = "ABOVE" if current_price >= target_price else "BELOW"
        direction_emoji = "📈" if direction == "ABOVE" else "📉"

        # Calculate percentage difference
        percent_diff = abs(((current_price - target_price) / target_price) * 100)

        # Format prices
        def format_price(price: float) -> str:
            if price >= 1:
                return f"{price:,.2f}"
            elif price >= 0.01:
                return f"{price:.4f}"
            else:
                return f"{price:.8f}"

        message = (
            f"🚨 <b>ALERT!</b>\n\n"
            f"<b>{symbol}</b> • {exchange_display}\n"
            f"Target: <code>${format_price(target_price)}</code>\n"
            f"Current: <code>${format_price(current_price)}</code>\n"
            f"{direction_emoji} {direction.lower()} | {percent_diff:.2f}%\n\n"
            f"✅ Target reached!"
        )

        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode="HTML"
        )

        logger.success(f"Alert sent to {telegram_id} for {symbol} at {current_price}")
    except Exception as e:
        logger.error(f"Failed to send alert to {telegram_id}: {e}")

