import random
from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from lexicon import LEXICON_RU, MOTIVATIONAL_MESSAGES
from database import get_or_create_user, add_flow_record, add_sprint_record, get_user_productivity_history
from keyboards import create_cancel_keyboard
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
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    if user.created_at == user.created_at: # Простая проверка на нового/вернувшегося пользователя
        await message.answer(LEXICON_RU['/start'])
    else:
        await message.answer(LEXICON_RU['welcome_back'])

# Обработчик команды /help
@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(LEXICON_RU['/help'])

# Обработчик команды /record_flow
@router.message(Command(commands='record_flow'), StateFilter(None))
async def process_record_flow_command(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['/record_flow'], reply_markup=create_cancel_keyboard())
    await state.set_state(RecordStates.waiting_for_flow_duration)

# Обработчик длительности потока
@router.message(StateFilter(RecordStates.waiting_for_flow_duration))
async def process_flow_duration(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == LEXICON_RU['cancel_button']:
        await state.clear()
        await message.answer(LEXICON_RU['cancel_action'], reply_markup=ReplyKeyboardRemove())
        return

    try:
        duration = int(message.text)
        if duration <= 0:
            await message.answer(LEXICON_RU['invalid_flow_duration'])
            return
        await add_flow_record(session, user_id=message.from_user.id, duration_minutes=duration)
        await message.answer(LEXICON_RU['flow_recorded'].format(duration=duration), reply_markup=ReplyKeyboardRemove())
        await state.clear()
    except ValueError:
        await message.answer(LEXICON_RU['invalid_flow_duration'])

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
        await add_sprint_record(session, user_id=message.from_user.id, duration_minutes=duration)
        await message.answer(LEXICON_RU['sprint_recorded'].format(duration=duration), reply_markup=ReplyKeyboardRemove())
        await state.clear()
    except ValueError:
        await message.answer(LEXICON_RU['invalid_sprint_duration'])

# Обработчик команды /history
@router.message(Command(commands='history'))
async def process_history_command(message: Message, session: AsyncSession):
    flow_records, sprint_records = await get_user_productivity_history(session, user_id=message.from_user.id)

    if not flow_records and not sprint_records:
        await message.answer(LEXICON_RU['no_history'])
        return

    history_text = LEXICON_RU['/history']
    all_records = sorted(
        list(flow_records) + list(sprint_records),
        key=lambda x: x.recorded_at,
        reverse=True
    )

    for record in all_records:
        date_str = record.recorded_at.strftime('%Y-%m-%d %H:%M')
        if isinstance(record, type(flow_records[0]) if flow_records else object):
            history_text += LEXICON_RU['flow_entry'].format(duration=record.duration_minutes, date=date_str)
        elif isinstance(record, type(sprint_records[0]) if sprint_records else object):
            history_text += LEXICON_RU['sprint_entry'].format(duration=record.duration_minutes, date=date_str)

    await message.answer(history_text)

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
