import { ArrowDownRight, ArrowUpRight, Radio } from "lucide-react";

import type { TradeTick } from "../types/trading";

interface TradeFeedProps {
  trades: TradeTick[];
}

export function TradeFeed({ trades }: TradeFeedProps) {
  const latest = trades.slice(0, 20);

  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4 backdrop-blur">
      <header className="mb-4 flex items-center justify-between text-sm text-slate-300">
        <span className="flex items-center gap-2">
          <Radio size={16} /> Live Tape
        </span>
        <span className="text-xs text-slate-500">{latest.length} ticks</span>
      </header>

      <div className="space-y-2 text-xs text-slate-300">
        {latest.length === 0 && <p className="text-center text-slate-500">Flux en attente…</p>}
        {latest.map((trade) => {
          const sideLong = trade.side.toUpperCase() === "BUY" || trade.side.toUpperCase() === "BID";
          const SideIcon = sideLong ? ArrowUpRight : ArrowDownRight;
          const color = sideLong ? "text-emerald-300" : "text-rose-300";
          return (
            <article
              key={`${trade.symbol}-${trade.receivedAt}-${trade.price}-${trade.amount}`}
              className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <SideIcon size={16} className={color} />
                <div>
                  <p className="text-sm font-semibold text-white">{trade.price.toFixed(2)}</p>
                  <p className="text-[11px] text-slate-500">{trade.symbol}</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-sm font-medium ${color}`}>{trade.amount.toFixed(4)}</p>
                <time className="text-[11px] text-slate-500" dateTime={trade.receivedAt}>
                  {new Date(trade.receivedAt).toLocaleTimeString([], { minute: "2-digit", second: "2-digit" })}
                </time>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
