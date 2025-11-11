from aiogram import Bot
from aiogram.types import BotCommand
from lexicon import LEXICON_RU

async def set_main_menu(bot: Bot):
    """Устанавливает главное меню для бота."""
    main_menu_commands = [
        BotCommand(command='/start', description=LEXICON_RU['/start'].split('\n')[0]),
        BotCommand(command='/record_flow', description='Записать время потока'),
        BotCommand(command='/record_sprint', description='Записать время спринта'),
        BotCommand(command='/history', description='Посмотреть историю'),
        BotCommand(command='/motivate', description='Мотивация'),
    ]
    await bot.set_my_commands(main_menu_commands)
