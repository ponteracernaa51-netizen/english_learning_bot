# app/main.py
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update
import uvicorn

from app.bot import application
from app.core.config import settings

# Настраиваем логирование, чтобы видеть ошибки на сервере Render
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None)

@app.on_event("startup")
async def on_startup():
    """Устанавливает вебхук при старте приложения."""
    webhook_url = f"{settings.WEBHOOK_URL}/{settings.TELEGRAM_TOKEN}"
    logger.info(f"Setting webhook to: {webhook_url}")
    await application.bot.set_webhook(url=webhook_url)

@app.post("/{token}")
async def process_update(token: str, request: Request):
    """Принимает обновления от Telegram и передает их обработчику."""
    if token != settings.TELEGRAM_TOKEN:
        logger.warning("Invalid token received.")
        return Response(status_code=403)
        
    try:
        update_data = await request.json()
        update = Update.de_json(data=update_data, bot=application.bot)
        logger.info(f"Processing update {update.update_id} from chat {update.effective_chat.id if update.effective_chat else 'N/A'}")
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)

    return Response(status_code=200)

@app.on_event("shutdown")
async def on_shutdown():
    """Удаляет вебхук при остановке приложения."""
    logger.info("Deleting webhook...")
    await application.bot.delete_webhook()