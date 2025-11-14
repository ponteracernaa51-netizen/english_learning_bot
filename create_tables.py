# create_tables.py
import asyncio
from app.database import engine
from app.models import Base
import platform

# Патч для Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def create_db_tables():
    async with engine.begin() as conn:
        # Сначала удаляем все существующие таблицы (на всякий случай)
        await conn.run_sync(Base.metadata.drop_all)
        # Затем создаем их заново
        await conn.run_sync(Base.metadata.create_all)
    print("Tables dropped and created successfully.")

if __name__ == "__main__":
    asyncio.run(create_db_tables())