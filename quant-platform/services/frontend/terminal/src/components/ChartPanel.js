import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useRef } from "react";
import { createChart, } from "lightweight-charts";
function isFiniteNumber(value) {
    return typeof value === "number" && isFinite(value);
}
export function ChartPanel(_a) {
    var _b, _c, _d;
    var orderBook = _a.orderBook, trades = _a.trades;
    var bids = (_b = orderBook === null || orderBook === void 0 ? void 0 : orderBook.bids.slice(0, 6)) !== null && _b !== void 0 ? _b : [];
    var asks = (_c = orderBook === null || orderBook === void 0 ? void 0 : orderBook.asks.slice(0, 6)) !== null && _c !== void 0 ? _c : [];
    var chartContainerRef = useRef(null);
    var chartRef = useRef(null);
    var candleSeriesRef = useRef(null);
    var volumeSeriesRef = useRef(null);
    var _e = useMemo(function () {
        var _a;
        var bucket = new Map();
        for (var _i = 0, trades_1 = trades; _i < trades_1.length; _i++) {
            var trade = trades_1[_i];
            var ts = (_a = trade.timestamp) !== null && _a !== void 0 ? _a : Date.parse(trade.receivedAt);
            if (!isFiniteNumber(ts)) {
                continue;
            }
            var minuteBucket = Math.floor(ts / 60000) * 60; // seconds for Lightweight Charts
            var time = minuteBucket;
            var existing = bucket.get(minuteBucket);
            if (!existing) {
                bucket.set(minuteBucket, {
                    time: time,
                    open: trade.price,
                    high: trade.price,
                    low: trade.price,
                    close: trade.price,
                    volume: trade.amount,
                });
                continue;
            }
            existing.high = Math.max(existing.high, trade.price);
            existing.low = Math.min(existing.low, trade.price);
            existing.close = trade.price;
            existing.volume += trade.amount;
        }
        var sorted = Array.from(bucket.values()).sort(function (a, b) { return a.time - b.time; });
        if (sorted.length > 200) {
            sorted = sorted.slice(-200);
        }
        var candleData = sorted.map(function (candle) { return ({
            time: candle.time,
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close,
        }); });
        var volumeData = sorted.map(function (candle) { return ({
            time: candle.time,
            value: Number(candle.volume.toFixed(4)),
            color: candle.close >= candle.open ? "rgba(52,211,153,0.6)" : "rgba(248,113,113,0.6)",
        }); });
        return { candles: candleData, volumes: volumeData };
    }, [trades]), candles = _e.candles, volumes = _e.volumes;
    useEffect(function () {
        if (!chartContainerRef.current) {
            return undefined;
        }
        var container = chartContainerRef.current;
        var chart = createChart(container, {
            layout: {
                background: { color: "transparent" },
                textColor: "#cbd5f5",
            },
            grid: {
                vertLines: { color: "rgba(255,255,255,0.04)" },
                horzLines: { color: "rgba(255,255,255,0.04)" },
            },
            rightPriceScale: { borderVisible: false },
            timeScale: { borderVisible: false },
        });
        var candleSeries = chart.addCandlestickSeries({
            upColor: "#34d399",
            downColor: "#f87171",
            wickUpColor: "#34d399",
            wickDownColor: "#f87171",
            borderVisible: false,
        });
        var volumeSeries = chart.addHistogramSeries({
            priceFormat: { type: "volume" },
            priceScaleId: "",
            base: 0,
        });
        chart.priceScale("").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;
        volumeSeriesRef.current = volumeSeries;
        var resize = function () {
            if (chartContainerRef.current) {
                chart.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight,
                });
            }
        };
        resize();
        window.addEventListener("resize", resize);
        return function () {
            window.removeEventListener("resize", resize);
            chart.remove();
        };
    }, []);
    useEffect(function () {
        var _a;
        if (!candleSeriesRef.current || !volumeSeriesRef.current) {
            return;
        }
        candleSeriesRef.current.setData(candles);
        volumeSeriesRef.current.setData(volumes);
        if (candles.length > 0) {
            (_a = chartRef.current) === null || _a === void 0 ? void 0 : _a.timeScale().fitContent();
        }
    }, [candles, volumes]);
    var lastTrade = trades[0];
    return (_jsxs("div", { className: "surface-card interactive-lift p-4 md:p-5", children: [_jsxs("div", { className: "mb-4 flex flex-wrap items-center justify-between gap-2 text-sm text-slate-400", children: [_jsx("p", { className: "title-display font-bold text-slate-100", children: (_d = orderBook === null || orderBook === void 0 ? void 0 : orderBook.symbol) !== null && _d !== void 0 ? _d : "BTC/USDT" }), _jsx("p", { children: orderBook ? "Spread ".concat(orderBook.spread.toFixed(2)) : "Waiting feed" }), lastTrade && (_jsxs("span", { className: "text-xs text-emerald-300", children: ["Last trade ", lastTrade.price.toFixed(2), " \u00B7 ", lastTrade.side] }))] }), _jsx("div", { className: "h-64", ref: chartContainerRef }), _jsxs("div", { className: "mt-4 grid gap-4 md:grid-cols-2", children: [_jsx(OrderBookSide, { title: "Bids", data: bids, accent: "text-emerald-300" }), _jsx(OrderBookSide, { title: "Asks", data: asks, accent: "text-rose-300" })] }), _jsx("p", { className: "mt-4 text-xs text-slate-500", children: orderBook
                    ? "Carnet mis \u00E0 jour ".concat(new Date(orderBook.receivedAt).toLocaleTimeString())
                    : "Connecté au flux Binance…" })] }));
}
function OrderBookSide(_a) {
    var title = _a.title, data = _a.data, accent = _a.accent;
    return (_jsxs("div", { children: [_jsxs("div", { className: "flex items-center justify-between text-xs text-slate-500", children: [_jsx("p", { className: "text-sm font-semibold ".concat(accent), children: title }), _jsx("p", { children: "px / size" })] }), _jsxs("div", { className: "mt-2 space-y-1 text-xs text-slate-300", children: [data.length === 0 && _jsx("p", { className: "text-slate-600", children: "\u2014" }), data.map(function (_a) {
                        var price = _a[0], size = _a[1];
                        return (_jsxs("div", { className: "interactive-lift flex justify-between rounded-[10px] bg-white/7 px-2 py-1", children: [_jsx("span", { children: price.toFixed(2) }), _jsx("span", { children: size.toFixed(3) })] }, "".concat(title, "-").concat(price, "-").concat(size)));
                    })] })] }));
}
