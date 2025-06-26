from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, BigInteger, Enum
from enum import Enum as PyEnum
from datetime import datetime
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Получаем URL базы данных
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Ошибка: DATABASE_URL не найден. Проверьте .env файл!")

# Создаем асинхронный движок SQLAlchemy
try:
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
except Exception as e:
    raise RuntimeError(f"Ошибка при создании движка базы данных: {e}")

# Определяем базовый класс моделей
Base = declarative_base()

# Функция инициализации базы данных
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Функция для сброса базы данных
async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, cascade=True)
        await conn.run_sync(Base.metadata.create_all)