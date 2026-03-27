import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Activity, Bell, TriangleAlert } from "lucide-react";
var levelStyles = {
    info: "text-slate-300",
    signal: "text-emerald-300",
    warn: "text-amber-300",
    panic: "text-rose-400",
};
var levelIcon = {
    info: _jsx(Activity, { size: 14 }),
    signal: _jsx(Bell, { size: 14 }),
    warn: _jsx(TriangleAlert, { size: 14 }),
    panic: _jsx(TriangleAlert, { size: 14 }),
};
export function TerminalLogPanel(_a) {
    var logs = _a.logs;
    return (_jsxs("div", { className: "surface-card interactive-lift p-4 md:p-5", children: [_jsxs("header", { className: "mb-4 flex items-center justify-between text-sm text-slate-300", children: [_jsxs("span", { className: "flex items-center gap-2", children: [_jsx(Activity, { size: 16 }), " Journal IA"] }), _jsxs("span", { className: "text-xs text-slate-500", children: [logs.length, " events"] })] }), _jsxs("div", { className: "space-y-2 text-xs text-slate-300", children: [logs.length === 0 && _jsx("p", { className: "text-center text-slate-500", children: "En attente d'activit\u00E9\u2026" }), logs.map(function (log) { return (_jsxs("article", { className: "interactive-lift flex items-center justify-between rounded-[10px] border border-white/10 bg-white/7 px-3 py-2", children: [_jsxs("div", { className: "flex items-center gap-2 ".concat(levelStyles[log.level]), children: [levelIcon[log.level], _jsx("p", { className: "text-sm font-medium", children: log.message })] }), _jsx("time", { className: "text-[11px] text-slate-500", dateTime: log.timestamp, children: new Date(log.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) })] }, log.id)); })] })] }));
}
