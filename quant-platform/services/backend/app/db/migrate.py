"""Simple schema management helper for the quant backend."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ..core.config import get_settings
from .base import Base

logger = logging.getLogger(__name__)


def _build_engine() -> AsyncEngine:
    settings = get_settings()
    if settings.postgres_dsn is None:
        raise RuntimeError("POSTGRES_DSN is not configured")
    return create_async_engine(str(settings.postgres_dsn), echo=False, pool_pre_ping=True)


async def run_schema_upgrade() -> None:
    """Apply the latest SQLAlchemy metadata (idempotent)."""

    engine = _build_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    logger.info("Database schema ensured (create_all)")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run_schema_upgrade())


if __name__ == "__main__":
    main()
