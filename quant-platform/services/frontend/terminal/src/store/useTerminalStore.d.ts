import type { OrderBookSnapshot, RiskStats, SignalEvent, TerminalLog, TradeTick } from "../types/trading";
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
export declare const useTerminalStore: import("zustand").UseBoundStore<import("zustand").StoreApi<TerminalState>>;
export {};
