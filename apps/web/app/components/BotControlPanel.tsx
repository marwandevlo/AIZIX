"use client";

import { useState } from "react";
import type { Balances, BotActionResponse, BotStatus } from "@/lib/aizix-api";
import {
  postBotPause,
  postBotStart,
  postBotStop,
  postCompounding,
  formatUsd,
} from "@/lib/aizix-api";

const statusStyles: Record<
  BotStatus,
  { label: string; ring: string; text: string; dot: string }
> = {
  ACTIVE: {
    label: "ACTIVE",
    ring: "border-emerald-400/40 bg-emerald-500/10 shadow-aizix-status-emerald",
    text: "text-emerald-300",
    dot: "bg-emerald-400 shadow-aizix-dot-emerald",
  },
  PAUSED: {
    label: "PAUSED",
    ring: "border-amber-400/45 bg-amber-500/10 shadow-aizix-status-amber",
    text: "text-amber-300",
    dot: "bg-amber-400 shadow-aizix-dot-amber",
  },
  STOPPED: {
    label: "STOPPED",
    ring: "border-red-500/45 bg-red-500/10 shadow-aizix-status-red",
    text: "text-red-400",
    dot: "bg-red-500 shadow-aizix-dot-red",
  },
};

type Props = {
  status: BotStatus;
  compoundingEnabled: boolean;
  balances: Balances | null;
  onRemoteChange: () => Promise<void>;
};

export function BotControlPanel({
  status,
  compoundingEnabled,
  balances,
  onRemoteChange,
}: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const s = statusStyles[status];

  const total = balances?.total ?? 0;
  const trading = balances?.trading_balance ?? 0;
  const safety = balances?.safety_balance ?? 0;
  const tradingPct =
    total > 0 ? Math.min(100, Math.max(0, (trading / total) * 100)) : 70;
  const safetyPct =
    total > 0 ? Math.min(100, Math.max(0, (safety / total) * 100)) : 30;

  async function run(label: string, fn: () => Promise<BotActionResponse>) {
    setBusy(label);
    setErr(null);
    try {
      await fn();
      await onRemoteChange();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Control request failed");
    } finally {
      setBusy(null);
    }
  }

  async function toggleCompounding(next: boolean) {
    setBusy("compound");
    setErr(null);
    try {
      await postCompounding(next);
      await onRemoteChange();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Compounding update failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section
      aria-label="Bot control panel"
      className="relative overflow-hidden rounded-3xl border border-violet-500/20 bg-slate-950/35 p-8 shadow-aizix-panel backdrop-blur-xl sm:p-10"
    >
      <div className="pointer-events-none absolute -right-16 top-0 size-48 rounded-full bg-violet-600/15 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 left-0 size-40 rounded-full bg-cyan-500/10 blur-3xl" />

      <div className="relative flex flex-col gap-10">
        {err ? (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200/90">
            {err}
          </p>
        ) : null}

        <div className="flex flex-col gap-6 border-b border-white/5 pb-8 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-aizix-panel text-violet-300/80">
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
            <span className="text-aizix-micro font-semibold uppercase tracking-widest text-slate-500">
              Current status
            </span>
            <div
              className={`flex items-center gap-3 rounded-2xl border px-5 py-3 ${s.ring}`}
              role="status"
              aria-live="polite"
            >
              <span
                className={`relative flex size-2.5 shrink-0 rounded-full ${s.dot}`}
              >
                {status === "ACTIVE" ? (
                  <span className="absolute inset-0 animate-ping rounded-full bg-emerald-400/50" />
                ) : null}
              </span>
              <span
                className={`font-mono text-sm font-bold tracking-aizix-tight ${s.text}`}
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
              disabled={busy !== null}
              onClick={() => void run("start", postBotStart)}
              className="rounded-2xl border border-emerald-500/35 bg-emerald-500/10 px-5 py-4 text-sm font-semibold text-emerald-200 shadow-aizix-btn-emerald transition-all hover:border-emerald-400/50 hover:bg-emerald-500/15 hover:shadow-aizix-btn-emerald-hover disabled:opacity-50"
            >
              {busy === "start" ? "Starting…" : "Start Trading"}
            </button>
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => void run("pause", postBotPause)}
              className="rounded-2xl border border-amber-400/35 bg-amber-500/10 px-5 py-4 text-sm font-semibold text-amber-200 shadow-aizix-btn-amber transition-all hover:border-amber-400/55 hover:bg-amber-500/15 hover:shadow-aizix-btn-amber-hover disabled:opacity-50"
            >
              {busy === "pause" ? "Pausing…" : "Pause"}
            </button>
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => void run("stop", postBotStop)}
              className="rounded-2xl border border-red-500/40 bg-red-500/10 px-5 py-4 text-sm font-semibold text-red-200 shadow-aizix-btn-red transition-all hover:border-red-400/55 hover:bg-red-500/15 hover:shadow-aizix-btn-red-hover disabled:opacity-50"
            >
              {busy === "stop" ? "Stopping…" : "Emergency Stop"}
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-cyan-500/15 bg-slate-900/40 p-6 backdrop-blur-md">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Compounding</h3>
              <p className="mt-1 text-xs text-slate-500">
                Auto-reinvest profits with dual-wallet routing.
              </p>
            </div>

            <button
              type="button"
              role="switch"
              aria-checked={compoundingEnabled}
              aria-label="Compounding"
              disabled={busy !== null}
              onClick={() => void toggleCompounding(!compoundingEnabled)}
              className={`relative h-12 w-22 shrink-0 rounded-full border transition disabled:opacity-50 ${
                compoundingEnabled
                  ? "border-cyan-400/40 bg-linear-to-r from-violet-600/25 to-cyan-600/25 shadow-aizix-toggle"
                  : "border-white/10 bg-slate-950/70"
              }`}
            >
              <span
                className={`absolute top-1 size-10 rounded-full shadow-lg transition-all duration-300 ease-out ${
                  compoundingEnabled
                    ? "right-1 bg-cyan-400 shadow-aizix-toggle-knob"
                    : "left-1 bg-slate-600"
                }`}
              />
              <span className="pointer-events-none relative z-10 flex h-full items-center justify-between px-2.5 text-aizix-micro font-bold uppercase tracking-wider">
                <span className={!compoundingEnabled ? "text-slate-200" : "text-slate-500"}>
                  Off
                </span>
                <span className={compoundingEnabled ? "text-cyan-100" : "text-slate-500"}>
                  On
                </span>
              </span>
            </button>
          </div>

          <div
            className={`mt-6 space-y-4 transition-opacity duration-300 ${
              compoundingEnabled ? "opacity-100" : "opacity-40"
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-medium uppercase tracking-wider text-slate-500">
              <span>Allocation split</span>
              {balances ? (
                <span className="font-mono normal-case text-slate-400">
                  {formatUsd(trading)} · {formatUsd(safety)} · {formatUsd(total)}
                </span>
              ) : null}
              {!compoundingEnabled ? (
                <span className="normal-case text-slate-500">Paused routing</span>
              ) : null}
            </div>
            <div className="flex h-3 overflow-hidden rounded-full border border-white/10 bg-slate-950/80">
              <div
                className="flex items-center justify-center bg-linear-to-r from-violet-500 to-blue-500 shadow-aizix-bar-violet transition-all duration-500"
                style={{ width: `${tradingPct}%` }}
                title="Trading wallet"
              />
              <div
                className="flex items-center justify-center bg-linear-to-r from-cyan-500 to-teal-400 shadow-aizix-bar-cyan transition-all duration-500"
                style={{ width: `${safetyPct}%` }}
                title="Safety wallet"
              />
            </div>
            <div className="flex flex-col gap-3 text-sm sm:flex-row sm:justify-between">
              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-violet-400 shadow-aizix-dot-sm-violet" />
                <span className="text-slate-300">
                  <span className="font-mono font-semibold text-violet-200">
                    {tradingPct.toFixed(1)}%
                  </span>{" "}
                  Trading Wallet
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-cyan-400 shadow-aizix-dot-sm-cyan" />
                <span className="text-slate-300">
                  <span className="font-mono font-semibold text-cyan-200">
                    {safetyPct.toFixed(1)}%
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
