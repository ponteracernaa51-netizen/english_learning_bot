# app/bot.py
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, 
                          MessageHandler, filters)
from app.core.config import settings
from app.handlers import common, settings as s, training
from app.keyboards import button_texts # Импортируем тексты кнопок

# Создаем экземпляр Application
application = Application.builder().token(settings.TELEGRAM_TOKEN).build()

# Тексты кнопок для всех языков, чтобы фильтровать сообщения
all_button_texts = {text for lang in button_texts.values() for text in lang.values()}

# --- Регистрация обработчиков ---

# Общие команды
application.add_handler(CommandHandler("start", common.start))
application.add_handler(CallbackQueryHandler(common.set_language, pattern="^lang_"))

# Настройки (реагируем на текстовые сообщения из ReplyKeyboard)
application.add_handler(MessageHandler(filters.Text([
    button_texts['ru']['themes'], button_texts['en']['themes']
]), s.show_topics))
application.add_handler(MessageHandler(filters.Text([
    button_texts['ru']['level'], button_texts['en']['level']
]), s.show_levels))
application.add_handler(MessageHandler(filters.Text([
    button_texts['ru']['direction'], button_texts['en']['direction']
]), s.show_direction))
application.add_handler(MessageHandler(filters.Text([
    button_texts['ru']['profile'], button_texts['en']['profile']
]), common.show_profile))
application.add_handler(MessageHandler(filters.Text([
    button_texts['ru']['settings'], button_texts['en']['settings']
]), common.show_settings))

# Обработчики для Inline-кнопок настроек
application.add_handler(CallbackQueryHandler(s.set_topic, pattern="^topic_"))
application.add_handler(CallbackQueryHandler(s.set_level, pattern="^level_"))
application.add_handler(CallbackQueryHandler(s.set_direction, pattern="^dir_"))

# Тренировка
# ПРАВИЛЬНО (новая версия)
application.add_handler(MessageHandler(filters.Text([
    button_texts['ru']['start'], button_texts['en']['start']
]), training.start_training_command))
application.add_handler(CallbackQueryHandler(training.next_phrase_callback, pattern="^next_phrase$"))

# Обработчик для смены темы/уровня после тренировки
application.add_handler(CallbackQueryHandler(s.show_topics, pattern="^change_topic$"))
application.add_handler(CallbackQueryHandler(s.show_levels, pattern="^change_level$"))

# Обработчик проверки перевода (должен быть одним из последних)
# Он будет ловить любой текст, который не является командой или кнопкой меню
application.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND & ~filters.Text(all_button_texts),
    training.check_translation
))
