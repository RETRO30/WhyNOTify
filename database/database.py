import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from utils.config import Config

Base = declarative_base()
engine = create_async_engine(
    f"postgresql+asyncpg://{Config.database.username}:{Config.database.password}@{Config.database.hostname}@{Config.database.port}/{Config.database.database}"
)

# Создаем сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()