var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
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
import { create } from "zustand";
var initialRisk = {
    equity: 25000,
    dailyPnL: -320,
    dailyLimit: -500,
    utilization: 0.38,
};
var clamp = function (value, min, max) {
    return Math.min(Math.max(value, min), max);
};
export var useTerminalStore = create(function (set) { return ({
    signals: [],
    risk: initialRisk,
    halted: false,
    orderBook: null,
    trades: [],
    logs: [],
    pushSignal: function (signal) {
        return set(function (state) {
            if (state.halted) {
                return state;
            }
            return {
                signals: __spreadArray([signal], state.signals, true).slice(0, 25),
            };
        });
    },
    updateRisk: function (updater) {
        return set(function (state) {
            if (state.halted) {
                return state;
            }
            var nextRisk = typeof updater === "function"
                ? clampRisk(updater(state.risk))
                : clampRisk(__assign(__assign({}, state.risk), updater));
            return { risk: nextRisk };
        });
    },
    setHalted: function (value) {
        return set(function (state) {
            if (state.halted === value) {
                return state;
            }
            return { halted: value };
        });
    },
    setOrderBook: function (snapshot) {
        return set(function (state) {
            if (state.halted) {
                return state;
            }
            return { orderBook: snapshot };
        });
    },
    pushTrade: function (trade) {
        return set(function (state) {
            if (state.halted) {
                return state;
            }
            return {
                trades: __spreadArray([trade], state.trades, true).slice(0, 50),
            };
        });
    },
    pushLog: function (log) {
        return set(function (state) { return ({
            logs: __spreadArray([log], state.logs, true).slice(0, 40),
        }); });
    },
    panicSell: function () {
        return set(function (state) {
            var panicLog = {
                id: crypto.randomUUID(),
                timestamp: new Date().toISOString(),
                level: "panic",
                message: "PANIC SELL déclenché côté frontend",
            };
            return {
                halted: true,
                signals: [],
                orderBook: null,
                trades: [],
                logs: __spreadArray([panicLog], state.logs, true).slice(0, 40),
                risk: clampRisk(__assign(__assign({}, state.risk), { utilization: 0, dailyPnL: state.risk.dailyPnL - 100 })),
            };
        });
    },
    reset: function () {
        return set({ signals: [], risk: initialRisk, halted: false, orderBook: null, trades: [], logs: [] });
    },
}); });
function clampRisk(risk) {
    return __assign(__assign({}, risk), { dailyPnL: clamp(risk.dailyPnL, risk.dailyLimit * 1.2, risk.equity * 0.05), utilization: clamp(risk.utilization, 0, 1) });
}
