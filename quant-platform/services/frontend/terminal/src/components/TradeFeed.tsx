import { useEffect, useMemo, useState } from "react";
import { ArrowDownRight, ArrowUpRight, Pause, Radio } from "lucide-react";

import type { TradeTick } from "../types/trading";

interface TradeFeedProps {
  trades: TradeTick[];
}

export function TradeFeed({ trades }: TradeFeedProps) {
  const [freezeFeed, setFreezeFeed] = useState(false);
  const [snapshot, setSnapshot] = useState<TradeTick[]>([]);

  useEffect(() => {
    if (!freezeFeed) {
      setSnapshot(trades.slice(0, 12));
    }
  }, [trades, freezeFeed]);

  const latest = freezeFeed ? snapshot : trades.slice(0, 12);

  const sideSummary = useMemo(() => {
    return latest.reduce(
      (acc, trade) => {
        const isBuy = trade.side.toUpperCase() === "BUY" || trade.side.toUpperCase() === "BID";
        if (isBuy) {
          acc.buy += 1;
        } else {
          acc.sell += 1;
        }
        return acc;
      },
      { buy: 0, sell: 0 },
    );
  }, [latest]);

  return (
    <div className="surface-card interactive-lift p-4 md:p-5">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-2 text-sm text-slate-300">
        <span className="flex items-center gap-2">
          <Radio size={16} /> Live Tape
        </span>
        <div className="flex items-center gap-2">
          <span className="rounded-[8px] bg-emerald-500/12 px-2 py-1 text-[11px] font-semibold text-emerald-300">
            BUY {sideSummary.buy}
          </span>
          <span className="rounded-[8px] bg-rose-500/12 px-2 py-1 text-[11px] font-semibold text-rose-300">
            SELL {sideSummary.sell}
          </span>
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded-[8px] border border-white/15 px-2 py-1 text-[11px] text-slate-300 hover:bg-white/8"
            onClick={() => setFreezeFeed((current) => !current)}
          >
            <Pause size={12} /> {freezeFeed ? "Reprendre" : "Pause flux"}
          </button>
        </div>
      </header>

      <div className="max-h-[360px] space-y-2 overflow-y-auto pr-1 text-xs text-slate-300">
        {latest.length === 0 && <p className="text-center text-slate-500">Flux en attente…</p>}
        {latest.map((trade) => {
          const sideLong = trade.side.toUpperCase() === "BUY" || trade.side.toUpperCase() === "BID";
          const SideIcon = sideLong ? ArrowUpRight : ArrowDownRight;
          const color = sideLong ? "text-emerald-300" : "text-rose-300";
          return (
            <article
              key={`${trade.symbol}-${trade.receivedAt}-${trade.price}-${trade.amount}`}
              className="flex items-center justify-between rounded-[10px] border border-white/10 bg-white/7 px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <SideIcon size={16} className={color} />
                <div>
                  <p className="text-sm font-semibold text-white">{trade.price.toFixed(2)}</p>
                  <p className="text-[11px] text-slate-500">{trade.symbol}</p>
                </div>
              </div>
              <div className="text-right">
                <p
                  className={`inline-block rounded-[8px] px-2 py-0.5 text-[10px] font-bold tracking-[0.14em] ${
                    sideLong ? "bg-emerald-500/12 text-emerald-200" : "bg-rose-500/12 text-rose-200"
                  }`}
                >
                  {sideLong ? "BUY" : "SELL"}
                </p>
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
