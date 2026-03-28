from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from sqlalchemy import select , delete, update
from sqlalchemy.future import select
from app.core.redis_db import redis_client
from aiogram.types import Message


async def register_user(telegram_id: int, session: AsyncSession,telegram_username: str = None):
    # 1 check if user already exists
    existing_user = await session.execute(select(User).filter(User.telegram_id == telegram_id))
    existing_user = existing_user.scalars().first()
    if existing_user:
        return f"Hello! {existing_user.telegram_username}"
    # 2 if not, create new user
    new_user = User(telegram_id=telegram_id, telegram_username=telegram_username)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return f"Welcome, {new_user.telegram_username}! You have been registered."


