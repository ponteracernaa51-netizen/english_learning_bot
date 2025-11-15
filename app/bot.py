# app/bot.py

from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, 
                          MessageHandler, filters)
from app.core.config import settings
from app.handlers import common, settings as s, training
from app.keyboards import button_texts # Импортируем наш словарь с текстами

# Создаем экземпляр Application
application = Application.builder().token(settings.TELEGRAM_TOKEN).build()

# --- ИЗМЕНЕНИЕ: Динамически создаем списки текстов для фильтров ---
# Собираем все варианты текста для каждой кнопки из всех языков
themes_texts = [lang['themes'] for lang in button_texts.values()]
level_texts = [lang['level'] for lang in button_texts.values()]
direction_texts = [lang['direction'] for lang in button_texts.values()]
start_texts = [lang['start'] for lang in button_texts.values()]
profile_texts = [lang['profile'] for lang in button_texts.values()]
settings_texts = [lang['settings'] for lang in button_texts.values()]

# Этот сет теперь автоматически включает и узбекские тексты. Он используется
# чтобы обработчик перевода не срабатывал на нажатие кнопок.
all_button_texts = {text for lang in button_texts.values() for text in lang.values()}

# --- Регистрация обработчиков с новыми динамическими фильтрами ---

# Общие команды
application.add_handler(CommandHandler("start", common.start))
application.add_handler(CallbackQueryHandler(common.set_language, pattern="^lang_"))

# Настройки (реагируем на текстовые сообщения из ReplyKeyboard)
application.add_handler(MessageHandler(filters.Text(themes_texts), s.show_topics))
application.add_handler(MessageHandler(filters.Text(level_texts), s.show_levels))
application.add_handler(MessageHandler(filters.Text(direction_texts), s.show_direction))
application.add_handler(MessageHandler(filters.Text(profile_texts), common.show_profile))
application.add_handler(MessageHandler(filters.Text(settings_texts), common.show_settings))

# Обработчики для Inline-кнопок настроек
application.add_handler(CallbackQueryHandler(s.set_topic, pattern="^topic_"))
application.add_handler(CallbackQueryHandler(s.set_level, pattern="^level_"))
application.add_handler(CallbackQueryHandler(s.set_direction, pattern="^dir_"))

# Тренировка
application.add_handler(MessageHandler(filters.Text(start_texts), training.start_training_command))
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
