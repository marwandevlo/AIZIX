export function AuroraWhale() {
  return (
    <section
      aria-label="Whale activity"
      className="rounded-2xl border border-cyan-500/25 bg-slate-950/55 p-6 shadow-aizix-card-cyan backdrop-blur-2xl"
    >
      <h2 className="text-lg font-bold tracking-tight text-white">Whale Activity</h2>
      <div className="mt-5 rounded-2xl border border-cyan-500/20 bg-linear-to-br from-slate-900/90 via-violet-950/40 to-cyan-950/30 p-5">
        <p className="text-lg font-bold text-white">
          Whale detected <span className="not-italic">🐋</span>
        </p>
        <p className="mt-2 text-slate-300">Large BTC buy order</p>
        <p className="mt-4 font-mono text-2xl font-bold text-cyan-200">1,250 BTC3L</p>
        <button
          type="button"
          className="mt-5 w-full rounded-xl border border-violet-500/40 bg-violet-600/20 py-2.5 text-sm font-bold uppercase tracking-wide text-violet-100 transition-colors hover:bg-violet-600/30"
        >
          View Whale Tracker
        </button>
      </div>
    </section>
  );
}
