from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from lexicon import LEXICON_RU

def create_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру с кнопкой 'Отмена'"""
    cancel_button = KeyboardButton(text=LEXICON_RU['cancel_button'])
    keyboard = ReplyKeyboardMarkup(keyboard=[[cancel_button]], resize_keyboard=True, one_time_keyboard=True)
    return keyboard

def create_history_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру с кнопкой 'История'"""
    history_button = KeyboardButton(text=LEXICON_RU['history_button'])
    keyboard = ReplyKeyboardMarkup(keyboard=[[history_button]], resize_keyboard=True, one_time_keyboard=True)
    return keyboard