export type SignalDirection = "LONG" | "SHORT";
export interface SignalEvent {
    id: string;
    timestamp: string;
    symbol: string;
    direction: SignalDirection;
    confidence: number;
    reason: string;
}
export interface RiskStats {
    equity: number;
    dailyPnL: number;
    dailyLimit: number;
    utilization: number;
}
export interface OrderBookSnapshot {
    symbol: string;
    bids: number[][];
    asks: number[][];
    bestBid: number;
    bestAsk: number;
    spread: number;
    receivedAt: string;
}
export interface TradeTick {
    symbol: string;
    price: number;
    amount: number;
    side: string;
    timestamp?: number;
    receivedAt: string;
}
export interface TerminalLog {
    id: string;
    timestamp: string;
    level: "info" | "signal" | "warn" | "panic";
    message: string;
    detail?: string;
}
