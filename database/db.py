from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, FlowRecord, SprintRecord
from datetime import datetime, timedelta

async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None = None) -> User:
    """Получает пользователя из БД или создает нового, если его нет."""
    result = await session.execute(select(User).filter_by(telegram_id=telegram_id))
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        # Обновляем username, если он изменился
        if user.username != username:
            user.username = username
            await session.commit()
            await session.refresh(user)
    return user

async def add_flow_record(session: AsyncSession, user_id: int, duration_minutes: int, username: str | None = None) -> FlowRecord:
    """Добавляет запись о времени в состоянии потока."""
    flow_record = FlowRecord(user_id=user_id, duration_minutes=duration_minutes, username=username)
    session.add(flow_record)
    await session.commit()
    await session.refresh(flow_record)
    return flow_record

async def add_sprint_record(session: AsyncSession, user_id: int, duration_minutes: int, username: str | None = None) -> SprintRecord:
    """Добавляет запись о спринте."""
    sprint_record = SprintRecord(user_id=user_id, duration_minutes=duration_minutes, username=username)
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

async def get_productivity_sum_by_day(
    session: AsyncSession,
    user_id: int,
    start_dt: datetime,
    end_dt: datetime,
) -> dict:
    """Возвращает словарь {date: total_minutes} по дням для диапазона [start_dt, end_dt]."""
    # Поток по дням
    flow_stmt = (
        select(func.date(FlowRecord.recorded_at), func.coalesce(func.sum(FlowRecord.duration_minutes), 0))
        .where(
            FlowRecord.user_id == user_id,
            FlowRecord.recorded_at >= start_dt,
            FlowRecord.recorded_at <= end_dt,
        )
        .group_by(func.date(FlowRecord.recorded_at))
    )
    flow_rows = (await session.execute(flow_stmt)).all()
    # Спринты по дням
    sprint_stmt = (
        select(func.date(SprintRecord.recorded_at), func.coalesce(func.sum(SprintRecord.duration_minutes), 0))
        .where(
            SprintRecord.user_id == user_id,
            SprintRecord.recorded_at >= start_dt,
            SprintRecord.recorded_at <= end_dt,
        )
        .group_by(func.date(SprintRecord.recorded_at))
    )
    sprint_rows = (await session.execute(sprint_stmt)).all()

    totals: dict = {}
    for d, minutes in flow_rows:
        totals[d] = totals.get(d, 0) + int(minutes or 0)
    for d, minutes in sprint_rows:
        totals[d] = totals.get(d, 0) + int(minutes or 0)
    return totals

async def get_productivity_sum_for_month(
    session: AsyncSession,
    user_id: int,
    year: int,
    month: int,
) -> int:
    """Возвращает суммарные минуты продуктивности за конкретный месяц."""
    # начало месяца
    start_dt = datetime(year=year, month=month, day=1)
    # вычисляем начало следующего месяца
    if month == 12:
        next_month = datetime(year=year + 1, month=1, day=1)
    else:
        next_month = datetime(year=year, month=month + 1, day=1)

    flow_stmt = (
        select(func.coalesce(func.sum(FlowRecord.duration_minutes), 0))
        .where(
            FlowRecord.user_id == user_id,
            FlowRecord.recorded_at >= start_dt,
            FlowRecord.recorded_at < next_month,
        )
    )
    sprint_stmt = (
        select(func.coalesce(func.sum(SprintRecord.duration_minutes), 0))
        .where(
            SprintRecord.user_id == user_id,
            SprintRecord.recorded_at >= start_dt,
            SprintRecord.recorded_at < next_month,
        )
    )
    flow_sum = (await session.execute(flow_stmt)).scalar() or 0
    sprint_sum = (await session.execute(sprint_stmt)).scalar() or 0
    return int(flow_sum) + int(sprint_sum)

async def get_all_months_with_data(session: AsyncSession, user_id: int) -> list[tuple[int, int, int]]:
    """Возвращает список кортежей (year, month, total_minutes) для всех месяцев с данными, отсортированных по дате (новые сначала)."""
    # Получаем уникальные месяцы из flow_records
    flow_stmt = (
        select(
            func.extract('year', FlowRecord.recorded_at).label('year'),
            func.extract('month', FlowRecord.recorded_at).label('month'),
            func.coalesce(func.sum(FlowRecord.duration_minutes), 0).label('minutes')
        )
        .where(FlowRecord.user_id == user_id)
        .group_by(func.extract('year', FlowRecord.recorded_at), func.extract('month', FlowRecord.recorded_at))
    )
    flow_rows = (await session.execute(flow_stmt)).all()
    
    # Получаем уникальные месяцы из sprint_records
    sprint_stmt = (
        select(
            func.extract('year', SprintRecord.recorded_at).label('year'),
            func.extract('month', SprintRecord.recorded_at).label('month'),
            func.coalesce(func.sum(SprintRecord.duration_minutes), 0).label('minutes')
        )
        .where(SprintRecord.user_id == user_id)
        .group_by(func.extract('year', SprintRecord.recorded_at), func.extract('month', SprintRecord.recorded_at))
    )
    sprint_rows = (await session.execute(sprint_stmt)).all()
    
    # Объединяем данные
    totals: dict[tuple[int, int], int] = {}
    for year, month, minutes in flow_rows:
        key = (int(year), int(month))
        totals[key] = totals.get(key, 0) + int(minutes or 0)
    for year, month, minutes in sprint_rows:
        key = (int(year), int(month))
        totals[key] = totals.get(key, 0) + int(minutes or 0)
    
    # Сортируем по дате (новые сначала)
    result = [(year, month, minutes) for (year, month), minutes in totals.items()]
    result.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return result

async def get_total_productivity(session: AsyncSession, user_id: int) -> int:
    """Возвращает суммарные минуты продуктивности за всю историю пользователя."""
    flow_stmt = (
        select(func.coalesce(func.sum(FlowRecord.duration_minutes), 0))
        .where(FlowRecord.user_id == user_id)
    )
    sprint_stmt = (
        select(func.coalesce(func.sum(SprintRecord.duration_minutes), 0))
        .where(SprintRecord.user_id == user_id)
    )
    flow_sum = (await session.execute(flow_stmt)).scalar() or 0
    sprint_sum = (await session.execute(sprint_stmt)).scalar() or 0
    return int(flow_sum) + int(sprint_sum)
