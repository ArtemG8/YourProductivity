from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from config import conf

# Асинхронный движок SQLAlchemy
DATABASE_URL = (
    f"postgresql+asyncpg://{conf.DB_USER}:{conf.DB_PASS}@"
    f"{conf.DB_HOST}:{conf.DB_PORT}/{conf.DB_NAME}"
)

engine = create_async_engine(DATABASE_URL, echo=False)

#фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_async_session() -> AsyncSession:
    """Зависимость для получения асинхронной сессии базы данных"""
    async with AsyncSessionLocal() as session:
        yield session

async def create_db_and_tables():
    """Создает таблицы в базе данных"""
    from database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)