import asyncio
import logging
from datetime import datetime
from typing import Any

from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

try:
    from ccxtpro import binance as ccxt_binance  # type: ignore
except ImportError:  # pragma: no cover
    ccxt_binance = None

from ...core.config import get_settings
from ...cache.redis import redis_client
from ...notifications import send_telegram_alert
from .store import MarketDataStore

logger = logging.getLogger(__name__)


class BinanceMarketStream:
    def __init__(self) -> None:
        if ccxt_binance is None:
            raise RuntimeError("ccxtpro is not installed")

        settings = get_settings()
        self.symbol = settings.trading_symbol
        self._client = ccxt_binance({
            "enableRateLimit": True,
            "options": {
                "defaultType": "future",
            },
        })
        self._store = MarketDataStore()

    async def connect(self) -> None:
        await self._client.load_markets()
        logger.info("Binance markets loaded")

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(5))
    async def watch_order_book(self) -> Any:
        return await self._client.watch_order_book(self.symbol)

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(5))
    async def watch_trades(self) -> Any:
        return await self._client.watch_trades(self.symbol)

    async def run(self) -> None:
        await self.connect()
        await asyncio.gather(
            self._consume_order_book(),
            self._consume_trades(),
        )

    async def _consume_order_book(self) -> None:
        while True:
            try:
                book = await self.watch_order_book()
                bids = book.get("bids", [])[:20]
                asks = book.get("asks", [])[:20]
                best_bid = bids[0][0] if bids else 0
                best_ask = asks[0][0] if asks else 0
                spread = best_ask - best_bid if best_bid and best_ask else 0
                payload = {
                    "symbol": self.symbol,
                    "bids": bids,
                    "asks": asks,
                    "bestBid": best_bid,
                    "bestAsk": best_ask,
                    "spread": spread,
                    "receivedAt": datetime.utcnow().isoformat(),
                }

                await redis_client.push_stream(f"md:book:{self.symbol}", payload)
                await redis_client.publish_json("md:book:latest", payload)
                await self._store.save_order_book(
                    symbol=self.symbol,
                    bids=bids,
                    asks=asks,
                    best_bid=best_bid,
                    best_ask=best_ask,
                    spread=spread,
                    received_at=datetime.utcnow(),
                )
            except RetryError as exc:
                logger.warning("Retry exceeded for order book stream: %s", exc)
                await send_telegram_alert("⚠️ Flux carnet Binance en échec – tentative de reconnexion")
                await asyncio.sleep(5)
            except Exception as exc:  # pragma: no cover
                logger.exception("Unexpected error in order book stream: %s", exc)
                await send_telegram_alert("❌ Erreur inattendue sur le flux carnet Binance")
                await asyncio.sleep(2)

    async def _consume_trades(self) -> None:
        while True:
            try:
                trades = await self.watch_trades()
                formatted = [
                    {
                        "symbol": self.symbol,
                        "price": trade.get("price"),
                        "amount": trade.get("amount"),
                        "side": trade.get("side"),
                        "timestamp": trade.get("timestamp"),
                        "receivedAt": datetime.utcnow().isoformat(),
                    }
                    for trade in trades
                ]
                if not formatted:
                    continue

                await redis_client.push_stream(f"md:trades:{self.symbol}", {"trades": formatted})
                await redis_client.publish_json("md:trades:latest", {"trades": formatted})
                await self._store.save_trades(symbol=self.symbol, trades=trades)
            except RetryError as exc:
                logger.warning("Retry exceeded for trades stream: %s", exc)
                await send_telegram_alert("⚠️ Flux trades Binance en échec – tentative de reconnexion")
                await asyncio.sleep(5)
            except Exception as exc:  # pragma: no cover
                logger.exception("Unexpected error in trades stream: %s", exc)
                await send_telegram_alert("❌ Erreur inattendue sur le flux trades Binance")
                await asyncio.sleep(2)


async def start_market_stream() -> None:
    stream = BinanceMarketStream()
    await stream.run()
