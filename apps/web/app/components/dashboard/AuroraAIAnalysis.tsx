const REASONS = [
  "Strong upward momentum",
  "Whale accumulation",
  "Positive sentiment",
] as const;

export function AuroraAIAnalysis() {
  return (
    <section
      aria-label="AI market analysis"
      className="rounded-2xl border border-violet-500/25 bg-slate-950/55 p-6 shadow-aizix-panel backdrop-blur-2xl"
    >
      <h2 className="text-lg font-bold tracking-tight text-white">AI Market Analysis</h2>
      <div className="mt-5 flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="text-3xl font-black tracking-tight text-white sm:text-4xl">
            Bullish <span className="inline-block">🐂</span>
          </p>
          <p className="mt-2 text-sm text-slate-400">Aurora sentiment fusion · Mock output</p>
        </div>
        <div className="rounded-2xl border border-emerald-500/35 bg-emerald-500/10 px-6 py-4 text-right shadow-aizix-status-emerald">
          <p className="text-aizix-micro font-bold uppercase tracking-widest text-emerald-200/80">
            Confidence
          </p>
          <p className="font-mono text-4xl font-black text-emerald-300">78%</p>
        </div>
      </div>
      <div className="mt-6 border-t border-white/10 pt-5">
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Reasons</p>
        <ul className="mt-3 space-y-2">
          {REASONS.map((r) => (
            <li
              key={r}
              className="flex items-center gap-3 rounded-xl border border-white/5 bg-white/3 px-4 py-2.5 text-sm text-slate-200"
            >
              <span className="size-1.5 shrink-0 rounded-full bg-cyan-400 shadow-aizix-dot-sm-cyan" />
              {r}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
