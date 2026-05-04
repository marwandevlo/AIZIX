"use client";

export function AuroraCompounding() {
  return (
    <section
      aria-label="Compounding system"
      className="relative overflow-hidden rounded-2xl border border-cyan-500/25 bg-slate-950/55 p-6 shadow-aizix-card-cyan backdrop-blur-2xl"
    >
      <div className="pointer-events-none absolute right-0 top-0 size-40 rounded-full bg-cyan-500/20 blur-3xl" />
      <h2 className="relative text-lg font-bold tracking-tight text-white">
        Compounding System
      </h2>
      <p className="relative mt-1 text-xs text-slate-500">
        Dual-wallet reinvest · Aurora allocation ring
      </p>

      <div className="relative mt-6 flex flex-col items-center gap-6 sm:flex-row sm:justify-center sm:gap-10">
        <div className="relative size-44 sm:size-52">
          <div
            className="absolute inset-0 rounded-full shadow-aurora-donut"
            style={{
              padding: 3,
              background:
                "conic-gradient(from -90deg, rgb(6 182 212) 0deg 252deg, rgb(139 92 246) 252deg 360deg)",
            }}
          >
            <div className="flex size-full items-center justify-center rounded-full bg-slate-950">
              <div className="text-center">
                <p className="font-mono text-2xl font-bold text-white">70</p>
                <p className="text-aizix-micro font-bold uppercase tracking-widest text-cyan-400/90">
                  Trade
                </p>
                <p className="mt-1 font-mono text-lg font-bold text-violet-300">30</p>
                <p className="text-aizix-micro font-bold uppercase tracking-widest text-violet-300/80">
                  Safety
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-xs space-y-4 text-sm text-slate-300">
          <div className="flex items-center gap-2">
            <span className="size-3 rounded-full bg-cyan-400 shadow-aizix-dot-sm-cyan" />
            <span className="font-semibold text-cyan-100">70% Trading Wallet</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="size-3 rounded-full bg-violet-400 shadow-aizix-dot-sm-violet" />
            <span className="font-semibold text-violet-100">30% Safety Wallet</span>
          </div>
          <button
            type="button"
            className="w-full rounded-xl border border-cyan-400/40 bg-linear-to-r from-violet-600/80 to-cyan-600/70 py-3 text-sm font-bold uppercase tracking-wide text-white shadow-aizix-cta transition-all hover:shadow-aurora-cta-hover"
          >
            Smart Compound Now
          </button>
        </div>
      </div>
    </section>
  );
}
