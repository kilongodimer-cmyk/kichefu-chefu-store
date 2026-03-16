"""Entrypoint for running the Binance market data stream as a standalone worker."""

import asyncio
import logging

from ..notifications import send_telegram_alert
from ..services.market_data.binance_stream import start_market_stream

logger = logging.getLogger(__name__)


async def _run_worker() -> None:
    await send_telegram_alert("🚀 L'ouvrier market data démarre")
    try:
        await start_market_stream()
    except Exception as exc:
        logger.exception("Market data worker crashed: %s", exc)
        await send_telegram_alert("🔥 Market data worker crash: %s" % exc)
        raise
    else:
        await send_telegram_alert("✅ Market data worker arrêté proprement")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("Starting market data worker")
    asyncio.run(_run_worker())


if __name__ == "__main__":
    main()
