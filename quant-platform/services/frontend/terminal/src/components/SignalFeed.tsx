import { Activity, Zap } from "lucide-react";

import type { SignalEvent } from "../types/trading";

interface SignalFeedProps {
  signals: SignalEvent[];
  halted?: boolean;
}

export function SignalFeed({ signals, halted = false }: SignalFeedProps) {
  const latestSignal = signals[0];

  const isBuySignal = (direction: string) => {
    const normalized = direction.toUpperCase();
    return normalized.includes("BUY") || normalized.includes("LONG");
  };

  return (
    <div className="surface-card interactive-lift p-4 md:p-5">
      <header className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-300">
          <Zap size={16} /> Live Signals
        </div>
        <span
          className={`inline-flex items-center gap-2 rounded-[10px] px-3 py-1 text-xs font-medium tracking-[0.2em] ${
            halted
              ? "bg-amber-500/18 text-amber-200"
              : "bg-emerald-500/12 text-emerald-200"
          }`}
        >
          {halted ? "PAUSE" : "LIVE"}
        </span>
      </header>

      {latestSignal && (
        <article
          className={`mb-4 rounded-[12px] border px-4 py-3 ${
            isBuySignal(latestSignal.direction)
              ? "border-emerald-400/35 bg-emerald-500/10"
              : "border-rose-400/35 bg-rose-500/10"
          }`}
        >
          <p className="text-[11px] uppercase tracking-[0.14em] text-slate-300">Dernier signal</p>
          <div className="mt-2 flex items-center justify-between gap-2">
            <p className="text-xl font-extrabold text-white">{latestSignal.direction}</p>
            <span
              className={`rounded-[8px] px-2 py-1 text-[11px] font-bold tracking-[0.12em] ${
                isBuySignal(latestSignal.direction)
                  ? "bg-emerald-500/15 text-emerald-100"
                  : "bg-rose-500/15 text-rose-100"
              }`}
            >
              {isBuySignal(latestSignal.direction) ? "BUY" : "SELL"}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-200">Confiance {(latestSignal.confidence * 100).toFixed(0)}%</p>
        </article>
      )}

      <div className="max-h-[360px] space-y-3 overflow-y-auto pr-1">
        {signals.map((signal) => (
          <article
            key={signal.id}
            className="rounded-[10px] border border-white/12 bg-slate-900/45 p-3"
          >
            <div className="flex items-center justify-between text-xs text-slate-400">
              <p>{signal.symbol}</p>
              <time dateTime={signal.timestamp}>
                {new Date(signal.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </time>
            </div>
            <div className="mt-1 flex items-center justify-between">
              <p className="text-lg font-semibold">
                {signal.direction}
                <span className="ml-2 text-sm text-slate-400">
                  {(signal.confidence * 100).toFixed(0)}%
                </span>
              </p>
              <div
                className={`inline-flex items-center gap-1 rounded-[10px] px-3 py-1 text-xs ${
                  isBuySignal(signal.direction)
                    ? "bg-emerald-500/12 text-emerald-300"
                    : "bg-rose-500/12 text-rose-300"
                }`}
              >
                <Activity size={12} /> {isBuySignal(signal.direction) ? "BUY" : "SELL"}
              </div>
            </div>
            <p className="mt-2 text-sm text-slate-400">{signal.reason}</p>
          </article>
        ))}
        {signals.length === 0 && (
          <p className="text-center text-sm text-slate-500">
            {halted ? "Bot en pause" : "Aucun signal pour le moment."}
          </p>
        )}
      </div>
    </div>
  );
}
