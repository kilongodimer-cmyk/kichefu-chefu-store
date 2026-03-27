import { useEffect, useMemo, useRef } from "react";
import {
  createChart,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";

import type { OrderBookSnapshot, TradeTick } from "../types/trading";

interface ChartPanelProps {
  orderBook: OrderBookSnapshot | null;
  trades: TradeTick[];
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && isFinite(value);
}

export function ChartPanel({ orderBook, trades }: ChartPanelProps) {
  const bids = orderBook?.bids.slice(0, 6) ?? [];
  const asks = orderBook?.asks.slice(0, 6) ?? [];
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  const { candles, volumes } = useMemo(() => {
    const bucket = new Map<number, {
      time: UTCTimestamp;
      open: number;
      high: number;
      low: number;
      close: number;
      volume: number;
    }>();

    for (const trade of trades) {
      const ts = trade.timestamp ?? Date.parse(trade.receivedAt);
      if (!isFiniteNumber(ts)) {
        continue;
      }
      const minuteBucket = Math.floor(ts / 60000) * 60; // seconds for Lightweight Charts
      const time = minuteBucket as UTCTimestamp;
      const existing = bucket.get(minuteBucket);
      if (!existing) {
        bucket.set(minuteBucket, {
          time,
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

    let sorted = Array.from(bucket.values()).sort((a, b) => a.time - b.time);
    if (sorted.length > 200) {
      sorted = sorted.slice(-200);
    }

    const candleData: CandlestickData[] = sorted.map((candle) => ({
      time: candle.time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    const volumeData: HistogramData[] = sorted.map((candle) => ({
      time: candle.time,
      value: Number(candle.volume.toFixed(4)),
      color: candle.close >= candle.open ? "rgba(52,211,153,0.6)" : "rgba(248,113,113,0.6)",
    }));

    return { candles: candleData, volumes: volumeData };
  }, [trades]);

  useEffect(() => {
    if (!chartContainerRef.current) {
      return undefined;
    }

    const container = chartContainerRef.current;
    const chart = createChart(container, {
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
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#34d399",
      downColor: "#f87171",
      wickUpColor: "#34d399",
      wickDownColor: "#f87171",
      borderVisible: false,
    });

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "",
      base: 0,
    });
    chart.priceScale("").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    const resize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };
    resize();
    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current) {
      return;
    }
    candleSeriesRef.current.setData(candles);
    volumeSeriesRef.current.setData(volumes);
    if (candles.length > 0) {
      chartRef.current?.timeScale().fitContent();
    }
  }, [candles, volumes]);

  const lastTrade = trades[0];

  return (
    <div className="surface-card interactive-lift p-4 md:p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 text-sm text-slate-400">
        <p className="title-display font-bold text-slate-100">{orderBook?.symbol ?? "BTC/USDT"}</p>
        <p>{orderBook ? `Spread ${orderBook.spread.toFixed(2)}` : "Waiting feed"}</p>
        {lastTrade && (
          <span className="text-xs text-emerald-300">
            Last trade {lastTrade.price.toFixed(2)} · {lastTrade.side}
          </span>
        )}
      </div>

      <div className="h-64" ref={chartContainerRef} />

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <OrderBookSide title="Bids" data={bids} accent="text-emerald-300" />
        <OrderBookSide title="Asks" data={asks} accent="text-rose-300" />
      </div>

      <p className="mt-4 text-xs text-slate-500">
        {orderBook
          ? `Carnet mis à jour ${new Date(orderBook.receivedAt).toLocaleTimeString()}`
          : "Connecté au flux Binance…"}
      </p>
    </div>
  );
}

interface OrderBookSideProps {
  title: string;
  data: number[][];
  accent: string;
}

function OrderBookSide({ title, data, accent }: OrderBookSideProps) {
  return (
    <div>
      <div className="flex items-center justify-between text-xs text-slate-500">
        <p className={`text-sm font-semibold ${accent}`}>{title}</p>
        <p>px / size</p>
      </div>
      <div className="mt-2 space-y-1 text-xs text-slate-300">
        {data.length === 0 && <p className="text-slate-600">—</p>}
        {data.map(([price, size]) => (
          <div
            key={`${title}-${price}-${size}`}
            className="interactive-lift flex justify-between rounded-[10px] bg-white/7 px-2 py-1"
          >
            <span>{price.toFixed(2)}</span>
            <span>{size.toFixed(3)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
