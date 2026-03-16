import { Activity, Zap } from "lucide-react";

import type { SignalEvent } from "../types/trading";

interface SignalFeedProps {
  signals: SignalEvent[];
  halted?: boolean;
}

export function SignalFeed({ signals, halted = false }: SignalFeedProps) {
  return (
    <div className="rounded-2xl border border-white/5 bg-white/5 p-4 backdrop-blur">
      <header className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-300">
          <Zap size={16} /> Live Signals
        </div>
        <span
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium tracking-[0.2em] ${
            halted
              ? "bg-amber-500/20 text-amber-200"
              : "bg-emerald-500/10 text-emerald-200"
          }`}
        >
          {halted ? "PAUSE" : "LIVE"}
        </span>
      </header>
      <div className="space-y-3">
        {signals.map((signal) => (
          <article
            key={signal.id}
            className="rounded-xl border border-white/10 bg-slate-900/50 p-3"
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
              <div className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
                <Activity size={12} /> RF Score
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
