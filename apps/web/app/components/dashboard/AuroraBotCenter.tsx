"use client";

import type { DashboardBotStatus } from "./types";

type Props = {
  status: DashboardBotStatus;
  onStatusChange: (s: DashboardBotStatus) => void;
  risk: number;
  onRiskChange: (n: number) => void;
};

const ring: Record<DashboardBotStatus, string> = {
  ACTIVE:
    "border-emerald-400/45 bg-emerald-500/15 text-emerald-200 shadow-aizix-status-emerald",
  PAUSED:
    "border-amber-400/45 bg-amber-500/15 text-amber-200 shadow-aizix-status-amber",
  STOPPED: "border-rose-500/45 bg-rose-500/15 text-rose-200 shadow-aizix-status-red",
};

export function AuroraBotCenter({
  status,
  onStatusChange,
  risk,
  onRiskChange,
}: Props) {
  return (
    <section
      aria-label="Bot control center"
      className="relative overflow-hidden rounded-2xl border border-violet-500/25 bg-slate-950/55 p-5 shadow-aizix-signals backdrop-blur-2xl sm:p-6"
    >
      <div className="pointer-events-none absolute -right-20 -top-20 size-56 rounded-full bg-violet-600/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-16 -left-10 size-48 rounded-full bg-cyan-500/15 blur-3xl" />

      <div className="relative flex flex-col gap-6 lg:flex-row lg:items-start">
        <div className="flex shrink-0 flex-col items-center lg:items-start">
          <div className="relative flex size-28 items-center justify-center rounded-2xl border border-cyan-400/40 bg-linear-to-br from-violet-600/40 via-blue-600/25 to-cyan-500/35 shadow-aurora-bull sm:size-32">
            <div className="absolute inset-0 animate-pulse rounded-2xl bg-cyan-400/10" />
            <span className="relative text-5xl drop-shadow-aurora-bull sm:text-6xl">🐂</span>
          </div>
          <p className="mt-2 text-center text-aizix-micro font-bold uppercase tracking-widest text-violet-300/90 lg:text-left">
            Holographic bull
          </p>
        </div>

        <div className="min-w-0 flex-1 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-bold tracking-tight text-white">
              Bot Control Center
            </h2>
            <span
              className={`rounded-full border px-3 py-1 text-xs font-bold uppercase ${ring[status]}`}
            >
              {status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <button
              type="button"
              onClick={() => onStatusChange("ACTIVE")}
              className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 py-2.5 text-xs font-bold text-emerald-200 transition-all hover:bg-emerald-500/20 sm:text-sm"
            >
              Start
            </button>
            <button
              type="button"
              onClick={() => onStatusChange("PAUSED")}
              className="rounded-xl border border-amber-500/40 bg-amber-500/10 py-2.5 text-xs font-bold text-amber-200 transition-all hover:bg-amber-500/20 sm:text-sm"
            >
              Pause
            </button>
            <button
              type="button"
              onClick={() => onStatusChange("STOPPED")}
              className="rounded-xl border border-slate-500/40 bg-slate-800/40 py-2.5 text-xs font-bold text-slate-200 transition-all hover:bg-slate-700/50 sm:text-sm"
            >
              Stop
            </button>
            <button
              type="button"
              onClick={() => onStatusChange("STOPPED")}
              className="rounded-xl border border-rose-500/50 bg-rose-500/15 py-2.5 text-xs font-bold text-rose-100 transition-all hover:bg-rose-500/25 sm:text-sm"
            >
              Emergency Stop
            </button>
          </div>

          <div className="rounded-xl border border-white/10 bg-slate-900/50 p-4">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Risk Level
              </span>
              <span className="font-mono text-sm font-bold text-cyan-300">{risk}%</span>
            </div>
            <input
              type="range"
              min={1}
              max={100}
              value={risk}
              onChange={(e) => onRiskChange(Number(e.target.value))}
              className="aurora-risk-range mt-3"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="rounded-lg border border-blue-500/35 bg-blue-500/10 px-3 py-1.5 text-xs font-bold uppercase tracking-wide text-blue-200">
              Trading Mode: ETF MODE
            </span>
            <span className="rounded-lg border border-violet-500/35 bg-violet-500/10 px-3 py-1.5 text-xs font-semibold text-violet-100">
              Strategy: AI Adaptive Strategy
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
