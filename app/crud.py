# app/crud.py

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import User, Phrase, Level, Topic, UserProgress

# --- User Functions ---

async def get_or_create_user(session: AsyncSession, tg_id: int, username: str | None = None) -> User:
    """
    Находит пользователя по tg_id или создает нового, если он не найден.
    Возвращает полную информацию о пользователе, включая level и topic.
    """
    result = await session.execute(
        select(User)
        .options(selectinload(User.level), selectinload(User.topic))
        .filter_by(tg_id=tg_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(tg_id=tg_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user, ['level', 'topic'])
    
    return user

async def update_user_setting(session: AsyncSession, tg_id: int, **kwargs):
    """Обновляет настройки пользователя (тему, уровень и т.д.)."""
    user = await get_or_create_user(session, tg_id)
    for key, value in kwargs.items():
        setattr(user, key, value)
    await session.commit()
    return user

async def update_user_state(session: AsyncSession, tg_id: int, state: str | None, phrase_id: int | None):
    """Обновляет состояние пользователя (режим и текущую фразу)."""
    user = await get_or_create_user(session, tg_id)
    user.state = state
    user.current_phrase_id = phrase_id
    await session.commit()
    return user

# --- Content Functions ---

async def get_all_topics(session: AsyncSession):
    result = await session.execute(select(Topic).order_by(Topic.id))
    return result.scalars().all()

async def get_all_levels(session: AsyncSession):
    result = await session.execute(select(Level).order_by(Level.sort_order))
    return result.scalars().all()

async def get_random_phrase(session: AsyncSession, user: User) -> Phrase | None:
    if not user.topic_id or not user.level_id:
        return None
        
    result = await session.execute(
        select(Phrase)
        .filter_by(topic_id=user.topic_id, level_id=user.level_id)
        .order_by(func.random())
        .limit(1)
    )
    return result.scalar_one_or_none()
    
async def get_phrase_by_id(session: AsyncSession, phrase_id: int) -> Phrase | None:
    result = await session.execute(select(Phrase).filter_by(id=phrase_id))
    return result.scalar_one_or_none()

async def save_user_progress(session: AsyncSession, user_id: int, phrase_id: int, score: int):
    progress = UserProgress(user_id=user_id, phrase_id=phrase_id, score=score, attempts=1)
    session.add(progress)
    await session.commit()
