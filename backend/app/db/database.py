"""
Настройка подключения к базе данных.
SQLAlchemy 2.0 с async поддержкой.
"""
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Синхронный engine (для Alembic миграций)
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Асинхронный engine (для FastAPI)
# Заменяем postgresql:// на postgresql+asyncpg://
async_database_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

async_engine = create_async_engine(
    async_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Синхронная сессия для Alembic
SessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False,
)


# Базовый класс для моделей
class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy"""
    pass


# Dependency для получения сессии БД в endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения async сессии БД.
    Используется в FastAPI endpoints.

    Yields:
        AsyncSession: Сессия базы данных

    Example:
        ```python
        @router.get("/patients")
        async def get_patients(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Patient))
            return result.scalars().all()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
