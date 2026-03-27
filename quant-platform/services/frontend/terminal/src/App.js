var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
var _a;
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Power } from "lucide-react";
import { ChartPanel } from "./components/ChartPanel";
import { SignalFeed } from "./components/SignalFeed";
import { RiskPanel } from "./components/RiskPanel";
import { ControlBar } from "./components/ControlBar";
import { TradeFeed } from "./components/TradeFeed";
import { TerminalLogPanel } from "./components/TerminalLogPanel";
import { useTerminalStore } from "./store/useTerminalStore";
import { useMarketStream } from "./hooks/useMarketStream";
var DEFAULT_SYMBOL = "BTCUSDT";
var API_BASE = (_a = import.meta.env.VITE_API_BASE) !== null && _a !== void 0 ? _a : "http://localhost:8000";
export function App() {
    var _this = this;
    var signals = useTerminalStore(function (state) { return state.signals; });
    var risk = useTerminalStore(function (state) { return state.risk; });
    var halted = useTerminalStore(function (state) { return state.halted; });
    var orderBook = useTerminalStore(function (state) { return state.orderBook; });
    var trades = useTerminalStore(function (state) { return state.trades; });
    var pushSignal = useTerminalStore(function (state) { return state.pushSignal; });
    var updateRisk = useTerminalStore(function (state) { return state.updateRisk; });
    var setOrderBook = useTerminalStore(function (state) { return state.setOrderBook; });
    var pushTrade = useTerminalStore(function (state) { return state.pushTrade; });
    var localPanic = useTerminalStore(function (state) { return state.panicSell; });
    var setHalted = useTerminalStore(function (state) { return state.setHalted; });
    var pushLog = useTerminalStore(function (state) { return state.pushLog; });
    var logs = useTerminalStore(function (state) { return state.logs; });
    var _a = useState(false), readingMode = _a[0], setReadingMode = _a[1];
    var _b = useState(orderBook), frozenOrderBook = _b[0], setFrozenOrderBook = _b[1];
    var _c = useState(trades), frozenTrades = _c[0], setFrozenTrades = _c[1];
    var _d = useState(signals), frozenSignals = _d[0], setFrozenSignals = _d[1];
    useEffect(function () {
        if (!readingMode) {
            setFrozenOrderBook(orderBook);
        }
    }, [orderBook, readingMode]);
    useEffect(function () {
        if (!readingMode) {
            setFrozenTrades(trades);
        }
    }, [trades, readingMode]);
    useEffect(function () {
        if (!readingMode) {
            setFrozenSignals(signals);
        }
    }, [signals, readingMode]);
    var visibleOrderBook = readingMode ? frozenOrderBook : orderBook;
    var visibleTrades = readingMode ? frozenTrades : trades;
    var visibleSignals = readingMode ? frozenSignals : signals;
    var liveSharpe = useMemo(function () {
        if (trades.length < 5) {
            return null;
        }
        var chronological = __spreadArray([], trades, true).reverse();
        var returns = [];
        for (var i = 1; i < chronological.length; i += 1) {
            var prev = chronological[i - 1];
            var current = chronological[i];
            if (!prev || !current) {
                continue;
            }
            var ret = (current.price - prev.price) / prev.price;
            if (Number.isFinite(ret)) {
                returns.push(ret);
            }
        }
        if (returns.length < 5) {
            return null;
        }
        var mean = returns.reduce(function (sum, value) { return sum + value; }, 0) / returns.length;
        var variance = returns.reduce(function (sum, value) { return sum + (value - mean) * (value - mean); }, 0) / returns.length;
        var std = Math.sqrt(Math.max(variance, 1e-12));
        return std === 0 ? null : Math.sqrt(252) * mean / std;
    }, [trades]);
    useMarketStream({
        symbol: DEFAULT_SYMBOL,
        halted: halted,
        onSignal: function (signal) {
            pushSignal(signal);
            pushLog({
                id: crypto.randomUUID(),
                timestamp: signal.timestamp,
                level: "signal",
                message: "".concat(signal.direction, " ").concat(signal.symbol, " ").concat((signal.confidence * 100).toFixed(0), "%"),
                detail: "".concat(signal.reason, " \u2022 Sharpe ").concat((liveSharpe !== null && liveSharpe !== void 0 ? liveSharpe : 0).toFixed(2)),
            });
        },
        onRiskUpdate: function (next) {
            updateRisk(function () { return next; });
            pushLog({
                id: crypto.randomUUID(),
                timestamp: new Date().toISOString(),
                level: "info",
                message: "Risk refresh \u2022 PnL ".concat(next.dailyPnL.toFixed(0), " USD"),
                detail: "Utilisation ".concat((next.utilization * 100).toFixed(1), "% \u2022 Equity ").concat(next.equity.toFixed(0)),
            });
        },
        onOrderBook: setOrderBook,
        onTrade: pushTrade,
    });
    var postControl = function (endpoint) { return __awaiter(_this, void 0, void 0, function () {
        var response, text;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, fetch("".concat(API_BASE).concat(endpoint), { method: "POST" })];
                case 1:
                    response = _a.sent();
                    if (!!response.ok) return [3 /*break*/, 3];
                    return [4 /*yield*/, response.text()];
                case 2:
                    text = _a.sent();
                    throw new Error(text || "Control action failed");
                case 3: return [2 /*return*/];
            }
        });
    }); };
    var handlePanicSell = function () { return __awaiter(_this, void 0, void 0, function () {
        var error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (halted) {
                        return [2 /*return*/];
                    }
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, postControl("/market/panic-sell")];
                case 2:
                    _a.sent();
                    localPanic();
                    pushLog({
                        id: crypto.randomUUID(),
                        timestamp: new Date().toISOString(),
                        level: "panic",
                        message: "PANIC SELL envoyé au backend",
                        detail: "Sharpe ".concat((liveSharpe !== null && liveSharpe !== void 0 ? liveSharpe : 0).toFixed(2), " \u2022 Trades ").concat(trades.length),
                    });
                    return [3 /*break*/, 4];
                case 3:
                    error_1 = _a.sent();
                    console.error("Unable to trigger panic sell", error_1);
                    pushLog({
                        id: crypto.randomUUID(),
                        timestamp: new Date().toISOString(),
                        level: "warn",
                        message: "Erreur Panic Sell: ".concat(String(error_1)),
                        detail: "Sharpe ".concat((liveSharpe !== null && liveSharpe !== void 0 ? liveSharpe : 0).toFixed(2)),
                    });
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    }); };
    var handleResume = function () { return __awaiter(_this, void 0, void 0, function () {
        var error_2;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!halted) {
                        return [2 /*return*/];
                    }
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, postControl("/market/resume")];
                case 2:
                    _a.sent();
                    setHalted(false);
                    pushLog({
                        id: crypto.randomUUID(),
                        timestamp: new Date().toISOString(),
                        level: "info",
                        message: "Resume trading envoyé",
                        detail: "Sharpe ".concat((liveSharpe !== null && liveSharpe !== void 0 ? liveSharpe : 0).toFixed(2)),
                    });
                    return [3 /*break*/, 4];
                case 3:
                    error_2 = _a.sent();
                    console.error("Unable to resume trading", error_2);
                    pushLog({
                        id: crypto.randomUUID(),
                        timestamp: new Date().toISOString(),
                        level: "warn",
                        message: "Erreur Resume: ".concat(String(error_2)),
                    });
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    }); };
    var showDailyWarning = useMemo(function () { return risk.dailyPnL <= risk.dailyLimit * 0.8; }, [risk.dailyPnL, risk.dailyLimit]);
    return (_jsxs("div", { className: "min-h-screen text-slate-100", children: [_jsxs("header", { className: "border-b border-white/10 px-4 py-4 md:px-8 flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("p", { className: "text-xs uppercase tracking-[0.28em] text-slate-400", children: "Quant Platform" }), _jsx("h1", { className: "title-display text-xl font-extrabold text-white md:text-3xl", children: "Real-Time Trading Terminal" })] }), _jsxs("button", { className: "interactive-lift inline-flex items-center gap-2 rounded-[10px] border border-rose-300/30 bg-rose-500/12 px-4 py-2 text-rose-200 hover:bg-rose-500/18 disabled:opacity-60", onClick: handlePanicSell, disabled: halted, children: [_jsx(Power, { size: 16 }), " Panic Sell"] }), _jsx("button", { type: "button", className: "interactive-lift inline-flex items-center gap-2 rounded-[10px] border px-4 py-2 text-sm ".concat(readingMode
                            ? "border-amber-300/35 bg-amber-500/14 text-amber-100"
                            : "border-white/20 bg-white/8 text-slate-100"), onClick: function () { return setReadingMode(function (current) { return !current; }); }, children: readingMode ? "Reprendre le live" : "Mode lecture (figer)" })] }), _jsxs("main", { className: "grid grid-cols-1 gap-5 p-4 md:gap-6 md:p-8 xl:grid-cols-3", children: [_jsxs("section", { className: "section-enter xl:col-span-2 space-y-5 md:space-y-6", children: [_jsx(ControlBar, { halted: halted, onPanicSell: handlePanicSell, onResume: handleResume }), _jsxs("div", { className: "grid gap-6 lg:grid-cols-2", children: [_jsx(ChartPanel, { orderBook: visibleOrderBook, trades: visibleTrades }), _jsx(TradeFeed, { trades: visibleTrades })] }), _jsx(SignalFeed, { signals: visibleSignals, halted: halted })] }), _jsxs("aside", { className: "section-enter space-y-5 md:space-y-6", children: [_jsx(RiskPanel, { stats: risk, showWarning: showDailyWarning }), _jsx(TerminalLogPanel, { logs: logs }), _jsxs("div", { className: "surface-card interactive-lift p-5", children: [_jsxs("p", { className: "flex items-center gap-2 text-sm font-medium text-slate-300", children: [_jsx(Activity, { size: 16 }), " AI Model"] }), _jsx("p", { className: "title-display mt-3 text-3xl font-bold text-white", children: "RandomForest v0.1" }), _jsx("p", { className: "mt-2 text-sm text-slate-400", children: "Live inference with 150 estimators, retrained 2026-03-15." }), showDailyWarning && (_jsxs("p", { className: "mt-4 flex items-center gap-2 text-sm text-amber-300", children: [_jsx(AlertTriangle, { size: 16 }), "Daily PnL approaching limit."] }))] })] })] })] }));
}
