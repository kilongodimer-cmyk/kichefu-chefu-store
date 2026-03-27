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

const DEFAULT_SYMBOL = "BTCUSDT";
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export function App() {
  const signals = useTerminalStore((state) => state.signals);
  const risk = useTerminalStore((state) => state.risk);
  const halted = useTerminalStore((state) => state.halted);
  const orderBook = useTerminalStore((state) => state.orderBook);
  const trades = useTerminalStore((state) => state.trades);
  const pushSignal = useTerminalStore((state) => state.pushSignal);
  const updateRisk = useTerminalStore((state) => state.updateRisk);
  const setOrderBook = useTerminalStore((state) => state.setOrderBook);
  const pushTrade = useTerminalStore((state) => state.pushTrade);
  const localPanic = useTerminalStore((state) => state.panicSell);
  const setHalted = useTerminalStore((state) => state.setHalted);
  const pushLog = useTerminalStore((state) => state.pushLog);
  const logs = useTerminalStore((state) => state.logs);
  const [readingMode, setReadingMode] = useState(false);
  const [frozenOrderBook, setFrozenOrderBook] = useState(orderBook);
  const [frozenTrades, setFrozenTrades] = useState(trades);
  const [frozenSignals, setFrozenSignals] = useState(signals);

  useEffect(() => {
    if (!readingMode) {
      setFrozenOrderBook(orderBook);
    }
  }, [orderBook, readingMode]);

  useEffect(() => {
    if (!readingMode) {
      setFrozenTrades(trades);
    }
  }, [trades, readingMode]);

  useEffect(() => {
    if (!readingMode) {
      setFrozenSignals(signals);
    }
  }, [signals, readingMode]);

  const visibleOrderBook = readingMode ? frozenOrderBook : orderBook;
  const visibleTrades = readingMode ? frozenTrades : trades;
  const visibleSignals = readingMode ? frozenSignals : signals;

  const liveSharpe = useMemo(() => {
    if (trades.length < 5) {
      return null;
    }
    const chronological = [...trades].reverse();
    const returns: number[] = [];
    for (let i = 1; i < chronological.length; i += 1) {
      const prev = chronological[i - 1];
      const current = chronological[i];
      if (!prev || !current) {
        continue;
      }
      const ret = (current.price - prev.price) / prev.price;
      if (Number.isFinite(ret)) {
        returns.push(ret);
      }
    }
    if (returns.length < 5) {
      return null;
    }
    const mean = returns.reduce((sum, value) => sum + value, 0) / returns.length;
    const variance =
      returns.reduce((sum, value) => sum + (value - mean) * (value - mean), 0) / returns.length;
    const std = Math.sqrt(Math.max(variance, 1e-12));
    return std === 0 ? null : Math.sqrt(252) * mean / std;
  }, [trades]);

  useMarketStream({
    symbol: DEFAULT_SYMBOL,
    halted,
    onSignal: (signal) => {
      pushSignal(signal);
      pushLog({
        id: crypto.randomUUID(),
        timestamp: signal.timestamp,
        level: "signal",
        message: `${signal.direction} ${signal.symbol} ${(signal.confidence * 100).toFixed(0)}%`,
        detail: `${signal.reason} • Sharpe ${(liveSharpe ?? 0).toFixed(2)}`,
      });
    },
    onRiskUpdate: (next) => {
      updateRisk(() => next);
      pushLog({
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        level: "info",
        message: `Risk refresh • PnL ${next.dailyPnL.toFixed(0)} USD`,
        detail: `Utilisation ${(next.utilization * 100).toFixed(1)}% • Equity ${next.equity.toFixed(0)}`,
      });
    },
    onOrderBook: setOrderBook,
    onTrade: pushTrade,
  });

  const postControl = async (endpoint: string) => {
    const response = await fetch(`${API_BASE}${endpoint}`, { method: "POST" });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "Control action failed");
    }
  };

  const handlePanicSell = async () => {
    if (halted) {
      return;
    }
    try {
      await postControl("/market/panic-sell");
      localPanic();
      pushLog({
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        level: "panic",
        message: "PANIC SELL envoyé au backend",
        detail: `Sharpe ${(liveSharpe ?? 0).toFixed(2)} • Trades ${trades.length}`,
      });
    } catch (error) {
      console.error("Unable to trigger panic sell", error);
      pushLog({
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        level: "warn",
        message: `Erreur Panic Sell: ${String(error)}`,
        detail: `Sharpe ${(liveSharpe ?? 0).toFixed(2)}`,
      });
    }
  };

  const handleResume = async () => {
    if (!halted) {
      return;
    }
    try {
      await postControl("/market/resume");
      setHalted(false);
      pushLog({
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        level: "info",
        message: "Resume trading envoyé",
        detail: `Sharpe ${(liveSharpe ?? 0).toFixed(2)}`,
      });
    } catch (error) {
      console.error("Unable to resume trading", error);
      pushLog({
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        level: "warn",
        message: `Erreur Resume: ${String(error)}`,
      });
    }
  };

  const showDailyWarning = useMemo(
    () => risk.dailyPnL <= risk.dailyLimit * 0.8,
    [risk.dailyPnL, risk.dailyLimit],
  );

  return (
    <div className="min-h-screen text-slate-100">
      <header className="border-b border-white/10 px-4 py-4 md:px-8 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Quant Platform</p>
          <h1 className="title-display text-xl font-extrabold text-white md:text-3xl">Real-Time Trading Terminal</h1>
        </div>
        <button
          className="interactive-lift inline-flex items-center gap-2 rounded-[10px] border border-rose-300/30 bg-rose-500/12 px-4 py-2 text-rose-200 hover:bg-rose-500/18 disabled:opacity-60"
          onClick={handlePanicSell}
          disabled={halted}
        >
          <Power size={16} /> Panic Sell
        </button>
        <button
          type="button"
          className={`interactive-lift inline-flex items-center gap-2 rounded-[10px] border px-4 py-2 text-sm ${
            readingMode
              ? "border-amber-300/35 bg-amber-500/14 text-amber-100"
              : "border-white/20 bg-white/8 text-slate-100"
          }`}
          onClick={() => setReadingMode((current) => !current)}
        >
          {readingMode ? "Reprendre le live" : "Mode lecture (figer)"}
        </button>
      </header>

      <main className="grid grid-cols-1 gap-5 p-4 md:gap-6 md:p-8 xl:grid-cols-3">
        <section className="section-enter xl:col-span-2 space-y-5 md:space-y-6">
          <ControlBar
            halted={halted}
            onPanicSell={handlePanicSell}
            onResume={handleResume}
          />
          <div className="grid gap-6 lg:grid-cols-2">
            <ChartPanel orderBook={visibleOrderBook} trades={visibleTrades} />
            <TradeFeed trades={visibleTrades} />
          </div>
          <SignalFeed signals={visibleSignals} halted={halted} />
        </section>
        <aside className="section-enter space-y-5 md:space-y-6">
          <RiskPanel stats={risk} showWarning={showDailyWarning} />
          <TerminalLogPanel logs={logs} />
          <div className="surface-card interactive-lift p-5">
            <p className="flex items-center gap-2 text-sm font-medium text-slate-300">
              <Activity size={16} /> AI Model
            </p>
            <p className="title-display mt-3 text-3xl font-bold text-white">RandomForest v0.1</p>
            <p className="mt-2 text-sm text-slate-400">
              Live inference with 150 estimators, retrained 2026-03-15.
            </p>
            {showDailyWarning && (
              <p className="mt-4 flex items-center gap-2 text-sm text-amber-300">
                <AlertTriangle size={16} />
                Daily PnL approaching limit.
              </p>
            )}
          </div>
        </aside>
      </main>
    </div>
  );
}
