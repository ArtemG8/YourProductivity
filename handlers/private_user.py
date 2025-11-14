import random
from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from lexicon import LEXICON_RU, MOTIVATIONAL_MESSAGES
from database import (
    get_or_create_user,
    add_flow_record,
    add_sprint_record,
    get_user_productivity_history,
    get_productivity_sum_by_day,
    get_productivity_sum_for_month,
    get_all_months_with_data,
    get_total_productivity,
)
from keyboards import create_cancel_keyboard, create_flow_active_kb, create_flow_paused_kb, create_history_inline_kb
from states import RecordStates

router = Router()

# Обработчик команды /start
@router.message(CommandStart())
async def process_start_command(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear() # Очищаем состояние, если пользователь перезапускает бота
    user_data = message.from_user
    user = await get_or_create_user(
        session,
        telegram_id=user_data.id,
        username=user_data.username
    )
    if user.created_at == user.created_at: # Простая проверка на нового/вернувшегося пользователя
        await message.answer(LEXICON_RU['/start'])
    else:
        await message.answer(LEXICON_RU['welcome_back'])

# Обработчик команды /help
@router.message(Command(commands='/start'))
async def process_help_command(message: Message):
    await message.answer(LEXICON_RU['/start'])

# Обработчик команды /record_flow — запускает таймер потока
@router.message(Command(commands='record_flow'), StateFilter(None))
async def process_record_flow_command(message: Message, state: FSMContext):
    now_ts = int(datetime.utcnow().timestamp())
    sent = await message.answer(LEXICON_RU['/record_flow'], reply_markup=create_flow_active_kb())
    await state.update_data(
        flow_start_ts=now_ts,
        flow_accumulated_sec=0,
        flow_is_paused=False,
        flow_message_id=sent.message_id,
        flow_chat_id=sent.chat.id,
    )
    await state.set_state(RecordStates.flow_active)

def _format_hh_mm(total_seconds: int) -> tuple[int, int]:
    minutes = total_seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    return hours, minutes

# Пауза таймера
@router.callback_query(StateFilter(RecordStates.flow_active), F.data == 'flow_pause')
async def on_flow_pause(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    start_ts = data.get('flow_start_ts')
    accumulated = data.get('flow_accumulated_sec', 0)
    now_ts = int(datetime.utcnow().timestamp())
    if start_ts is not None:
        accumulated += max(0, now_ts - int(start_ts))
    await state.update_data(flow_accumulated_sec=accumulated, flow_is_paused=True, flow_start_ts=None)
    await callback.message.edit_reply_markup(reply_markup=create_flow_paused_kb())
    await callback.answer(LEXICON_RU['flow_paused'], show_alert=False)
    await state.set_state(RecordStates.flow_paused)

# Возобновление таймера
@router.callback_query(StateFilter(RecordStates.flow_paused), F.data == 'flow_resume')
async def on_flow_resume(callback: CallbackQuery, state: FSMContext):
    now_ts = int(datetime.utcnow().timestamp())
    await state.update_data(flow_start_ts=now_ts, flow_is_paused=False)
    await callback.message.edit_reply_markup(reply_markup=create_flow_active_kb())
    await callback.answer(LEXICON_RU['flow_resumed'], show_alert=False)
    await state.set_state(RecordStates.flow_active)

# Завершение таймера
@router.callback_query(StateFilter('*'), F.data == 'flow_finish')
async def on_flow_finish(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    accumulated = int(data.get('flow_accumulated_sec', 0))
    start_ts = data.get('flow_start_ts')
    if start_ts is not None and not data.get('flow_is_paused', False):
        now_ts = int(datetime.utcnow().timestamp())
        accumulated += max(0, now_ts - int(start_ts))

    total_seconds = max(0, accumulated)
    hours, minutes = _format_hh_mm(total_seconds)
    total_minutes = total_seconds // 60

    # Запись в БД в минутах (округление вниз)
    await add_flow_record(session, user_id=callback.from_user.id, duration_minutes=total_minutes, username=callback.from_user.username)

    # Скрываем клавиатуру под сообщением таймера
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Выбираем сообщение в зависимости от времени концентрации
    if total_minutes < 60:
        # Меньше часа
        message_text = LEXICON_RU['flow_finished_short'].format(hours=hours, minutes=minutes)
    elif total_minutes < 90:
        # Больше часа, но меньше 1.5 часов
        message_text = LEXICON_RU['flow_finished_good'].format(hours=hours, minutes=minutes)
    else:
        # Больше 1 часа 30 минут
        message_text = LEXICON_RU['flow_finished'].format(hours=hours, minutes=minutes)

    await callback.message.answer(message_text, reply_markup=create_history_inline_kb())
    await state.clear()
    await callback.answer()

# Отмена
@router.callback_query(StateFilter('*'), F.data == 'flow_cancel')
async def on_flow_cancel(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.clear()
    await callback.message.answer(LEXICON_RU['cancel_action'])
    await callback.answer()

# Обработчик команды /record_sprint
@router.message(Command(commands='record_sprint'), StateFilter(None))
async def process_record_sprint_command(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['/record_sprint'], reply_markup=create_cancel_keyboard())
    await state.set_state(RecordStates.waiting_for_sprint_duration)

# Обработчик длительности спринта
@router.message(StateFilter(RecordStates.waiting_for_sprint_duration))
async def process_sprint_duration(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == LEXICON_RU['cancel_button']:
        await state.clear()
        await message.answer(LEXICON_RU['cancel_action'], reply_markup=ReplyKeyboardRemove())
        return

    try:
        duration = int(message.text)
        if duration <= 0:
            await message.answer(LEXICON_RU['invalid_sprint_duration'])
            return
        await add_sprint_record(session, user_id=message.from_user.id, duration_minutes=duration, username=message.from_user.username)
        await message.answer(LEXICON_RU['sprint_recorded'].format(duration=duration), reply_markup=ReplyKeyboardRemove())
        await state.clear()
    except ValueError:
        await message.answer(LEXICON_RU['invalid_sprint_duration'])

#Форматирование вывода часов и минут
def _format_hours_minutes(total_minutes: int) -> tuple[int, int]:
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return hours, minutes

# Форматирование вывода месяцев
def _format_date_dd_mm_yyyy(dt: datetime) -> str:
    month_names = {
        1: "января", 2: "февраля", 3: "марта",
        4: "апреля", 5: "мая", 6: "июня",
        7: "июля", 8: "августа", 9: "сентября",
        10: "октября", 11: "ноября", 12: "декабря"
    }
    day = dt.day
    month = month_names[dt.month]
    year = dt.year
    return f"{day:02d} {month} {year}"

# Обработчик кнопок и функционала  /history
def _history_kb(mode: str, weeks_offset: int = 0, month_offset: int = 0):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    kb = InlineKeyboardBuilder()
    if mode == 'days':
        kb.row(
            InlineKeyboardButton(text=LEXICON_RU['btn_hist_prev_weeks'], callback_data=f'hist:days:{weeks_offset+1}:0'),
            InlineKeyboardButton(text=LEXICON_RU['btn_hist_next_weeks'], callback_data=f'hist:days:{weeks_offset-1}:0'),
        )
        kb.row(InlineKeyboardButton(text=LEXICON_RU['btn_hist_months'], callback_data=f'hist:months:0:0'))
    else:
        # months mode - показываем все месяцы
        kb.row(InlineKeyboardButton(text=LEXICON_RU['btn_hist_days'], callback_data=f'hist:days:0:0'))
    return kb.as_markup()

async def _render_history_days(session: AsyncSession, user_id: int, weeks_offset: int = 0) -> str:
    today = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=0)
    window_start = today - timedelta(days=13)
    shift_days = weeks_offset * 14
    start_dt = window_start - timedelta(days=shift_days)
    end_dt = today - timedelta(days=shift_days)

    by_day = await get_productivity_sum_by_day(session, user_id, start_dt, end_dt)

    lines = [LEXICON_RU['history_days_header']]
    total_minutes = 0
    # выводим по дням от старого к новому
    for i in range(14):
        day_dt = (start_dt + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        # ключи by_day приходят как date, приведём к той же дате
        key_date = day_dt.date()
        minutes = int(by_day.get(key_date, 0))
        total_minutes += minutes
        h, m = _format_hours_minutes(minutes)
        lines.append(f"- {h} часов {m} минут ({_format_date_dd_mm_yyyy(day_dt)})")

    h_tot, m_tot = _format_hours_minutes(total_minutes)
    lines.append(LEXICON_RU['history_total'].format(hours=h_tot, minutes=m_tot))
    # Если нет данных в окне
    if total_minutes == 0:
        lines.insert(1, LEXICON_RU['history_no_data_period'])
    return "\n".join(lines)

async def _render_history_month(session: AsyncSession, user_id: int, month_offset: int = 0) -> str:
    # Получаем все месяцы с данными
    months_data = await get_all_months_with_data(session, user_id)
    
    lines = [LEXICON_RU['history_months_header']]
    
    # Если нет данных за месяцы
    if not months_data:
        lines.append(LEXICON_RU['history_no_data_period'])
    else:
        # Форматируем названия месяцев (именительный падеж)
        month_names = {
            1: "январь", 2: "февраль", 3: "март",
            4: "апрель", 5: "май", 6: "июнь",
            7: "июль", 8: "август", 9: "сентябрь",
            10: "октябрь", 11: "ноябрь", 12: "декабрь"
        }
        
        # Показываем все месяцы с данными
        for year, month, total_minutes in months_data:
            h, m = _format_hours_minutes(total_minutes)
            month_name = month_names[month]
            lines.append(f"- {h} часов {m} минут ({month_name} {year})")
    
    # Итоговая статистика за всю историю
    total_all_minutes = await get_total_productivity(session, user_id)
    h_tot, m_tot = _format_hours_minutes(total_all_minutes)
    lines.append(f"Итого: {h_tot} часов {m_tot} минут")
    
    return "\n".join(lines)

# Обработчик команды /history
@router.message(Command(commands='history'))
async def process_history_command(message: Message, session: AsyncSession):
    text = await _render_history_days(session, user_id=message.from_user.id, weeks_offset=0)
    await message.answer(text, reply_markup=_history_kb('days', weeks_offset=0))

# Обработчик inline-кнопки "История"
@router.callback_query(F.data == 'show_history')
async def process_history_inline_button(callback: CallbackQuery, session: AsyncSession):
    text = await _render_history_days(session, user_id=callback.from_user.id, weeks_offset=0)
    await callback.message.answer(text, reply_markup=_history_kb('days', weeks_offset=0))
    await callback.answer()

@router.callback_query(F.data.startswith('hist:'))
async def on_history_pagination(callback: CallbackQuery, session: AsyncSession):
    # Формат колбэка: hist:{mode}:{weeks_offset}:{month_offset}
    try:
        _, mode, weeks_offset_str, month_offset_str = callback.data.split(':', 3)
        weeks_offset = int(weeks_offset_str)
        month_offset = int(month_offset_str)
    except Exception:
        await callback.answer()
        return

    if mode == 'days':
        text = await _render_history_days(session, user_id=callback.from_user.id, weeks_offset=weeks_offset)
        await callback.message.edit_text(text)
        await callback.message.edit_reply_markup(reply_markup=_history_kb('days', weeks_offset=weeks_offset))
    else:
        text = await _render_history_month(session, user_id=callback.from_user.id, month_offset=month_offset)
        await callback.message.edit_text(text)
        await callback.message.edit_reply_markup(reply_markup=_history_kb('months', month_offset=month_offset))
    await callback.answer()

# Обработчик команды /motivate
@router.message(Command(commands='motivate'))
async def process_motivate_command(message: Message):
    motivation_message = random.choice(MOTIVATIONAL_MESSAGES)
    await message.answer(LEXICON_RU['/motivate'].format(message=motivation_message))

# Обработчик отмены для любого состояния
@router.message(StateFilter('*'), F.text == LEXICON_RU['cancel_button'])
async def process_cancel_command_state(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(LEXICON_RU['cancel_action'], reply_markup=ReplyKeyboardRemove())

# Обработчик для неопознанных команд
@router.message()
async def send_unknown_message(message: Message):
    await message.answer(LEXICON_RU['unknown_command'])
