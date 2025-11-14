# app/crud.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Phrase, Level, Topic, UserProgress
from sqlalchemy.orm import selectinload

# --- User Functions ---
async def get_or_create_user(session: AsyncSession, tg_id: int, username: str) -> User:
    result = await session.execute(select(User).filter_by(tg_id=tg_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(tg_id=tg_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user

async def update_user_setting(session: AsyncSession, tg_id: int, **kwargs):
    user = await get_or_create_user(session, tg_id, "") # username не важен при обновлении
    for key, value in kwargs.items():
        setattr(user, key, value)
    await session.commit()
    return user

async def get_user_settings(session: AsyncSession, tg_id: int) -> User:
    result = await session.execute(select(User).filter_by(tg_id=tg_id))
    return result.scalar_one()

# --- Content Functions ---
async def get_all_topics(session: AsyncSession):
    result = await session.execute(select(Topic).order_by(Topic.id))
    return result.scalars().all()

async def get_all_levels(session: AsyncSession):
    result = await session.execute(select(Level).order_by(Level.sort_order))
    return result.scalars().all()

async def get_random_phrase(session: AsyncSession, user: User) -> Phrase:
    result = await session.execute(
        select(Phrase)
        .filter_by(topic_id=user.topic_id, level_id=user.level_id)
        .order_by(func.random())
        .limit(1)
    )
    return result.scalar_one_or_none()
    
async def save_user_progress(session: AsyncSession, user_id: int, phrase_id: int, score: int):
    # Здесь можно добавить логику обновления попыток, если запись уже есть
    progress = UserProgress(user_id=user_id, phrase_id=phrase_id, score=score, attempts=1)
    session.add(progress)
    await session.commit()

async def get_user_info(session: AsyncSession, tg_id: int) -> User | None:
    """
    Получает полную информацию о пользователе, включая связанные
    объекты Level и Topic.
    """
    result = await session.execute(
        select(User)
        .options(selectinload(User.level), selectinload(User.topic))
        .filter_by(tg_id=tg_id)
    )
    return result.scalar_one_or_none()