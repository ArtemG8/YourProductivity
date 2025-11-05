import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import conf
from database import create_db_and_tables
from handlers import private_user_router
from keyboards import set_main_menu
from middlewares import DbSessionMiddleware

# Настройка логирования
logger = logging.getLogger(__name__)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s'
    )

    logger.info("Starting bot...")

    storage = MemoryStorage()

    # Инициализируем бота и диспетчера
    bot = Bot(token=conf.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher(storage=storage)

    # middleware для работы с БД
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    # Роутеры
    dp.include_router(private_user_router)
    # dp.include_router(admin_router) # Если появится роутер для админа
    # dp.include_router(errors_router) # Если появится роутер для ошибок

    # Установка команд меню
    await set_main_menu(bot)

    # Создаем таблицы в БД, если их нет
    logger.info("Creating database tables if not exist...")
    await create_db_and_tables()
    logger.info("Database tables checked/created.")
    
    # # Выполняем миграции
    # logger.info("Running database migrations...")
    # # await run_migrations()
    # logger.info("Database migrations completed.")

    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
