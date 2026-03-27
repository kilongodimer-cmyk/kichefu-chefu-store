import type { RiskStats } from "../types/trading";
interface RiskPanelProps {
    stats: RiskStats;
    showWarning?: boolean;
}
export declare function RiskPanel({ stats, showWarning }: RiskPanelProps): import("react/jsx-runtime").JSX.Element;
export {};
