import type { OrderBookSnapshot, TradeTick } from "../types/trading";
interface ChartPanelProps {
    orderBook: OrderBookSnapshot | null;
    trades: TradeTick[];
}
export declare function ChartPanel({ orderBook, trades }: ChartPanelProps): import("react/jsx-runtime").JSX.Element;
export {};
