import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { ArrowDownRight, ArrowUpRight, Pause, Radio } from "lucide-react";
export function TradeFeed(_a) {
    var trades = _a.trades;
    var _b = useState(false), freezeFeed = _b[0], setFreezeFeed = _b[1];
    var _c = useState([]), snapshot = _c[0], setSnapshot = _c[1];
    useEffect(function () {
        if (!freezeFeed) {
            setSnapshot(trades.slice(0, 12));
        }
    }, [trades, freezeFeed]);
    var latest = freezeFeed ? snapshot : trades.slice(0, 12);
    var sideSummary = useMemo(function () {
        return latest.reduce(function (acc, trade) {
            var isBuy = trade.side.toUpperCase() === "BUY" || trade.side.toUpperCase() === "BID";
            if (isBuy) {
                acc.buy += 1;
            }
            else {
                acc.sell += 1;
            }
            return acc;
        }, { buy: 0, sell: 0 });
    }, [latest]);
    return (_jsxs("div", { className: "surface-card interactive-lift p-4 md:p-5", children: [_jsxs("header", { className: "mb-4 flex flex-wrap items-center justify-between gap-2 text-sm text-slate-300", children: [_jsxs("span", { className: "flex items-center gap-2", children: [_jsx(Radio, { size: 16 }), " Live Tape"] }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsxs("span", { className: "rounded-[8px] bg-emerald-500/12 px-2 py-1 text-[11px] font-semibold text-emerald-300", children: ["BUY ", sideSummary.buy] }), _jsxs("span", { className: "rounded-[8px] bg-rose-500/12 px-2 py-1 text-[11px] font-semibold text-rose-300", children: ["SELL ", sideSummary.sell] }), _jsxs("button", { type: "button", className: "inline-flex items-center gap-1 rounded-[8px] border border-white/15 px-2 py-1 text-[11px] text-slate-300 hover:bg-white/8", onClick: function () { return setFreezeFeed(function (current) { return !current; }); }, children: [_jsx(Pause, { size: 12 }), " ", freezeFeed ? "Reprendre" : "Pause flux"] })] })] }), _jsxs("div", { className: "max-h-[360px] space-y-2 overflow-y-auto pr-1 text-xs text-slate-300", children: [latest.length === 0 && _jsx("p", { className: "text-center text-slate-500", children: "Flux en attente\u2026" }), latest.map(function (trade) {
                        var sideLong = trade.side.toUpperCase() === "BUY" || trade.side.toUpperCase() === "BID";
                        var SideIcon = sideLong ? ArrowUpRight : ArrowDownRight;
                        var color = sideLong ? "text-emerald-300" : "text-rose-300";
                        return (_jsxs("article", { className: "flex items-center justify-between rounded-[10px] border border-white/10 bg-white/7 px-3 py-2", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx(SideIcon, { size: 16, className: color }), _jsxs("div", { children: [_jsx("p", { className: "text-sm font-semibold text-white", children: trade.price.toFixed(2) }), _jsx("p", { className: "text-[11px] text-slate-500", children: trade.symbol })] })] }), _jsxs("div", { className: "text-right", children: [_jsx("p", { className: "inline-block rounded-[8px] px-2 py-0.5 text-[10px] font-bold tracking-[0.14em] ".concat(sideLong ? "bg-emerald-500/12 text-emerald-200" : "bg-rose-500/12 text-rose-200"), children: sideLong ? "BUY" : "SELL" }), _jsx("p", { className: "text-sm font-medium ".concat(color), children: trade.amount.toFixed(4) }), _jsx("time", { className: "text-[11px] text-slate-500", dateTime: trade.receivedAt, children: new Date(trade.receivedAt).toLocaleTimeString([], { minute: "2-digit", second: "2-digit" }) })] })] }, "".concat(trade.symbol, "-").concat(trade.receivedAt, "-").concat(trade.price, "-").concat(trade.amount)));
                    })] })] }));
}
