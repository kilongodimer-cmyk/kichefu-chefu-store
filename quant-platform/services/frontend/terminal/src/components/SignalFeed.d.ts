import type { SignalEvent } from "../types/trading";
interface SignalFeedProps {
    signals: SignalEvent[];
    halted?: boolean;
}
export declare function SignalFeed({ signals, halted }: SignalFeedProps): import("react/jsx-runtime").JSX.Element;
export {};
