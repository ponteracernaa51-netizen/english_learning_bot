# app/handlers/settings.py (ПОЛНАЯ ВЕРСИЯ)

from telegram import Update
from telegram.ext import ContextTypes
from app import crud, keyboards
from app.database import async_session_factory
from app.handlers.training import STATE_AWAITING_TRANSLATION # <-- Импортируем константу

async def show_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with async_session_factory() as session:
        user = await crud.get_or_create_user(session, update.effective_user.id, update.effective_user.username)
        
        # Если пользователь переводил фразу, отменяем это состояние
        if user.state == STATE_AWAITING_TRANSLATION:
            await crud.update_user_state(session, user.tg_id, None, None)
            await update.effective_message.reply_text("Тренировка отменена.")

        topics = await crud.get_all_topics(session)
    
    keyboard = keyboards.create_dynamic_keyboard(topics, 'topic', user.language)
    await update.effective_message.reply_text("Выберите тему для тренировки:", reply_markup=keyboard)

async def set_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic_id = int(query.data.split('_')[1])

    async with async_session_factory() as session:
        await crud.update_user_setting(session, tg_id=query.from_user.id, topic_id=topic_id)
    
    await query.edit_message_text("✅ Тема сохранена!")

async def show_levels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with async_session_factory() as session:
        user = await crud.get_or_create_user(session, update.effective_user.id, update.effective_user.username)

        # Если пользователь переводил фразу, отменяем это состояние
        if user.state == STATE_AWAITING_TRANSLATION:
            await crud.update_user_state(session, user.tg_id, None, None)
            await update.effective_message.reply_text("Тренировка отменена.")

        levels = await crud.get_all_levels(session)
    
    keyboard = keyboards.create_dynamic_keyboard(levels, 'level', user.language)
    await update.effective_message.reply_text("Выберите ваш уровень:", reply_markup=keyboard)

async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level_id = int(query.data.split('_')[1])

    async with async_session_factory() as session:
        await crud.update_user_setting(session, tg_id=query.from_user.id, level_id=level_id)
    
    await query.edit_message_text("✅ Уровень сохранен!")

async def show_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with async_session_factory() as session:
        user = await crud.get_or_create_user(session, update.effective_user.id, update.effective_user.username)
        
        # Если пользователь переводил фразу, отменяем это состояние
        if user.state == STATE_AWAITING_TRANSLATION:
            await crud.update_user_state(session, user.tg_id, None, None)
            await update.effective_message.reply_text("Тренировка отменена.")

    await update.message.reply_text(
        "Выберите направление перевода:",
        reply_markup=keyboards.direction_keyboard()
    )

async def set_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    direction = query.data.split('_')[1]

    async with async_session_factory() as session:
        await crud.update_user_setting(session, tg_id=query.from_user.id, direction=direction)
    
    await query.edit_message_text("✅ Направление сохранено!")
