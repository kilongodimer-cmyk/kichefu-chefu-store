interface ControlBarProps {
    halted: boolean;
    onPanicSell: () => void;
    onResume: () => void;
}
export declare function ControlBar({ halted, onPanicSell, onResume }: ControlBarProps): import("react/jsx-runtime").JSX.Element;
export {};
