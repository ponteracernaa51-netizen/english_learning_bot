# app/main.py

import logging
import asyncio
from fastapi import FastAPI, Request, Response
from telegram import Update
import uvicorn

from app.bot import application
from app.core.config import settings
from app.database import engine  # ### ДОБАВЛЕНО: Импортируем engine
from app.models import Base  # ### ДОБАВЛЕНО: Импортируем Base со всеми моделями

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None)

### ДОБАВЛЕНО: Функция для создания таблиц ###
def create_tables():
    logger.info("Creating database tables if they don't exist...")
    try:
        # create_all не является асинхронной, поэтому используем sync_engine
        Base.metadata.create_all(bind=engine.sync_engine)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}", exc_info=True)

@app.get("/")
async def health_check():
    return Response(status_code=200)

@app.on_event("startup")
async def on_startup():
    # ### ДОБАВЛЕНО: Вызываем создание таблиц перед инициализацией бота ###
    create_tables() 
    await application.initialize()
    logger.info("Application initialized.")

@app.post("/{token}")
async def process_update(token: str, request: Request):
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
    logger.info("Application is shutting down.")
    await application.shutdown()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
