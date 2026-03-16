import { ShieldAlert, TrendingDown, TrendingUp } from "lucide-react";

import type { RiskStats } from "../types/trading";

interface RiskPanelProps {
  stats: RiskStats;
  showWarning?: boolean;
}

export function RiskPanel({ stats, showWarning = false }: RiskPanelProps) {
  const equityPct = (stats.dailyPnL / stats.equity) * 100;
  const limitPct = (stats.dailyLimit / stats.equity) * 100;

  return (
    <div className="rounded-2xl border border-white/5 bg-gradient-to-br from-slate-900/80 to-slate-900/30 p-5 backdrop-blur">
      <header className="flex items-center justify-between text-sm text-slate-300">
        <div className="flex items-center gap-2">
          <ShieldAlert size={16} /> Gestion du risque
        </div>
        <span className="text-xs uppercase tracking-[0.3em] text-slate-500">
          2% Max
        </span>
      </header>
      <div className="mt-4 space-y-3">
        <StatRow
          label="Capital"
          value={formatCurrency(stats.equity)}
          accent="text-slate-100"
        />
        <StatRow
          label="PnL journalier"
          value={formatCurrency(stats.dailyPnL)}
          accent={stats.dailyPnL >= 0 ? "text-emerald-300" : "text-rose-300"}
          icon={stats.dailyPnL >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
        />
        <StatRow
          label="Limite journalière"
          value={formatCurrency(stats.dailyLimit)}
          accent="text-amber-300"
        />
      </div>
      <div className="mt-5">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
          Utilisation
        </p>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-gradient-to-r from-sky-400 to-fuchsia-400 transition-all"
            style={{ width: `${Math.min(stats.utilization * 100, 100)}%` }}
          />
        </div>
        <div className="mt-2 flex justify-between text-xs text-slate-400">
          <span>{(stats.utilization * 100).toFixed(1)}%</span>
          <span>2% par trade</span>
        </div>
      </div>
      <div className="mt-5 space-y-2 text-xs text-slate-400">
        <p>
          PnL vs capital : {equityPct.toFixed(2)}% • Limite : {limitPct.toFixed(2)}%
        </p>
        {showWarning && (
          <p className="rounded-xl bg-amber-500/10 px-3 py-2 text-amber-200">
            Attention : le bot se rapproche de la limite journalière.
          </p>
        )}
      </div>
    </div>
  );
}

interface StatRowProps {
  label: string;
  value: string;
  accent: string;
  icon?: React.ReactNode;
}

function StatRow({ label, value, accent, icon }: StatRowProps) {
  return (
    <div className="flex items-center justify-between text-sm text-slate-400">
      <span>{label}</span>
      <span className={`flex items-center gap-2 font-semibold ${accent}`}>
        {icon}
        {value}
      </span>
    </div>
  );
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}
