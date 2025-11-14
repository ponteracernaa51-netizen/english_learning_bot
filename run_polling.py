# run_polling.py (ФИНАЛЬНАЯ ВЕРСИЯ)
import logging
import asyncio
import platform # Импортируем platform, чтобы проверить ОС

# --- НАЧАЛО ИСПРАВЛЕНИЯ ---
# Проверяем, что мы на Windows, и применяем нужную политику
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# --- КОНЕЦ ИСПРАВЛЕНИЯ ---

from app.bot import application

# Настраиваем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting bot in polling mode...")
    application.run_polling()