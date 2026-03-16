import { Activity, Bell, TriangleAlert } from "lucide-react";

import type { TerminalLog } from "../types/trading";

interface TerminalLogPanelProps {
  logs: TerminalLog[];
}

const levelStyles: Record<TerminalLog["level"], string> = {
  info: "text-slate-300",
  signal: "text-emerald-300",
  warn: "text-amber-300",
  panic: "text-rose-400",
};

const levelIcon: Record<TerminalLog["level"], JSX.Element> = {
  info: <Activity size={14} />,
  signal: <Bell size={14} />,
  warn: <TriangleAlert size={14} />,
  panic: <TriangleAlert size={14} />,
};

export function TerminalLogPanel({ logs }: TerminalLogPanelProps) {
  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/50 p-4 backdrop-blur">
      <header className="mb-4 flex items-center justify-between text-sm text-slate-300">
        <span className="flex items-center gap-2">
          <Activity size={16} /> Journal IA
        </span>
        <span className="text-xs text-slate-500">{logs.length} events</span>
      </header>
      <div className="space-y-2 text-xs text-slate-300">
        {logs.length === 0 && <p className="text-center text-slate-500">En attente d'activité…</p>}
        {logs.map((log) => (
          <article
            key={log.id}
            className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-3 py-2"
          >
            <div className={`flex items-center gap-2 ${levelStyles[log.level]}`}>
              {levelIcon[log.level]}
              <p className="text-sm font-medium">{log.message}</p>
            </div>
            <time className="text-[11px] text-slate-500" dateTime={log.timestamp}>
              {new Date(log.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </time>
          </article>
        ))}
      </div>
    </div>
  );
}
