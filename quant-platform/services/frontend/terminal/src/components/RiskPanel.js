import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { ShieldAlert, TrendingDown, TrendingUp } from "lucide-react";
export function RiskPanel(_a) {
    var stats = _a.stats, _b = _a.showWarning, showWarning = _b === void 0 ? false : _b;
    var equityPct = (stats.dailyPnL / stats.equity) * 100;
    var limitPct = (stats.dailyLimit / stats.equity) * 100;
    return (_jsxs("div", { className: "surface-card interactive-lift p-5", children: [_jsxs("header", { className: "flex items-center justify-between text-sm text-slate-300", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx(ShieldAlert, { size: 16 }), " Gestion du risque"] }), _jsx("span", { className: "text-xs uppercase tracking-[0.3em] text-slate-500", children: "2% Max" })] }), _jsxs("div", { className: "mt-4 space-y-3", children: [_jsx(StatRow, { label: "Capital", value: formatCurrency(stats.equity), accent: "text-slate-100" }), _jsx(StatRow, { label: "PnL journalier", value: formatCurrency(stats.dailyPnL), accent: stats.dailyPnL >= 0 ? "text-emerald-300" : "text-rose-300", icon: stats.dailyPnL >= 0 ? _jsx(TrendingUp, { size: 16 }) : _jsx(TrendingDown, { size: 16 }) }), _jsx(StatRow, { label: "Limite journali\u00E8re", value: formatCurrency(stats.dailyLimit), accent: "text-amber-300" })] }), _jsxs("div", { className: "mt-5", children: [_jsx("p", { className: "text-xs uppercase tracking-[0.3em] text-slate-500", children: "Utilisation" }), _jsx("div", { className: "mt-2 h-2 overflow-hidden rounded-[10px] bg-white/10", children: _jsx("div", { className: "h-full rounded-[10px] bg-gradient-to-r from-sky-400/90 to-cyan-300/90 transition-all duration-300 ease-in-out", style: { width: "".concat(Math.min(stats.utilization * 100, 100), "%") } }) }), _jsxs("div", { className: "mt-2 flex justify-between text-xs text-slate-400", children: [_jsxs("span", { children: [(stats.utilization * 100).toFixed(1), "%"] }), _jsx("span", { children: "2% par trade" })] })] }), _jsxs("div", { className: "mt-5 space-y-2 text-xs text-slate-400", children: [_jsxs("p", { children: ["PnL vs capital : ", equityPct.toFixed(2), "% \u2022 Limite : ", limitPct.toFixed(2), "%"] }), showWarning && (_jsx("p", { className: "rounded-[10px] bg-amber-500/12 px-3 py-2 text-amber-200", children: "Attention : le bot se rapproche de la limite journali\u00E8re." }))] })] }));
}
function StatRow(_a) {
    var label = _a.label, value = _a.value, accent = _a.accent, icon = _a.icon;
    return (_jsxs("div", { className: "interactive-lift flex items-center justify-between rounded-[10px] px-2 py-1 text-sm text-slate-400", children: [_jsx("span", { children: label }), _jsxs("span", { className: "flex items-center gap-2 font-semibold ".concat(accent), children: [icon, value] })] }));
}
function formatCurrency(amount) {
    return new Intl.NumberFormat("fr-FR", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
    }).format(amount);
}
