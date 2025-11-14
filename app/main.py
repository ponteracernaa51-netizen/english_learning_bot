# app/main.py
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update
import uvicorn

from app.bot import application
from app.core.config import settings

# Настраиваем логирование, чтобы видеть подробные ошибки на сервере Render
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем экземпляр FastAPI, отключаем ненужную документацию
app = FastAPI(docs_url=None, redoc_url=None)


@app.get("/")
async def health_check():
    """
    Этот эндпоинт нужен для Render'а, чтобы он мог проверить,
    что сервис жив и здоров ('Health Check'). Render периодически
    отправляет GET-запрос на корневой URL. Если он получает
    успешный ответ (статус 200), он считает сервис рабочим.
    Без этого Render может решить, что сервис "упал", и перезапустить его.
    """
    return Response(status_code=200)


@app.on_event("startup")
async def on_startup():
    """
    Эта функция выполняется один раз при старте приложения.
    Она формирует URL для вебхука и сообщает Telegram, куда
    отправлять все обновления для нашего бота.
    """
    webhook_url = f"{settings.WEBHOOK_URL}/{settings.TELEGRAM_TOKEN}"
    logger.info(f"Setting webhook to: {webhook_url}")
    await application.bot.set_webhook(url=webhook_url)


@app.post("/{token}")
async def process_update(token: str, request: Request):
    """
    Это главный эндпоинт, который принимает все обновления от Telegram.
    Telegram отправляет POST-запросы на URL /<токен_бота>.
    """
    # Простая проверка безопасности, чтобы убедиться, что запрос пришел от Telegram
    if token != settings.TELEGRAM_TOKEN:
        logger.warning("Invalid token received.")
        return Response(status_code=403) # 403 Forbidden
        
    try:
        # Получаем данные из запроса и преобразуем их в объект Update
        update_data = await request.json()
        update = Update.de_json(data=update_data, bot=application.bot)
        
        # Логируем ID обновления и чата для удобной отладки
        chat_id = update.effective_chat.id if update.effective_chat else "N/A"
        logger.info(f"Processing update {update.update_id} from chat {chat_id}")
        
        # Передаем обновление на обработку в python-telegram-bot
        await application.process_update(update)

    except Exception as e:
        # Логируем любые ошибки, которые могут произойти при обработке
        logger.error(f"Error processing update: {e}", exc_info=True)

    # Всегда возвращаем Telegram'у статус 200 OK, чтобы он знал,
    # что мы получили обновление, даже если при обработке была ошибка.
    # Иначе Telegram будет пытаться отправить это обновление снова и снова.
    return Response(status_code=200)


@app.on_event("shutdown")
async def on_shutdown():
    """
    Эта функция выполняется при остановке приложения.
    Она удаляет вебхук, чтобы Telegram перестал слать обновления
    на уже неработающий адрес.
    """
    logger.info("Deleting webhook...")
    await application.bot.delete_webhook()


# Этот блок нужен для возможности локального запуска этого файла,
# но при развертывании на Render он не используется.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
