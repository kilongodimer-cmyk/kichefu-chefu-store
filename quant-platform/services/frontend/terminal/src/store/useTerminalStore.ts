import { create } from "zustand";

import type {
  OrderBookSnapshot,
  RiskStats,
  SignalEvent,
  TerminalLog,
  TradeTick,
} from "../types/trading";

const initialRisk: RiskStats = {
  equity: 25_000,
  dailyPnL: -320,
  dailyLimit: -500,
  utilization: 0.38,
};

type RiskUpdater = Partial<RiskStats> | ((current: RiskStats) => RiskStats);

interface TerminalState {
  signals: SignalEvent[];
  risk: RiskStats;
  halted: boolean;
  orderBook: OrderBookSnapshot | null;
  trades: TradeTick[];
  logs: TerminalLog[];
  pushSignal: (signal: SignalEvent) => void;
  updateRisk: (updater: RiskUpdater) => void;
  setHalted: (value: boolean) => void;
  setOrderBook: (snapshot: OrderBookSnapshot) => void;
  pushTrade: (trade: TradeTick) => void;
  pushLog: (log: TerminalLog) => void;
  panicSell: () => void;
  reset: () => void;
}

const clamp = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

export const useTerminalStore = create<TerminalState>((set) => ({
  signals: [],
  risk: initialRisk,
  halted: false,
  orderBook: null,
  trades: [],
  logs: [],
  pushSignal: (signal) =>
    set((state) => {
      if (state.halted) {
        return state;
      }
      return {
        signals: [signal, ...state.signals].slice(0, 25),
      };
    }),
  updateRisk: (updater) =>
    set((state) => {
      if (state.halted) {
        return state;
      }
      const nextRisk =
        typeof updater === "function"
          ? clampRisk(updater(state.risk))
          : clampRisk({ ...state.risk, ...updater });
      return { risk: nextRisk };
    }),
  setHalted: (value) =>
    set((state) => {
      if (state.halted === value) {
        return state;
      }
      return { halted: value };
    }),
  setOrderBook: (snapshot) =>
    set((state) => {
      if (state.halted) {
        return state;
      }
      return { orderBook: snapshot };
    }),
  pushTrade: (trade) =>
    set((state) => {
      if (state.halted) {
        return state;
      }
      return {
        trades: [trade, ...state.trades].slice(0, 50),
      };
    }),
  pushLog: (log) =>
    set((state) => ({
      logs: [log, ...state.logs].slice(0, 40),
    })),
  panicSell: () =>
    set((state) => {
      const panicLog: TerminalLog = {
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        level: "panic",
        message: "PANIC SELL déclenché côté frontend",
      };
      return {
        halted: true,
        signals: [],
        orderBook: null,
        trades: [],
        logs: [panicLog, ...state.logs].slice(0, 40),
        risk: clampRisk({
          ...state.risk,
          utilization: 0,
          dailyPnL: state.risk.dailyPnL - 100,
        }),
      };
    }),
  reset: () =>
    set({ signals: [], risk: initialRisk, halted: false, orderBook: null, trades: [], logs: [] }),
}));

function clampRisk(risk: RiskStats): RiskStats {
  return {
    ...risk,
    dailyPnL: clamp(risk.dailyPnL, risk.dailyLimit * 1.2, risk.equity * 0.05),
    utilization: clamp(risk.utilization, 0, 1),
  };
}
