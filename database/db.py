from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, FlowRecord, SprintRecord
from datetime import datetime, timedelta

async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None = None,
                             first_name: str | None = None, last_name: str | None = None) -> User:
    """Получает пользователя из БД или создает нового, если его нет."""
    result = await session.execute(select(User).filter_by(telegram_id=telegram_id))
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name, last_name=last_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user

async def add_flow_record(session: AsyncSession, user_id: int, duration_minutes: int) -> FlowRecord:
    """Добавляет запись о времени в состоянии потока."""
    flow_record = FlowRecord(user_id=user_id, first_name=first_name, duration_minutes=duration_minutes)
    session.add(flow_record)
    await session.commit()
    await session.refresh(flow_record)
    return flow_record

async def add_sprint_record(session: AsyncSession, user_id: int, duration_minutes: int) -> SprintRecord:
    """Добавляет запись о спринте."""
    sprint_record = SprintRecord(user_id=user_id, duration_minutes=duration_minutes)
    session.add(sprint_record)
    await session.commit()
    await session.refresh(sprint_record)
    return sprint_record

async def get_user_productivity_history(session: AsyncSession, user_id: int, limit: int = 10):
    """Получает последние записи о продуктивности пользователя (поток и спринты)."""
    flow_history = await session.execute(
        select(FlowRecord)
        .filter_by(user_id=user_id)
        .order_by(FlowRecord.recorded_at.desc())
        .limit(limit)
    )
    sprint_history = await session.execute(
        select(SprintRecord)
        .filter_by(user_id=user_id)
        .order_by(SprintRecord.recorded_at.desc())
        .limit(limit)
    )
    return flow_history.scalars().all(), sprint_history.scalars().all()
