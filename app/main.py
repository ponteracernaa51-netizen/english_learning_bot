# app/main.py (ФИНАЛЬНАЯ ВЕРСЯ БЕЗ УПРАВЛЕНИЯ ВЕБХУКОМ)
import logging
import asyncio
from fastapi import FastAPI, Request, Response
from telegram import Update
import uvicorn

from app.bot import application
from app.core.config import settings

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None)

@app.get("/")
async def health_check():
    return Response(status_code=200)

@app.on_event("startup")
async def on_startup():
    """Выполняется при старте FastAPI."""
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
    """Выполняется при остановке FastAPI."""
    logger.info("Application is shutting down.")
    await application.shutdown()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
