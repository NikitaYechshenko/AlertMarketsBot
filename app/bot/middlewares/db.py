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
        data: Dict[str, Any],
    ) -> Any:
        # 1. Open session BEFORE message reaches handler
        async with self.session_pool() as session:

            # 2. MAIN LINE: put session into data dict
            # Everything in data will be passed as handler arguments by aiogram
            data["session"] = session

            # 3. Pass control forward (to your handler)
            # Handler runs and code continues
            result = await handler(event, data)

        # 4. async with block ends, session closes safely!
        return result
