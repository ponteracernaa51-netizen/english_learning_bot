# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Создаем асинхронный "движок" для подключения к БД
# echo=True полезно для отладки, т.к. выводит все SQL-запросы в консоль
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Создаем фабрику сессий, которая будет создавать новые сессии для каждого запроса
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Зависимость для получения сессии БД (полезно для FastAPI в будущем)
async def get_db_session():
    async with async_session_factory() as session:
        yield session