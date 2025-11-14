# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Загружаем переменные из .env файла
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TELEGRAM_TOKEN: str
    GEMINI_API_KEY: str
    DATABASE_URL: str
    WEBHOOK_URL: str

# Создаем единственный экземпляр настроек, который будем использовать во всем приложении
settings = Settings()