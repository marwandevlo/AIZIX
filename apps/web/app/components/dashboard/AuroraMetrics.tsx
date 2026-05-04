const METRICS = [
  {
    label: "Total Balance",
    value: "12,540.25 USDT",
    accent: "from-violet-600/30 to-transparent",
    border: "border-violet-500/30",
    glow: "shadow-aizix-card-violet",
  },
  {
    label: "Daily Profit",
    value: "+1,240.75 USDT",
    accent: "from-emerald-500/30 to-transparent",
    border: "border-emerald-500/35",
    glow: "shadow-aizix-status-emerald",
  },
  {
    label: "Total Profit",
    value: "+24,320.65 USDT",
    accent: "from-blue-500/30 to-transparent",
    border: "border-blue-500/30",
    glow: "shadow-aizix-card-blue",
  },
  {
    label: "Safety Wallet",
    value: "6,250.00 USDT",
    accent: "from-cyan-500/30 to-transparent",
    border: "border-cyan-500/35",
    glow: "shadow-aizix-card-cyan",
  },
  {
    label: "Bot Win Rate",
    value: "78.42%",
    accent: "from-fuchsia-500/25 to-transparent",
    border: "border-fuchsia-500/25",
    glow: "shadow-aizix-card-fuchsia",
  },
] as const;

export function AuroraMetrics() {
  return (
    <section
      aria-label="Key metrics"
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5"
    >
      {METRICS.map((m) => (
        <article
          key={m.label}
          className={`relative overflow-hidden rounded-2xl border ${m.border} bg-slate-950/50 p-5 backdrop-blur-xl ${m.glow}`}
        >
          <div
            className={`pointer-events-none absolute inset-0 bg-linear-to-br ${m.accent} opacity-90`}
          />
          <div className="relative space-y-2">
            <p className="text-aizix-micro font-bold uppercase tracking-widest text-slate-500">
              {m.label}
            </p>
            <p className="font-mono text-xl font-semibold tracking-tight text-white sm:text-2xl">
              {m.value}
            </p>
            <div className="h-px w-full max-w-14 bg-linear-to-r from-cyan-400 via-violet-400 to-blue-500 opacity-80" />
          </div>
        </article>
      ))}
    </section>
  );
}
