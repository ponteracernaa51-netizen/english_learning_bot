# app/handlers/training.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from google.api_core import exceptions as google_exceptions ### ДОБАВЛЕНО ###

from app import crud, keyboards, gemini
from app.database import async_session_factory

logger = logging.getLogger(__name__)

# CURRENT_PHRASE_KEY = 'current_phrase' ### ИЗМЕНЕНО: Эта переменная больше не нужна


async def start_training_logic(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    """
    Основная логика начала тренировки. Эта функция не зависит от 'update'
    и может быть вызвана откуда угодно.
    """
    async with async_session_factory() as session:
        user = await crud.get_user_settings(session, tg_id=user_id)
        
        if not user.topic_id:
            await context.bot.send_message(chat_id=chat_id, text="❗️ Пожалуйста, сначала выберите '📚 Темы' в меню.")
            return
        if not user.level_id:
            await context.bot.send_message(chat_id=chat_id, text="❗️ Пожалуйста, сначала выберите '📈 Уровень' в меню.")
            return
        if not user.direction:
            await context.bot.send_message(chat_id=chat_id, text="❗️ Пожалуйста, сначала выберите '🔁 Направление' в меню.")
            return

        phrase = await crud.get_random_phrase(session, user)

    if not phrase:
        await context.bot.send_message(
            chat_id=chat_id,
            text="😕 Не найдено фраз для ваших настроек. Попробуйте выбрать другую тему или уровень."
        )
        return

    source_lang, _ = user.direction.split('-')
    text_to_translate = getattr(phrase, f'text_{source_lang}')
    
    safe_text_to_translate = escape_markdown(text_to_translate, version=2)
    
    ### ИЗМЕНЕНО: Полностью переработана логика сохранения состояния ###
    # 1. Отправляем сообщение и СОХРАНЯЕМ его
    sent_message = await context.bot.send_message(
        chat_id=chat_id,
        text=f"Переведите фразу:\n\n`{safe_text_to_translate}`",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    # 2. Инициализируем словарь для отслеживания, если его еще нет
    if 'pending_translations' not in context.chat_data:
        context.chat_data['pending_translations'] = {}

    # 3. Создаем связь: ID сообщения -> ID фразы. Теперь бот точно знает, на какой вопрос ждут ответ.
    context.chat_data['pending_translations'][sent_message.message_id] = phrase.id


async def start_training_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для текстовой команды '▶ Начать тренировку'."""
    await start_training_logic(
        context=context,
        chat_id=update.effective_chat.id,
        user_id=update.effective_user.id
    )


async def check_translation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ### ИЗМЕНЕНО: Функция полностью переписана для работы с ответами на сообщения ###
    Проверяет перевод, отправленный пользователем В ОТВЕТ на сообщение бота.
    """
    # 1. Проверяем, является ли это ответом на сообщение нашего бота
    if not update.message.reply_to_message or update.message.reply_to_message.from_user.id != context.bot.id:
        # Если это просто текст, можно мягко подсказать, что делать
        await update.message.reply_text(
            "Чтобы я понял, что вы переводите, пожалуйста, отвечайте (reply) на мое сообщение с фразой.",
            disable_notification=True
        )
        return

    original_message_id = update.message.reply_to_message.message_id
    
    # 2. Получаем ID фразы из нашего нового хранилища chat_data
    pending_translations = context.chat_data.get('pending_translations', {})
    phrase_id = pending_translations.get(original_message_id)

    if not phrase_id:
        await update.message.reply_text("Это уже устаревшая фраза. Давайте попробуем новую! Нажмите '▶️ Следующая фраза'.")
        return

    user_translation = update.message.text
    user_id = update.effective_user.id
    
    async with async_session_factory() as session:
        # 3. Получаем оригинальную фразу и пользователя из БД по ID
        user = await crud.get_user_settings(session, tg_id=user_id)
        original_phrase = await crud.get_phrase_by_id(session, phrase_id)

        if not original_phrase or not user:
            await update.message.reply_text("Не удалось найти данные для проверки. Попробуйте начать заново.")
            return

        processing_message = await update.message.reply_text("🧠 Анализирую ваш перевод...")
        
        # 4. Улучшенная обработка ошибок API
        try:
            ai_feedback = await gemini.check_user_translation(
                original_phrase=original_phrase,
                user_translation=user_translation,
                direction=user.direction
            )
        except google_exceptions.ResourceExhausted:
            await processing_message.edit_text("😔 Слишком много запросов, я не успеваю. Пожалуйста, попробуйте через минуту.")
            return
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            await processing_message.edit_text("😕 Произошла ошибка при обращении к AI. Попробуйте позже.")
            return
        finally:
            # 5. ОЧЕНЬ ВАЖНО: Удаляем ID из отслеживания, чтобы на него нельзя было ответить дважды
            pending_translations.pop(original_message_id, None)

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
