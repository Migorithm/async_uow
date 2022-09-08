from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .adapters.in_memory_orm import metadata, start_mappers

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=True,
    execution_options={"isolation_level": "AUTOCOMMIT"},
)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def in_memory_db():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    start_mappers()


async def session_factory():
    try:
        session = async_session()
        yield session
    except Exception:
        session.rollback()
    finally:
        await session.close()
