const SIGNALS = [
  { pair: "BTC3L/USDT", label: "Strong Buy", pct: "78%", accent: "from-emerald-500/25 to-cyan-500/10" },
  { pair: "ETH3L/USDT", label: "Buy", pct: "72%", accent: "from-cyan-500/25 to-blue-500/10" },
  { pair: "SOL3L/USDT", label: "Buy", pct: "65%", accent: "from-blue-500/25 to-violet-500/10" },
  { pair: "DOGE5L/USDT", label: "Moderate Buy", pct: "58%", accent: "from-violet-500/25 to-fuchsia-500/10" },
] as const;

export function AuroraSignalCards() {
  return (
    <section aria-label="AI signal cards">
      <h2 className="mb-4 text-lg font-bold tracking-tight text-white">AI Signals</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {SIGNALS.map((s) => (
          <article
            key={s.pair}
            className="relative overflow-hidden rounded-2xl border border-violet-500/20 bg-slate-950/50 p-5 shadow-aizix-signals backdrop-blur-xl"
          >
            <div
              className={`pointer-events-none absolute inset-0 bg-linear-to-br ${s.accent} opacity-80`}
            />
            <div className="relative flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-mono text-sm font-bold text-cyan-100 sm:text-base">{s.pair}</p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-violet-300/90">
                  {s.label}
                </p>
              </div>
              <span className="shrink-0 rounded-lg border border-white/15 bg-slate-950/80 px-2.5 py-1 font-mono text-lg font-black text-white">
                {s.pct}
              </span>
            </div>
            <div className="relative mt-4 h-1 overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-linear-to-r from-violet-500 via-cyan-400 to-emerald-400 shadow-aizix-bar-cyan"
                style={{ width: s.pct }}
              />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
