from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lexicon.lexicon_ru import LEXICON_RU

def create_flow_active_kb() -> InlineKeyboardMarkup:
    """Создает клавиатуру для активного таймера потока (Приостановить/Завершить)."""
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['btn_pause_flow'], callback_data='flow_pause'),
        InlineKeyboardButton(text=LEXICON_RU['btn_finish_flow'], callback_data='flow_finish'),
    )
    return kb_builder.as_markup()

def create_flow_paused_kb() -> InlineKeyboardMarkup:
    """Создает клавиатуру для приостановленного таймера потока (Продолжить/Завершить)."""
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['btn_resume_flow'], callback_data='flow_resume'),
        InlineKeyboardButton(text=LEXICON_RU['btn_finish_flow'], callback_data='flow_finish'),
    )
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['btn_cancel_flow'], callback_data='flow_cancel'),
    )
    return kb_builder.as_markup()

def create_history_inline_kb() -> InlineKeyboardMarkup:
    """Создает inline-клавиатуру с кнопкой 'История'"""
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['history_button'], callback_data='show_history'),
    )
    return kb_builder.as_markup()