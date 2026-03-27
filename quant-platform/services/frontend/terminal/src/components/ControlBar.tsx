import { Flame, RefreshCcw } from "lucide-react";

interface ControlBarProps {
  halted: boolean;
  onPanicSell: () => void;
  onResume: () => void;
}

export function ControlBar({ halted, onPanicSell, onResume }: ControlBarProps) {
  return (
    <div className="surface-card-strong interactive-lift p-4 md:p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-300">Controls</p>
          <p className="title-display text-lg font-bold text-white md:text-xl">
            {halted ? "Bot en pause" : "Bot en exécution"}
          </p>
          <p className="text-sm text-slate-300/85">
            Utilisez Panic Sell pour couper instantanément toutes les positions. Resume relance le flux temps réel.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={onPanicSell}
            disabled={halted}
            className="interactive-lift inline-flex items-center gap-2 rounded-[10px] bg-rose-500/70 px-5 py-2 text-sm font-semibold text-white hover:bg-rose-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Flame size={16} /> Panic Sell
          </button>
          <button
            type="button"
            onClick={onResume}
            disabled={!halted}
            className="interactive-lift inline-flex items-center gap-2 rounded-[10px] border border-slate-300/35 bg-white/5 px-5 py-2 text-sm font-semibold text-white hover:border-slate-100/65 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCcw size={16} /> Resume
          </button>
        </div>
      </div>
    </div>
  );
}
