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
    from app.models import (
        user,
        alert,
    )  # Import models so SQLAlchemy "sees" them and creates tables in DB

    # Important: Base.metadata.create_all will only work for tables
    # that were imported/created BEFORE calling this function.
    # Since classes are defined above, SQLAlchemy will "see" them.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database was initialized!")
