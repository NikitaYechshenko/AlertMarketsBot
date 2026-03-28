from typing import Callable, Awaitable, Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # 1. Открываем сессию ДО того, как сообщение попадет в хэндлер
        async with self.session_pool() as session:
            
            # 2. САМАЯ ГЛАВНАЯ СТРОЧКА: кладем сессию в словарь data
            # Всё, что лежит в data, aiogram попытается передать в аргументы хэндлера
            data["session"] = session
            
            # 3. Передаем управление дальше (в ваш хэндлер)
            # Хэндлер отработает, и код пойдет дальше
            result = await handler(event, data)
            
        # 4. Блок async with закончился, сессия безопасно закрылась сама!
        return result