"use client";

import { useState } from "react";

type BotStatus = "ACTIVE" | "PAUSED" | "STOPPED";

const statusStyles: Record<
  BotStatus,
  { label: string; ring: string; text: string; dot: string }
> = {
  ACTIVE: {
    label: "ACTIVE",
    ring: "border-emerald-400/40 bg-emerald-500/10 shadow-[0_0_24px_rgba(52,211,153,0.2)]",
    text: "text-emerald-300",
    dot: "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.9)]",
  },
  PAUSED: {
    label: "PAUSED",
    ring: "border-amber-400/45 bg-amber-500/10 shadow-[0_0_24px_rgba(251,191,36,0.15)]",
    text: "text-amber-300",
    dot: "bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.85)]",
  },
  STOPPED: {
    label: "STOPPED",
    ring: "border-red-500/45 bg-red-500/10 shadow-[0_0_24px_rgba(248,113,113,0.18)]",
    text: "text-red-400",
    dot: "bg-red-500 shadow-[0_0_10px_rgba(248,113,113,0.85)]",
  },
};

export function BotControlPanel() {
  const [status, setStatus] = useState<BotStatus>("ACTIVE");
  const [compounding, setCompounding] = useState(true);

  const s = statusStyles[status];

  return (
    <section
      aria-label="Bot control panel"
      className="relative overflow-hidden rounded-3xl border border-violet-500/20 bg-slate-950/35 p-8 shadow-[0_0_48px_rgba(139,92,246,0.08)] backdrop-blur-xl sm:p-10"
    >
      <div className="pointer-events-none absolute -right-16 top-0 h-48 w-48 rounded-full bg-violet-600/15 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 left-0 h-40 w-40 rounded-full bg-cyan-500/10 blur-3xl" />

      <div className="relative flex flex-col gap-10">
        <div className="flex flex-col gap-6 border-b border-white/5 pb-8 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-violet-300/80">
              Control
            </p>
            <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              Bot Control Panel
            </h2>
            <p className="max-w-md text-sm text-slate-400">
              Live execution state and circuit breakers. Signals route only when
              status is active.
            </p>
          </div>

          <div className="flex flex-col items-start gap-2 sm:items-end">
            <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">
              Current status
            </span>
            <div
              className={`flex items-center gap-3 rounded-2xl border px-5 py-3 ${s.ring}`}
              role="status"
              aria-live="polite"
            >
              <span
                className={`relative flex h-2.5 w-2.5 shrink-0 rounded-full ${s.dot}`}
              >
                {status === "ACTIVE" ? (
                  <span className="absolute inset-0 animate-ping rounded-full bg-emerald-400/50" />
                ) : null}
              </span>
              <span
                className={`font-mono text-sm font-bold tracking-[0.2em] ${s.text}`}
              >
                {s.label}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
            Execution
          </span>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <button
              type="button"
              onClick={() => setStatus("ACTIVE")}
              className="rounded-2xl border border-emerald-500/35 bg-emerald-500/10 px-5 py-4 text-sm font-semibold text-emerald-200 shadow-[0_0_28px_rgba(16,185,129,0.12)] transition hover:border-emerald-400/50 hover:bg-emerald-500/15 hover:shadow-[0_0_36px_rgba(16,185,129,0.2)]"
            >
              Start Trading
            </button>
            <button
              type="button"
              onClick={() => setStatus("PAUSED")}
              className="rounded-2xl border border-amber-400/35 bg-amber-500/10 px-5 py-4 text-sm font-semibold text-amber-200 shadow-[0_0_28px_rgba(245,158,11,0.1)] transition hover:border-amber-400/55 hover:bg-amber-500/15 hover:shadow-[0_0_36px_rgba(245,158,11,0.18)]"
            >
              Pause
            </button>
            <button
              type="button"
              onClick={() => setStatus("STOPPED")}
              className="rounded-2xl border border-red-500/40 bg-red-500/10 px-5 py-4 text-sm font-semibold text-red-200 shadow-[0_0_28px_rgba(239,68,68,0.12)] transition hover:border-red-400/55 hover:bg-red-500/15 hover:shadow-[0_0_36px_rgba(239,68,68,0.22)]"
            >
              Emergency Stop
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-cyan-500/15 bg-slate-900/40 p-6 backdrop-blur-md">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">
                Compounding
              </h3>
              <p className="mt-1 text-xs text-slate-500">
                Auto-reinvest profits with dual-wallet routing.
              </p>
            </div>

            <button
              type="button"
              role="switch"
              aria-checked={compounding}
              aria-label="Compounding"
              onClick={() => setCompounding((v) => !v)}
              className={`relative h-12 w-[5.5rem] shrink-0 rounded-full border transition ${
                compounding
                  ? "border-cyan-400/40 bg-gradient-to-r from-violet-600/25 to-cyan-600/25 shadow-[0_0_24px_rgba(34,211,238,0.2)]"
                  : "border-white/10 bg-slate-950/70"
              }`}
            >
              <span
                className={`absolute top-1 h-10 w-10 rounded-full shadow-lg transition-all duration-300 ease-out ${
                  compounding
                    ? "right-1 bg-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.55)]"
                    : "left-1 bg-slate-600"
                }`}
              />
              <span className="pointer-events-none relative z-10 flex h-full items-center justify-between px-2.5 text-[10px] font-bold uppercase tracking-wider">
                <span className={!compounding ? "text-slate-200" : "text-slate-500"}>
                  Off
                </span>
                <span className={compounding ? "text-cyan-100" : "text-slate-500"}>
                  On
                </span>
              </span>
            </button>
          </div>

          <div
            className={`mt-6 space-y-4 transition-opacity duration-300 ${
              compounding ? "opacity-100" : "opacity-40"
            }`}
          >
            <div className="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-slate-500">
              <span>Allocation split</span>
              {!compounding ? (
                <span className="normal-case text-slate-500">Paused routing</span>
              ) : null}
            </div>
            <div className="flex h-3 overflow-hidden rounded-full border border-white/10 bg-slate-950/80">
              <div
                className="flex items-center justify-center bg-gradient-to-r from-violet-500 to-blue-500 shadow-[0_0_20px_rgba(99,102,241,0.35)]"
                style={{ width: "70%" }}
                title="Trading Wallet 70%"
              />
              <div
                className="flex items-center justify-center bg-gradient-to-r from-cyan-500 to-teal-400 shadow-[0_0_20px_rgba(34,211,238,0.25)]"
                style={{ width: "30%" }}
                title="Safety Wallet 30%"
              />
            </div>
            <div className="flex flex-col gap-3 text-sm sm:flex-row sm:justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-violet-400 shadow-[0_0_8px_rgba(167,139,250,0.8)]" />
                <span className="text-slate-300">
                  <span className="font-mono font-semibold text-violet-200">
                    70%
                  </span>{" "}
                  Trading Wallet
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
                <span className="text-slate-300">
                  <span className="font-mono font-semibold text-cyan-200">
                    30%
                  </span>{" "}
                  Safety Wallet
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
