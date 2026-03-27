import { useEffect } from "react";
export function useMarketStream(_a) {
    var symbol = _a.symbol, halted = _a.halted, onOrderBook = _a.onOrderBook, onTrade = _a.onTrade, onSignal = _a.onSignal, onRiskUpdate = _a.onRiskUpdate;
    useEffect(function () {
        var _a;
        if (halted) {
            return undefined;
        }
        var lastPrice = 68250;
        var fallbackTick = 0;
        var fallbackInterval = null;
        var fallbackTimeout = null;
        var pushFallbackFrame = function () {
            var _a, _b, _c, _d, _e, _f, _g, _h;
            var drift = (Math.random() - 0.5) * 120;
            lastPrice = Math.max(100, lastPrice + drift);
            var now = new Date().toISOString();
            var side = drift >= 0 ? "BUY" : "SELL";
            onTrade === null || onTrade === void 0 ? void 0 : onTrade({
                symbol: symbol,
                price: Number(lastPrice.toFixed(2)),
                amount: Number((Math.random() * 0.35 + 0.01).toFixed(4)),
                side: side,
                timestamp: Date.now(),
                receivedAt: now,
            });
            var levels = Array.from({ length: 6 }, function (_, index) {
                var step = (index + 1) * 2.5;
                return [
                    Number((lastPrice - step).toFixed(2)),
                    Number((Math.random() * 0.9 + 0.1).toFixed(3)),
                ];
            });
            var asks = Array.from({ length: 6 }, function (_, index) {
                var step = (index + 1) * 2.5;
                return [
                    Number((lastPrice + step).toFixed(2)),
                    Number((Math.random() * 0.9 + 0.1).toFixed(3)),
                ];
            });
            onOrderBook === null || onOrderBook === void 0 ? void 0 : onOrderBook({
                symbol: symbol,
                bids: levels,
                asks: asks,
                bestBid: (_b = (_a = levels[0]) === null || _a === void 0 ? void 0 : _a[0]) !== null && _b !== void 0 ? _b : lastPrice,
                bestAsk: (_d = (_c = asks[0]) === null || _c === void 0 ? void 0 : _c[0]) !== null && _d !== void 0 ? _d : lastPrice,
                spread: Number((((_f = (_e = asks[0]) === null || _e === void 0 ? void 0 : _e[0]) !== null && _f !== void 0 ? _f : lastPrice) - ((_h = (_g = levels[0]) === null || _g === void 0 ? void 0 : _g[0]) !== null && _h !== void 0 ? _h : lastPrice)).toFixed(2)),
                receivedAt: now,
            });
            onRiskUpdate === null || onRiskUpdate === void 0 ? void 0 : onRiskUpdate({
                equity: 25000,
                dailyPnL: Number((-350 + Math.random() * 540).toFixed(0)),
                dailyLimit: -500,
                utilization: Number((0.12 + Math.random() * 0.62).toFixed(3)),
            });
            fallbackTick += 1;
            if (fallbackTick % 4 === 0) {
                onSignal === null || onSignal === void 0 ? void 0 : onSignal({
                    id: crypto.randomUUID(),
                    timestamp: now,
                    symbol: symbol,
                    direction: Math.random() > 0.5 ? "LONG" : "SHORT",
                    confidence: Number((0.58 + Math.random() * 0.38).toFixed(2)),
                    reason: "Fallback stream local actif (backend feed indisponible)",
                });
            }
        };
        var startFallback = function () {
            if (fallbackInterval !== null) {
                return;
            }
            pushFallbackFrame();
            fallbackInterval = window.setInterval(pushFallbackFrame, 1100);
        };
        var wsBase = (_a = import.meta.env.VITE_WS_BASE) !== null && _a !== void 0 ? _a : "ws://localhost:8000";
        var url = "".concat(wsBase.replace(/\/$/, ""), "/market/ws/").concat(symbol);
        var socket = new WebSocket(url);
        socket.onmessage = function (event) {
            try {
                var payload = JSON.parse(event.data);
                var _a = payload, type = _a.type, data = _a.data;
                if (type === "order_book" && data && onOrderBook) {
                    onOrderBook(data);
                }
                if (type === "trades" && (data === null || data === void 0 ? void 0 : data.trades) && onTrade) {
                    data.trades.forEach(function (trade) { return onTrade(trade); });
                }
                if (type === "signal" && data && onSignal) {
                    onSignal(data);
                }
                if (type === "risk" && (data === null || data === void 0 ? void 0 : data.stats) && onRiskUpdate) {
                    onRiskUpdate(data.stats);
                }
            }
            catch (error) {
                console.error("Failed to parse WS message", error);
            }
        };
        socket.onerror = function (error) {
            console.error("WebSocket error", error);
            startFallback();
        };
        socket.onclose = function () {
            startFallback();
        };
        fallbackTimeout = window.setTimeout(function () {
            if (socket.readyState !== WebSocket.OPEN) {
                startFallback();
            }
        }, 3000);
        return function () {
            if (fallbackTimeout !== null) {
                window.clearTimeout(fallbackTimeout);
            }
            if (fallbackInterval !== null) {
                window.clearInterval(fallbackInterval);
            }
            socket.close(1000, "cleanup");
        };
    }, [symbol, halted, onOrderBook, onTrade, onSignal, onRiskUpdate]);
}
