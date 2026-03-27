import type { OrderBookSnapshot, RiskStats, SignalEvent, TradeTick } from "../types/trading";
interface UseMarketStreamOptions {
    symbol: string;
    halted: boolean;
    onOrderBook?: (snapshot: OrderBookSnapshot) => void;
    onTrade?: (trade: TradeTick) => void;
    onSignal?: (signal: SignalEvent) => void;
    onRiskUpdate?: (stats: RiskStats) => void;
}
export declare function useMarketStream({ symbol, halted, onOrderBook, onTrade, onSignal, onRiskUpdate, }: UseMarketStreamOptions): void;
export {};
