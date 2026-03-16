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
    };

    return () => {
      socket.close(1000, "cleanup");
    };
  }, [symbol, halted, onOrderBook, onTrade, onSignal, onRiskUpdate]);
}
