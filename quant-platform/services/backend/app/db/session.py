from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import get_settings


def _build_engine():
    settings = get_settings()
    if settings.postgres_dsn is None:
        raise RuntimeError("POSTGRES_DSN is not configured")

    return create_async_engine(str(settings.postgres_dsn), echo=False, pool_pre_ping=True)


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    engine = _build_engine()
    return async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session
