from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ...db.models import OrderBookSnapshot, TradeTick
from ...db.session import get_sessionmaker


class MarketDataStore:
    """Persists market data snapshots and trades into PostgreSQL."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or get_sessionmaker()

    async def save_order_book(
        self,
        *,
        symbol: str,
        bids: list[list[float]],
        asks: list[list[float]],
        best_bid: float,
        best_ask: float,
        spread: float,
        received_at: datetime,
    ) -> None:
        snapshot = OrderBookSnapshot(
            symbol=symbol,
            bids={"levels": bids},
            asks={"levels": asks},
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread,
            received_at=received_at,
        )

        async with self._session_factory() as session:
            session.add(snapshot)
            await session.commit()

    async def save_trades(
        self,
        *,
        symbol: str,
        trades: Iterable[dict],
    ) -> None:
        trade_rows = [
            TradeTick(
                symbol=symbol,
                price=trade.get("price"),
                amount=trade.get("amount"),
                side=trade.get("side", "buy").upper(),
                exchange_timestamp=datetime.fromtimestamp(
                    (trade.get("timestamp") or trade.get("datetime") or datetime.utcnow().timestamp()) / 1000
                )
                if trade.get("timestamp")
                else datetime.utcnow(),
            )
            for trade in trades
        ]
        if not trade_rows:
            return

        async with self._session_factory() as session:
            session.add_all(trade_rows)
            await session.commit()

    async def latest_order_book_for_symbol(self, symbol: str) -> OrderBookSnapshot | None:
        async with self._session_factory() as session:
            stmt = (
                select(OrderBookSnapshot)
                .where(OrderBookSnapshot.symbol == symbol)
                .order_by(OrderBookSnapshot.received_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
