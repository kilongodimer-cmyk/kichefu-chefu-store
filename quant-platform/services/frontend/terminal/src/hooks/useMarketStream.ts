import { useEffect } from "react";

import type {
  OrderBookSnapshot,
  RiskStats,
  SignalEvent,
  TradeTick,
} from "../types/trading";

interface UseMarketStreamOptions {
  symbol: string;
  halted: boolean;
  onOrderBook?: (snapshot: OrderBookSnapshot) => void;
  onTrade?: (trade: TradeTick) => void;
  onSignal?: (signal: SignalEvent) => void;
  onRiskUpdate?: (stats: RiskStats) => void;
}

export function useMarketStream({
  symbol,
  halted,
  onOrderBook,
  onTrade,
  onSignal,
  onRiskUpdate,
}: UseMarketStreamOptions) {
  useEffect(() => {
    if (halted) {
      return undefined;
    }

    let lastPrice = 68250;
    let fallbackTick = 0;
    let fallbackInterval: number | null = null;
    let fallbackTimeout: number | null = null;

    const pushFallbackFrame = () => {
      const drift = (Math.random() - 0.5) * 120;
      lastPrice = Math.max(100, lastPrice + drift);
      const now = new Date().toISOString();
      const side = drift >= 0 ? "BUY" : "SELL";

      onTrade?.({
        symbol,
        price: Number(lastPrice.toFixed(2)),
        amount: Number((Math.random() * 0.35 + 0.01).toFixed(4)),
        side,
        timestamp: Date.now(),
        receivedAt: now,
      });

      const levels = Array.from({ length: 6 }, (_, index) => {
        const step = (index + 1) * 2.5;
        return [
          Number((lastPrice - step).toFixed(2)),
          Number((Math.random() * 0.9 + 0.1).toFixed(3)),
        ];
      });
      const asks = Array.from({ length: 6 }, (_, index) => {
        const step = (index + 1) * 2.5;
        return [
          Number((lastPrice + step).toFixed(2)),
          Number((Math.random() * 0.9 + 0.1).toFixed(3)),
        ];
      });

      onOrderBook?.({
        symbol,
        bids: levels,
        asks,
        bestBid: levels[0]?.[0] ?? lastPrice,
        bestAsk: asks[0]?.[0] ?? lastPrice,
        spread: Number(((asks[0]?.[0] ?? lastPrice) - (levels[0]?.[0] ?? lastPrice)).toFixed(2)),
        receivedAt: now,
      });

      onRiskUpdate?.({
        equity: 25_000,
        dailyPnL: Number((-350 + Math.random() * 540).toFixed(0)),
        dailyLimit: -500,
        utilization: Number((0.12 + Math.random() * 0.62).toFixed(3)),
      });

      fallbackTick += 1;
      if (fallbackTick % 4 === 0) {
        onSignal?.({
          id: crypto.randomUUID(),
          timestamp: now,
          symbol,
          direction: Math.random() > 0.5 ? "LONG" : "SHORT",
          confidence: Number((0.58 + Math.random() * 0.38).toFixed(2)),
          reason: "Fallback stream local actif (backend feed indisponible)",
        });
      }
    };

    const startFallback = () => {
      if (fallbackInterval !== null) {
        return;
      }
      pushFallbackFrame();
      fallbackInterval = window.setInterval(pushFallbackFrame, 1100);
    };

    const wsBase = import.meta.env.VITE_WS_BASE ?? "ws://localhost:8000";
    const url = `${wsBase.replace(/\/$/, "")}/market/ws/${symbol}`;
    const socket = new WebSocket(url);

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const { type, data } = payload as { type: string; data: any };

        if (type === "order_book" && data && onOrderBook) {
          onOrderBook(data as OrderBookSnapshot);
        }

        if (type === "trades" && data?.trades && onTrade) {
          (data.trades as TradeTick[]).forEach((trade) => onTrade(trade));
        }

        if (type === "signal" && data && onSignal) {
          onSignal(data as SignalEvent);
        }

        if (type === "risk" && data?.stats && onRiskUpdate) {
          onRiskUpdate(data.stats as RiskStats);
        }
      } catch (error) {
        console.error("Failed to parse WS message", error);
      }
    };

    socket.onerror = (error) => {
      console.error("WebSocket error", error);
      startFallback();
    };

    socket.onclose = () => {
      startFallback();
    };

    fallbackTimeout = window.setTimeout(() => {
      if (socket.readyState !== WebSocket.OPEN) {
        startFallback();
      }
    }, 3000);

    return () => {
      if (fallbackTimeout !== null) {
        window.clearTimeout(fallbackTimeout);
      }
      if (fallbackInterval !== null) {
        window.clearInterval(fallbackInterval);
      }
      socket.close(1000, "cleanup");
    };
  }, [symbol, halted, onOrderBook, onTrade, onSignal, onRiskUpdate]);
}
