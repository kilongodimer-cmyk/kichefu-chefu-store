from __future__ import annotations

import json
from typing import Any

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from ...cache.redis import redis_client
from ...services.market_data.store import MarketDataStore
from ...notifications import send_telegram_alert

router = APIRouter(prefix="/market", tags=["market"])


def get_market_store() -> MarketDataStore:
    return MarketDataStore()


@router.get("/orderbook/latest")
async def latest_order_book(
    symbol: str = Query(..., description="Trading symbol, e.g. BTC/USDT"),
    store: MarketDataStore = Depends(get_market_store),
) -> dict[str, Any]:
    snapshot = await store.latest_order_book_for_symbol(symbol)
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"No order book found for {symbol}")

    return {
        "symbol": snapshot.symbol,
        "bids": snapshot.bids,
        "asks": snapshot.asks,
        "bestBid": float(snapshot.best_bid),
        "bestAsk": float(snapshot.best_ask),
        "spread": float(snapshot.spread),
        "receivedAt": snapshot.received_at.isoformat(),
    }


@router.websocket("/ws/{symbol}")
async def market_ws(websocket: WebSocket, symbol: str) -> None:
    await websocket.accept()
    pubsub = await redis_client.subscribe(["md:book:latest", "md:trades:latest"])
    requested_symbol = _normalize_symbol(symbol)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None:
                continue

            channel_raw = message.get("channel")
            channel = channel_raw.decode() if isinstance(channel_raw, (bytes, bytearray)) else str(channel_raw)
            payload_raw = message.get("data")
            try:
                payload = json.loads(payload_raw)
            except (TypeError, json.JSONDecodeError):
                continue

            payload_symbol = payload.get("symbol")
            if payload_symbol is None and "trades" in payload:
                trades = payload.get("trades", [])
                if trades:
                    payload_symbol = trades[0].get("symbol")

            if payload_symbol:
                normalized_payload_symbol = _normalize_symbol(payload_symbol)
            else:
                normalized_payload_symbol = None

            if (
                normalized_payload_symbol
                and requested_symbol != "all"
                and normalized_payload_symbol != requested_symbol
            ):
                continue

            event_type = "order_book" if "book" in channel else "trades"
            await websocket.send_json({"type": event_type, "data": payload})
    except WebSocketDisconnect:
        await pubsub.unsubscribe()
    finally:
        await pubsub.close()


def _normalize_symbol(value: str) -> str:
    return value.replace("/", "").lower()


@router.post("/panic-sell", status_code=202, summary="Trigger emergency stop across strategies")
async def panic_sell() -> dict[str, str]:
    payload = {"type": "panic", "timestamp": datetime.utcnow().isoformat()}
    await redis_client.publish_json("control:panic", payload)
    await send_telegram_alert("⚠️ *Panic Sell* déclenché – arrêt d'urgence des stratégies")
    return {"status": "panic_signal_sent"}


@router.post("/resume", status_code=202, summary="Resume trading after a panic sell")
async def resume_trading() -> dict[str, str]:
    payload = {"type": "resume", "timestamp": datetime.utcnow().isoformat()}
    await redis_client.publish_json("control:panic", payload)
    await send_telegram_alert("✅ Reprise des stratégies après Panic Sell")
    return {"status": "resume_signal_sent"}
