# app/handlers/training.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from app import crud, keyboards, gemini
from app.database import async_session_factory

logger = logging.getLogger(__name__)

CURRENT_PHRASE_KEY = 'current_phrase'


async def start_training_logic(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    """
    Основная логика начала тренировки. Эта функция не зависит от 'update'
    и может быть вызвана откуда угодно.
    """
    async with async_session_factory() as session:
        user = await crud.get_user_settings(session, tg_id=user_id)
        
        # --- УЛУЧШЕННАЯ ПРОВЕРКА НАСТРОЕК ---
        # Проверяем каждую настройку отдельно и даем пользователю конкретную подсказку.
        if not user.topic_id:
            await context.bot.send_message(chat_id=chat_id, text="❗️ Пожалуйста, сначала выберите '📚 Темы' в меню.")
            return
        if not user.level_id:
            await context.bot.send_message(chat_id=chat_id, text="❗️ Пожалуйста, сначала выберите '📈 Уровень' в меню.")
            return
        if not user.direction:
            await context.bot.send_message(chat_id=chat_id, text="❗️ Пожалуйста, сначала выберите '🔁 Направление' в меню.")
            return
        # --- КОНЕЦ УЛУЧШЕННОЙ ПРОВЕРКИ ---

        # Этот код теперь будет выполняться только если все настройки на месте
        phrase = await crud.get_random_phrase(session, user)

    if not phrase:
        await context.bot.send_message(
            chat_id=chat_id,
            text="😕 Не найдено фраз для ваших настроек. Попробуйте выбрать другую тему или уровень."
        )
        return

    context.user_data[CURRENT_PHRASE_KEY] = phrase
    
    source_lang, _ = user.direction.split('-')
    text_to_translate = getattr(phrase, f'text_{source_lang}')
    
    safe_text_to_translate = escape_markdown(text_to_translate, version=2)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Переведите фразу:\n\n`{safe_text_to_translate}`",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def start_training_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для текстовой команды '▶ Начать тренировку'."""
    await start_training_logic(
        context=context,
        chat_id=update.effective_chat.id,
        user_id=update.effective_user.id
    )

async def check_translation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проверяет перевод, отправленный пользователем.
    Обращается к Gemini API, форматирует ответ и сохраняет прогресс.
    """
    original_phrase = context.user_data.get(CURRENT_PHRASE_KEY)
    if not original_phrase:
        await update.message.reply_text("Чтобы начать, нажмите '▶ Начать тренировку' в меню.")
        return

    user_translation = update.message.text
    user_id = update.effective_user.id
    
    async with async_session_factory() as session:
        user = await crud.get_user_settings(session, tg_id=user_id)
        
        processing_message = await update.message.reply_text("🧠 Анализирую ваш перевод...")
        
        try:
            ai_feedback = await gemini.check_user_translation(
                original_phrase=original_phrase,
                user_translation=user_translation,
                direction=user.direction
            )
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            await processing_message.edit_text("😕 Произошла ошибка при обращении к AI. Попробуйте позже.")
            context.user_data.pop(CURRENT_PHRASE_KEY, None)
            return

        await crud.save_user_progress(
            session, user_id=user.id, phrase_id=original_phrase.id, score=ai_feedback.get('score', 0)
        )

    score = ai_feedback.get('score', 0)
    correct_translation = escape_markdown(ai_feedback.get('correct_translation', 'N/A'), version=2)
    mistakes = escape_markdown(ai_feedback.get('mistakes', ''), version=2)
    explanation = escape_markdown(ai_feedback.get('explanation', 'Нет комментария.'), version=2)

    response_text = (
        f"⭐ *Результат: {score}/100*\n\n"
        f"✅ *Правильный перевод:*\n`{correct_translation}`\n\n"
    )
    if mistakes:
        response_text += f"❌ *Ошибки:*\n_{mistakes}_\n\n"
    
    response_text += f"💬 *Комментарий:*\n{explanation}"
    
    await processing_message.edit_text(
        text=response_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=keyboards.after_training_keyboard(user.language)
    )
    
    context.user_data.pop(CURRENT_PHRASE_KEY, None)


async def next_phrase_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для inline-кнопки '▶️ Следующая фраза'."""
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    
    await start_training_logic(
        context=context,
        chat_id=query.message.chat_id,
        user_id=query.from_user.id
    )
