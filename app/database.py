# app/database.py (УЛУЧШЕННАЯ ВЕРСИЯ)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event
from app.core.config import settings

# Создаем асинхронный "движок"
# pool_size=5, max_overflow=10 - стандартные настройки для небольшого веб-приложения
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False, # Отключаем логирование SQL в продакшене, чтобы не засорять логи
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True # Проверяет соединение перед использованием
)

# Добавляем обработчики для управления соединениями (важно для серверных сред)
@event.listens_for(engine.sync_engine, "connect")
def connect(dbapi_connection, connection_record):
    """Выполняется при установке нового соединения."""
    # Здесь можно установить тайм-ауты или другие параметры
    pass

@event.listens_for(engine.sync_engine, "close")
def close(dbapi_connection, connection_record):
    """Выполняется при закрытии соединения."""
    pass

# Создаем фабрику сессий
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Зависимость для FastAPI (не используется в боте напрямую, но полезна)
async def get_db_session():
    async with async_session_factory() as session:
        yield session
