# app/handlers/common.py
from telegram import Update
from telegram.ext import ContextTypes
from app import crud, keyboards
from app.database import async_session_factory
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with async_session_factory() as session:
        await crud.get_or_create_user(session, tg_id=user.id, username=user.username)
    
    await update.message.reply_html(
        f"Привет, <b>@{user.username}!</b>\n\n"
        "Я бот для изучения английского. Выбери язык интерфейса:",
        reply_markup=keyboards.language_choice_keyboard()
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.split('_')[1]
    
    async with async_session_factory() as session:
        await crud.update_user_setting(session, tg_id=query.from_user.id, language=lang_code)
    
    # Отправляем приветствие и главное меню
    await query.edit_message_text(
        text="Отлично! Язык сохранен.",
        reply_markup=None
    )
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="Добро пожаловать в главное меню!",
        reply_markup=keyboards.main_menu_keyboard(lang_code)
    )

    # app/handlers/common.py

# ... (ваш код для start и set_language) ...

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает профиль пользователя с его текущими настройками.
    """
    user_id = update.effective_user.id
    async with async_session_factory() as session:
        # Получаем пользователя со всеми связанными данными (уровень, тема)
        # Для этого нужно будет немного доработать crud-функцию
        user_info = await crud.get_user_info(session, tg_id=user_id)
    
    if user_info:
        # Формируем красивое сообщение
        level_name_raw = user_info.level.name_ru if user_info.level else "не выбран"
        topic_name_raw = user_info.topic.name_ru if user_info.topic else "не выбрана"

        level_name = escape_markdown(level_name_raw, version=2)
        topic_name = escape_markdown(topic_name_raw, version=2)

        direction_map = {
            'ru-en': 'Русский 🇷🇺 → Английский 🇬🇧',
            'en-ru': 'Английский 🇬🇧 → Русский 🇷🇺',
        }
        direction_text_raw = direction_map.get(user_info.direction, "не выбрано")
        direction_text = escape_markdown(direction_text_raw, version=2)

        text = (
            f"👤 *Ваш профиль*\n\n"
            # Обратите внимание, что `user_info.language` в `...` не нужно экранировать
            # так как этот текст мы контролируем и он не содержит спецсимволов.
            f"— *Язык интерфейса:* `{user_info.language}`\n" 
            f"— *Текущий уровень:* {level_name}\n"
            f"— *Текущая тема:* {topic_name}\n"
            f"— *Направление перевода:* {direction_text}\n\n"
            "Чтобы изменить настройки, используйте кнопки в главном меню\\." # Точку в конце тоже надо экранировать!
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text("Не удалось найти ваш профиль. Попробуйте нажать /start.")

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Здесь будут настройки. Например, уведомления или смена языка. Эта функция пока в разработке."
    await update.message.reply_text(text)