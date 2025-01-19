import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from utils.config import Config

Base = declarative_base()
engine = create_async_engine(
    f"postgresql+asyncpg://{Config.database.username}:{Config.database.password}@{Config.database.hostname}:{Config.database.port}/{Config.database.database}"
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Функция для инициализации базы данных
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Контекстный менеджер для сессии
async def get_session():
    async with async_session() as session:
        yield session