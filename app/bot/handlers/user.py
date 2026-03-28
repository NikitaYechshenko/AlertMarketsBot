from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters.command import Command
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.services.user_serv import register_user

user = Router()

@user.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    result = await register_user(telegram_id=message.from_user.id, session=session, telegram_username=message.from_user.username)
    await message.answer(result)