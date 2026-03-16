import { Flame, RefreshCcw } from "lucide-react";

interface ControlBarProps {
  halted: boolean;
  onPanicSell: () => void;
  onResume: () => void;
}

export function ControlBar({ halted, onPanicSell, onResume }: ControlBarProps) {
  return (
    <div className="rounded-2xl border border-white/5 bg-gradient-to-r from-rose-600/20 via-fuchsia-600/20 to-sky-600/20 p-4 backdrop-blur">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-200">Controls</p>
          <p className="text-lg font-semibold text-white">
            {halted ? "Bot en pause" : "Bot en exécution"}
          </p>
          <p className="text-sm text-slate-200/80">
            Utilisez Panic Sell pour couper instantanément toutes les positions. Resume relance le flux temps réel.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={onPanicSell}
            disabled={halted}
            className="inline-flex items-center gap-2 rounded-full bg-rose-500/80 px-5 py-2 text-sm font-semibold text-white transition hover:bg-rose-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Flame size={16} /> Panic Sell
          </button>
          <button
            type="button"
            onClick={onResume}
            disabled={!halted}
            className="inline-flex items-center gap-2 rounded-full border border-white/20 px-5 py-2 text-sm font-semibold text-white transition hover:border-white/60 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCcw size={16} /> Resume
          </button>
        </div>
      </div>
    </div>
  );
}
