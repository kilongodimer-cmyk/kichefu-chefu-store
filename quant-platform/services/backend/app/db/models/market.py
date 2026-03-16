from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class OrderBookSnapshot(Base):
    __tablename__ = "order_book_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    bids: Mapped[dict] = mapped_column(JSON)
    asks: Mapped[dict] = mapped_column(JSON)
    best_bid: Mapped[float] = mapped_column(Numeric(18, 8))
    best_ask: Mapped[float] = mapped_column(Numeric(18, 8))
    spread: Mapped[float] = mapped_column(Numeric(18, 8))
    received_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)


class TradeTick(Base):
    __tablename__ = "trade_ticks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    price: Mapped[float] = mapped_column(Numeric(18, 8))
    amount: Mapped[float] = mapped_column(Numeric(18, 8))
    side: Mapped[str] = mapped_column(String(4))
    exchange_timestamp: Mapped[datetime]
    received_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
