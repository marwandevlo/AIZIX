"use client";

import type { SignalPayload, SignalsPayload } from "@/lib/aizix-api";
import { formatUsd } from "@/lib/aizix-api";

const actionStyle: Record<string, string> = {
  BUY: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  SELL: "text-red-300 border-red-500/40 bg-red-500/10",
  HOLD: "text-slate-200 border-slate-500/35 bg-slate-800/40",
};

const riskStyle: Record<string, string> = {
  ok: "border-emerald-500/35 text-emerald-200/90 bg-emerald-500/10",
  low_confidence: "border-amber-400/40 text-amber-200/90 bg-amber-500/10",
  bot_not_active: "border-slate-500/40 text-slate-300 bg-slate-800/50",
  risk_halt: "border-red-500/45 text-red-200/90 bg-red-500/10",
  volatility_watch: "border-cyan-400/40 text-cyan-100/90 bg-cyan-500/10",
};

type Props = {
  signals: SignalsPayload | null;
  pulse: boolean;
  error: string | null;
};

export function AiSignalsPanel({ signals, pulse, error }: Props) {
  const latest: SignalPayload | null = signals?.latest ?? null;
  const rs = latest?.risk_status ?? "ok";

  return (
    <section
      aria-label="AI signals"
      className={`relative overflow-hidden rounded-3xl border border-violet-500/25 bg-slate-950/35 p-6 shadow-aizix-signals backdrop-blur-xl transition-shadow duration-300 sm:p-8 ${
        pulse ? "shadow-aizix-signals-pulse" : ""
      }`}
    >
      <div className="pointer-events-none absolute -left-20 top-1/2 size-40 -translate-y-1/2 rounded-full bg-cyan-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-16 top-0 size-48 rounded-full bg-violet-600/12 blur-3xl" />

      <div className="relative flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-aizix-panel text-cyan-300/80">
            Neural desk
          </p>
          <h2 className="text-xl font-semibold text-white sm:text-2xl">
            AI Signals
          </h2>
          <p className="max-w-xl text-sm text-slate-400">
            ETF sleeves (3L/3S), synthetic whale radar, and risk gating — paper
            trading only. No venue keys; no execution guarantees.
          </p>
        </div>
        {latest ? (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span
              className={`rounded-full border px-3 py-1 font-mono uppercase tracking-wider ${riskStyle[rs] ?? riskStyle.ok}`}
            >
              risk: {rs.replace(/_/g, " ")}
            </span>
            <span className="rounded-full border border-white/10 bg-slate-900/60 px-2 py-1 font-mono text-slate-400">
              {latest.latency_ms.toFixed(0)}ms
            </span>
          </div>
        ) : null}
      </div>

      {error ? (
        <p className="relative mt-4 text-sm text-amber-200/90">{error}</p>
      ) : null}

      {latest ? (
        <div className="relative mt-8 aizix-signals-grid">
          <div className="space-y-5 rounded-2xl border border-white/10 bg-slate-900/45 p-6 backdrop-blur-md">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex flex-wrap items-center gap-3">
                <span
                  className={`rounded-xl border px-4 py-2 font-mono text-lg font-bold tracking-widest ${actionStyle[latest.action] ?? actionStyle.HOLD}`}
                >
                  {latest.action}
                </span>
                <div>
                  <p className="text-aizix-micro font-semibold uppercase tracking-widest text-slate-500">
                    Symbol
                  </p>
                  <p className="font-mono text-lg text-cyan-100/95">{latest.symbol}</p>
                  <p className="text-xs text-slate-500">
                    ETF sleeve:{" "}
                    <span className="font-mono text-violet-300/90">{latest.etf_symbol}</span>
                  </p>
                </div>
              </div>
              <div className="flex min-w-40 flex-1 flex-col gap-1">
                <div className="flex justify-between text-aizix-micro font-semibold uppercase tracking-wider text-slate-500">
                  <span>Confidence</span>
                  <span className="text-cyan-200/90">
                    {latest.confidence_pct.toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-950">
                  <div
                    className="h-full rounded-full bg-linear-to-r from-violet-500 via-blue-500 to-cyan-400 transition-all duration-700 ease-out"
                    style={{ width: `${Math.min(100, latest.confidence_pct)}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <p className="text-aizix-micro font-semibold uppercase tracking-widest text-slate-500">
                  Mood
                </p>
                <p className="text-base text-white">{latest.market_mood}</p>
              </div>
              <div>
                <p className="text-aizix-micro font-semibold uppercase tracking-widest text-slate-500">
                  Risk status
                </p>
                <p className="font-mono text-sm text-slate-200">{latest.risk_status}</p>
              </div>
            </div>

            <div>
              <p className="text-aizix-micro font-semibold uppercase tracking-widest text-slate-500">
                Reason
              </p>
              <p className="mt-1 text-sm/relaxed text-slate-300">{latest.reason}</p>
            </div>

            <div className="rounded-xl border border-white/5 bg-slate-950/50 p-4">
              <p className="text-aizix-micro font-semibold uppercase tracking-widest text-slate-500">
                Whale activity
              </p>
              <p className="mt-2 text-sm italic text-slate-400">
                {latest.whale_activity.narrative}
              </p>
              <p className="mt-2 text-xs text-slate-600">
                Net flow{" "}
                <span className="font-mono text-slate-300">
                  {formatUsd(latest.whale_activity.net_flow_usd)}
                </span>
                <span className="mx-2 text-slate-600">·</span>
                Large moves{" "}
                <span className="font-mono text-slate-300">
                  {latest.whale_activity.large_wallet_moves}
                </span>
              </p>
            </div>

            <p className="text-xs text-slate-600">{latest.etf_bias}</p>
          </div>

          <div className="space-y-4">
            <div className="rounded-2xl border border-cyan-500/20 bg-slate-900/35 p-5 backdrop-blur-md">
              <p className="text-aizix-micro font-semibold uppercase tracking-widest text-slate-500">
                Mock tape
              </p>
              <ul className="mt-3 space-y-2 font-mono text-sm">
                {Object.entries(latest.prices).map(([sym, px]) => (
                  <li
                    key={sym}
                    className="flex justify-between border-b border-white/5 py-1 text-slate-300 last:border-0"
                  >
                    <span className="text-violet-300/90">{sym}</span>
                    <span>{formatUsd(px)}</span>
                  </li>
                ))}
              </ul>
            </div>
            {latest.market ? (
              <div className="rounded-2xl border border-violet-500/20 bg-slate-900/30 p-5 font-mono text-xs text-slate-400">
                <p className="mb-2 text-aizix-micro font-semibold uppercase tracking-widest text-slate-500">
                  Market snapshot
                </p>
                <p>trend: {(latest.market as { trend?: string }).trend}</p>
                <p>
                  vol (ann %):{" "}
                  {(latest.market as { volatility_annualized_pct?: number }).volatility_annualized_pct?.toFixed(1)}
                </p>
                <p>
                  sentiment:{" "}
                  {(latest.market as { sentiment_score?: number }).sentiment_score?.toFixed(3)}
                </p>
              </div>
            ) : null}
          </div>
        </div>
      ) : (
        <p className="relative mt-6 text-sm text-slate-500">Warming up signal bus…</p>
      )}
    </section>
  );
}
