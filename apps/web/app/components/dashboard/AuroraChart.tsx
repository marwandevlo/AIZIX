"use client";

const TIMEFRAMES = ["1m", "5m", "15m", "1H", "4H", "1D"] as const;
const CANDLES = [35, 52, 44, 58, 50, 68, 62, 74, 70, 82, 76, 88, 84, 92, 88, 95];

export function AuroraChart() {
  return (
    <section
      aria-label="Price chart"
      className="relative flex min-h-88 flex-col overflow-hidden rounded-2xl border border-violet-500/25 bg-slate-950/55 shadow-aurora-chart backdrop-blur-2xl sm:min-h-104 lg:min-h-112"
    >
      <div className="pointer-events-none absolute inset-0 bg-linear-to-b from-violet-950/50 via-transparent to-cyan-950/25" />
      <div className="aurora-chart-grid-bg bg-size-[28px_28px]" />

      <div className="relative z-10 flex flex-wrap items-start justify-between gap-4 border-b border-white/10 px-4 py-4 sm:px-6">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-lg border border-cyan-400/40 bg-cyan-500/10 px-3 py-1 font-mono text-sm font-bold text-cyan-100 shadow-aizix-card-cyan">
              BTC3L/USDT
            </span>
            <div className="font-mono">
              <span className="text-2xl font-bold text-white sm:text-3xl">22.45</span>
              <span className="ml-3 text-base font-semibold text-emerald-400 sm:text-lg">
                +4.25%
              </span>
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-500">Leveraged sleeve · Paper index</p>
        </div>
        <div className="flex flex-wrap gap-1 rounded-xl border border-white/10 bg-slate-950/80 p-1">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              type="button"
              className={`rounded-lg px-2.5 py-1.5 font-mono text-xs font-semibold transition-colors ${
                tf === "1H"
                  ? "bg-linear-to-r from-violet-600/60 to-cyan-600/50 text-white shadow-aurora-timeframe"
                  : "text-slate-500 hover:bg-white/5 hover:text-slate-300"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      <div className="relative z-10 flex flex-1 flex-col px-3 pb-4 pt-2 sm:px-5">
        <div className="mb-2 flex justify-between border-b border-white/5 pb-2 font-mono text-aizix-micro text-slate-500 sm:text-xs">
          <span>O 21.52</span>
          <span>H 22.88</span>
          <span>L 21.40</span>
          <span>C 22.45</span>
        </div>
        <div className="flex flex-1 items-end justify-between gap-px px-0.5 sm:gap-0.5">
          {CANDLES.map((h, i) => {
            const up = i % 4 !== 2;
            return (
              <div
                key={i}
                className="flex min-w-0 flex-1 flex-col items-center justify-end gap-0.5"
              >
                <div
                  className={`w-full max-w-2 rounded-t-xs sm:max-w-3 ${
                    up
                      ? "bg-linear-to-t from-emerald-600/90 to-emerald-300/95 shadow-aurora-candle-up"
                      : "bg-linear-to-t from-rose-600/90 to-rose-300/95 shadow-aurora-candle-down"
                  }`}
                  style={{ height: `${h}%` }}
                />
                <div
                  className={`h-2 w-full max-w-2 rounded-b-xs opacity-50 sm:max-w-3 ${
                    up ? "bg-emerald-500/45" : "bg-rose-500/45"
                  }`}
                />
              </div>
            );
          })}
        </div>
        <p className="mt-3 text-center text-aizix-micro text-slate-600 sm:text-xs">
          Synthetic candlestream · Aurora visualization layer
        </p>
      </div>
    </section>
  );
}
