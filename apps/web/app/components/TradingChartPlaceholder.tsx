export function TradingChartPlaceholder() {
  const candles = [42, 58, 52, 68, 61, 72, 65, 78, 70, 85, 79, 88, 82, 90];
  return (
    <section
      aria-label="Chart preview"
      className="relative flex min-h-88 flex-col overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-950/80 shadow-aizix-chart sm:min-h-104 lg:min-h-112"
    >
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.06)_1px,transparent_1px)] bg-size-[24px_24px]" />

      <header className="relative z-10 flex flex-wrap items-center justify-between gap-3 border-b border-white/5 bg-slate-900/60 px-3 py-2.5 backdrop-blur-sm sm:px-4">
        <div className="flex items-center gap-2">
          <span className="rounded border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-cyan-300/95 sm:text-xs">
            AIZIX / USD
          </span>
          <span className="font-mono text-sm font-semibold text-white sm:text-base">
            12,847.32
          </span>
          <span className="rounded px-1.5 py-0.5 text-xs font-medium text-emerald-400/90">
            +1.24%
          </span>
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-white/5 bg-slate-950/80 p-0.5">
          {["1H", "4H", "1D", "1W"].map((tf) => (
            <button
              key={tf}
              type="button"
              className={`rounded-md px-2 py-1 text-[10px] font-medium uppercase tracking-wide sm:text-xs ${
                tf === "1D"
                  ? "bg-violet-600/40 text-white"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
        <div className="hidden items-center gap-2 sm:flex">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">
            Indicators
          </span>
          <span className="rounded border border-white/10 bg-slate-900/80 px-2 py-1 font-mono text-[10px] text-slate-400">
            MA · RSI
          </span>
        </div>
      </header>

      <div className="relative z-10 flex flex-1 flex-col px-2 pb-3 pt-4 sm:px-4">
        <div className="mb-2 flex justify-between border-b border-white/5 pb-2 font-mono text-[10px] text-slate-500 sm:text-xs">
          <span>O 12,802</span>
          <span>H 12,910</span>
          <span>L 12,765</span>
          <span>C 12,847</span>
        </div>
        <div className="flex flex-1 items-end justify-between gap-0.5 sm:gap-1">
          {candles.map((h, i) => {
            const up = i % 3 !== 0;
            return (
              <div
                key={i}
                className="flex min-w-0 flex-1 flex-col items-center justify-end gap-1"
              >
                <div
                  className={`w-full max-w-[10px] rounded-t-sm sm:max-w-3 ${
                    up
                      ? "bg-linear-to-t from-emerald-600/70 to-emerald-400/90"
                      : "bg-linear-to-t from-rose-600/70 to-rose-400/90"
                  }`}
                  style={{ height: `${h}%` }}
                />
                <div
                  className={`h-3 w-full max-w-[10px] rounded-b-sm opacity-50 sm:max-w-3 ${
                    up ? "bg-emerald-500/35" : "bg-rose-500/35"
                  }`}
                />
              </div>
            );
          })}
        </div>
        <p className="mt-3 text-center text-[10px] text-slate-600 sm:text-xs">
          Live chart feed connects here — TradingView-style embed placeholder
        </p>
      </div>
    </section>
  );
}
