from typing import AsyncGenerator
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
# 1. Create async engine
engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=False,
    future=True,
)

# 2. Create async session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass

async def init_db():
    from app.models import user, alert  # Импортируем модели, чтобы SQLAlchemy их "увидел" и создал таблицы в БД
    # Важно: Base.metadata.create_all сработает только для тех таблиц, 
    # которые были импортированы/созданы ДО вызова этой функции.
    # Так как классы написаны выше в этом же файле, SQLAlchemy их "увидит".
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database was initialized!")