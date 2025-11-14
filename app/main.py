# app/main.py
import logging
import asyncio  # Добавлен импорт asyncio
from fastapi import FastAPI, Request, Response
from telegram import Update
import uvicorn

from app.bot import application
from app.core.config import settings

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создание экземпляра FastAPI
app = FastAPI(docs_url=None, redoc_url=None)


# --- НАЧАЛО ДИАГНОСТИЧЕСКОГО КОДА ---
async def stay_alive():
    """
    Фоновая задача-"пульс". Она просто бесконечно работает,
    каждую минуту отправляя сообщение в лог. Это не дает основному
    процессу завершиться и помогает диагностировать "тихие" падения.
    """
    while True:
        logger.info("Heartbeat: Service is still alive and running...")
        await asyncio.sleep(60)
# --- КОНЕЦ ДИАГНОСТИЧЕСКОГО КОДА ---


@app.get("/")
async def health_check():
    """Эндпоинт для Health Check от Render."""
    return Response(status_code=200)


@app.on_event("startup")
async def on_startup():
    """Выполняется при старте FastAPI."""
    # Инициализируем приложение PTB
    await application.initialize()
    
    # Устанавливаем вебхук
    webhook_url = f"{settings.WEBHOOK_URL}/{settings.TELEGRAM_TOKEN}"
    logger.info(f"Setting webhook to: {webhook_url}")
    await application.bot.set_webhook(url=webhook_url)

    # --- НАЧАЛО ДИАГНОСТИЧЕСКОГО КОДА ---
    # Запускаем нашу фоновую задачу "пульса"
    asyncio.create_task(stay_alive())
    # --- КОНЕЦ ДИАГНОСТИЧЕСКОГО КОДА ---


@app.post("/{token}")
async def process_update(token: str, request: Request):
    """Главный эндпоинт для приема обновлений от Telegram."""
    if token != settings.TELEGRAM_TOKEN:
        logger.warning("Invalid token received.")
        return Response(status_code=403)
        
    try:
        update_data = await request.json()
        update = Update.de_json(data=update_data, bot=application.bot)
        
        chat_id = update.effective_chat.id if update.effective_chat else "N/A"
        logger.info(f"Processing update {update.update_id} from chat {chat_id}")
        
        await application.process_update(update)

    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)

    return Response(status_code=200)


@app.on_event("shutdown")
async def on_shutdown():
    """Выполняется при остановке FastAPI."""
    logger.info("Application is shutting down. Deleting webhook...")
    await application.bot.delete_webhook()
    await application.shutdown()


# Блок для локального запуска
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

