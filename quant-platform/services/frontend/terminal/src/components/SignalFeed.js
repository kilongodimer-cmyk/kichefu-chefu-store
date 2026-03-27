import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Activity, Zap } from "lucide-react";
export function SignalFeed(_a) {
    var signals = _a.signals, _b = _a.halted, halted = _b === void 0 ? false : _b;
    var latestSignal = signals[0];
    var isBuySignal = function (direction) {
        var normalized = direction.toUpperCase();
        return normalized.includes("BUY") || normalized.includes("LONG");
    };
    return (_jsxs("div", { className: "surface-card interactive-lift p-4 md:p-5", children: [_jsxs("header", { className: "mb-4 flex items-center justify-between", children: [_jsxs("div", { className: "flex items-center gap-2 text-sm text-slate-300", children: [_jsx(Zap, { size: 16 }), " Live Signals"] }), _jsx("span", { className: "inline-flex items-center gap-2 rounded-[10px] px-3 py-1 text-xs font-medium tracking-[0.2em] ".concat(halted
                            ? "bg-amber-500/18 text-amber-200"
                            : "bg-emerald-500/12 text-emerald-200"), children: halted ? "PAUSE" : "LIVE" })] }), latestSignal && (_jsxs("article", { className: "mb-4 rounded-[12px] border px-4 py-3 ".concat(isBuySignal(latestSignal.direction)
                    ? "border-emerald-400/35 bg-emerald-500/10"
                    : "border-rose-400/35 bg-rose-500/10"), children: [_jsx("p", { className: "text-[11px] uppercase tracking-[0.14em] text-slate-300", children: "Dernier signal" }), _jsxs("div", { className: "mt-2 flex items-center justify-between gap-2", children: [_jsx("p", { className: "text-xl font-extrabold text-white", children: latestSignal.direction }), _jsx("span", { className: "rounded-[8px] px-2 py-1 text-[11px] font-bold tracking-[0.12em] ".concat(isBuySignal(latestSignal.direction)
                                    ? "bg-emerald-500/15 text-emerald-100"
                                    : "bg-rose-500/15 text-rose-100"), children: isBuySignal(latestSignal.direction) ? "BUY" : "SELL" })] }), _jsxs("p", { className: "mt-1 text-sm text-slate-200", children: ["Confiance ", (latestSignal.confidence * 100).toFixed(0), "%"] })] })), _jsxs("div", { className: "max-h-[360px] space-y-3 overflow-y-auto pr-1", children: [signals.map(function (signal) { return (_jsxs("article", { className: "rounded-[10px] border border-white/12 bg-slate-900/45 p-3", children: [_jsxs("div", { className: "flex items-center justify-between text-xs text-slate-400", children: [_jsx("p", { children: signal.symbol }), _jsx("time", { dateTime: signal.timestamp, children: new Date(signal.timestamp).toLocaleTimeString([], {
                                            hour: "2-digit",
                                            minute: "2-digit",
                                            second: "2-digit",
                                        }) })] }), _jsxs("div", { className: "mt-1 flex items-center justify-between", children: [_jsxs("p", { className: "text-lg font-semibold", children: [signal.direction, _jsxs("span", { className: "ml-2 text-sm text-slate-400", children: [(signal.confidence * 100).toFixed(0), "%"] })] }), _jsxs("div", { className: "inline-flex items-center gap-1 rounded-[10px] px-3 py-1 text-xs ".concat(isBuySignal(signal.direction)
                                            ? "bg-emerald-500/12 text-emerald-300"
                                            : "bg-rose-500/12 text-rose-300"), children: [_jsx(Activity, { size: 12 }), " ", isBuySignal(signal.direction) ? "BUY" : "SELL"] })] }), _jsx("p", { className: "mt-2 text-sm text-slate-400", children: signal.reason })] }, signal.id)); }), signals.length === 0 && (_jsx("p", { className: "text-center text-sm text-slate-500", children: halted ? "Bot en pause" : "Aucun signal pour le moment." }))] })] }));
}
