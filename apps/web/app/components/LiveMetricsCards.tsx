"use client";

import type { BotStatusPayload } from "@/lib/aizix-api";
import { formatUsd } from "@/lib/aizix-api";

type Props = {
  status: BotStatusPayload | null;
  mood: string;
  error: string | null;
};

export function LiveMetricsCards({ status, mood, error }: Props) {
  const total = status?.balances.total ?? 12_540;
  const daily = status?.daily_pnl_usd ?? 240;
  const win = status?.win_rate_pct ?? 78;

  const cards = [
    {
      label: "Total Balance",
      value: formatUsd(total),
      accent: "from-violet-500/20 to-transparent",
      border: "border-violet-500/30",
      glow: "shadow-aizix-card-violet",
    },
    {
      label: "Daily Profit",
      value: `${daily >= 0 ? "+" : ""}${formatUsd(daily)}`,
      accent: "from-cyan-400/20 to-transparent",
      border: "border-cyan-400/35",
      glow: "shadow-aizix-card-cyan",
    },
    {
      label: "Win Rate",
      value: `${win.toFixed(1)}%`,
      accent: "from-blue-500/20 to-transparent",
      border: "border-blue-500/30",
      glow: "shadow-aizix-card-blue",
    },
    {
      label: "AI Market Mood",
      value: mood,
      accent: "from-fuchsia-500/20 to-transparent",
      border: "border-fuchsia-500/25",
      glow: "shadow-aizix-card-fuchsia",
    },
  ] as const;

  return (
    <div className="space-y-3">
      {error ? (
        <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-amber-200/90">
          Live metrics paused: {error}. Start API:{" "}
          <code className="text-cyan-200/90">
            cd apps/api &amp;&amp; uvicorn app.main:app --reload
          </code>
        </p>
      ) : null}
      <section
        aria-label="Key metrics"
        className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6"
      >
        {cards.map((card) => (
          <article
            key={card.label}
            className={`group relative overflow-hidden rounded-2xl border ${card.border} bg-slate-950/40 p-6 backdrop-blur-md ${card.glow} transition-transform duration-300 hover:-translate-y-0.5`}
          >
            <div
              className={`pointer-events-none absolute inset-0 bg-linear-to-br ${card.accent} opacity-80`}
            />
            <div className="relative flex flex-col gap-3">
              <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                {card.label}
              </span>
              <span className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                {card.value}
              </span>
              <span className="h-px w-12 bg-linear-to-r from-cyan-400 to-violet-500 opacity-60" />
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
