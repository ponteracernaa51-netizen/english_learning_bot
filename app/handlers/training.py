# app/handlers/training.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from google.api_core import exceptions as google_exceptions

from app import crud, keyboards, gemini
from app.database import async_session_factory

logger = logging.getLogger(__name__)

# Название состояния, которое мы будем хранить в БД
STATE_AWAITING_TRANSLATION = 'awaiting_translation'


async def start_training_logic(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    """
    Основная логика начала тренировки, теперь работающая с БД.
    """
    async with async_session_factory() as session:
        user = await crud.get_user_settings(session, tg_id=user_id)
        
        # Проверяем состояние пользователя в БД
        if user.state == STATE_AWAITING_TRANSLATION:
            await context.bot.send_message(chat_id=chat_id, text="❗️ Пожалуйста, сначала завершите перевод текущей фразы.")
            return
        
        if not user.topic_id or not user.level_id or not user.direction:
            await context.bot.send_message(chat_id=chat_id, text="❗️ Пожалуйста, сначала выберите все настройки в меню.")
            return

        phrase = await crud.get_random_phrase(session, user)

        if not phrase:
            await context.bot.send_message(chat_id=chat_id, text="😕 Не найдено фраз для ваших настроек.")
            return

        # Устанавливаем состояние в БД
        await crud.update_user_state(session, user_id, STATE_AWAITING_TRANSLATION, phrase.id)

    source_lang, _ = user.direction.split('-')
    text_to_translate = getattr(phrase, f'text_{source_lang}')
    safe_text_to_translate = escape_markdown(text_to_translate, version=2)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Переведите фразу:\n\n`{safe_text_to_translate}`",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def start_training_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_training_logic(context, update.effective_chat.id, update.effective_user.id)

async def check_translation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проверяет перевод, основываясь на состоянии из БД.
    """
    user_id = update.effective_user.id
    user_translation = update.message.text
    
    async with async_session_factory() as session:
        user = await crud.get_user_settings(session, tg_id=user_id)

        if user.state != STATE_AWAITING_TRANSLATION or not user.current_phrase_id:
            await update.message.reply_text("Чтобы начать, нажмите '▶ Начать тренировку' в меню.")
            return
        
        original_phrase = await crud.get_phrase_by_id(session, user.current_phrase_id)
        if not original_phrase:
            await update.message.reply_text("Произошла ошибка, не могу найти исходную фразу. Начнем заново.")
            await crud.update_user_state(session, user_id, None, None) # Очищаем состояние в БД
            return

    processing_message = await update.message.reply_text("🧠 Анализирую ваш перевод...")
    
    try:
        ai_feedback = await gemini.check_user_translation(
            original_phrase=original_phrase,
            user_translation=user_translation,
            direction=user.direction
        )
        
        async with async_session_factory() as session:
            # Важно: user_id здесь это ID из таблицы users, а не tg_id
            await crud.save_user_progress(session, user.id, original_phrase.id, ai_feedback.get('score', 0))

        # ... (код форматирования ответа остается таким же) ...
        score = ai_feedback.get('score', 0)
        correct_translation = escape_markdown(ai_feedback.get('correct_translation', 'N/A'), version=2)
        mistakes = escape_markdown(ai_feedback.get('mistakes', ''), version=2)
        explanation = escape_markdown(ai_feedback.get('explanation', 'Нет комментария.'), version=2)
        response_text = (f"⭐ *Результат: {score}/100*\n\n✅ *Правильный перевод:*\n`{correct_translation}`\n\n")
        if mistakes: response_text += f"❌ *Ошибки:*\n_{mistakes}_\n\n"
        response_text += f"💬 *Комментарий:*\n{explanation}"
        
        await processing_message.edit_text(
            text=response_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=keyboards.after_training_keyboard(user.language)
        )
        
        # Очищаем состояние в БД после успешного ответа
        async with async_session_factory() as session:
            await crud.update_user_state(session, user_id, None, None)

    except (google_exceptions.ResourceExhausted, Exception) as e:
        logger.error(f"Error during translation check for user {user_id}: {e}", exc_info=True)
        error_message = "😔 Слишком много запросов, я не успеваю." if isinstance(e, google_exceptions.ResourceExhausted) else "😕 Произошла ошибка при обращении к AI. Попробуйте позже."
        await processing_message.edit_text(error_message)
        # Состояние в БД не очищаем, чтобы пользователь мог повторить попытку
        return

async def next_phrase_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    await start_training_logic(context, query.message.chat_id, query.from_user.id)
