import { DashboardLive } from "./components/DashboardLive";

export default function Home() {
  return (
    <div className="min-h-screen bg-aizix-bg text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-aizix-radial-violet" />
      <div className="pointer-events-none fixed inset-0 bg-aizix-radial-cyan" />

      <main className="relative mx-auto flex min-h-screen max-w-6xl flex-col gap-12 px-5 py-12 sm:px-8 sm:py-16 lg:gap-16">
        <header className="space-y-3 text-center sm:text-left">
          <p className="text-xs font-semibold uppercase tracking-aizix-wide text-cyan-400/90">
            AIZIX
          </p>
          <h1 className="bg-linear-to-r from-violet-300 via-cyan-200 to-blue-400 bg-clip-text text-3xl font-bold tracking-tight text-transparent sm:text-4xl lg:text-5xl">
            AIZIX AI Trading Dashboard
          </h1>
          <p className="max-w-2xl text-sm text-slate-400 sm:text-base">
            Neural execution, live risk overlays, and institutional-grade telemetry — unified in one command surface.
          </p>
        </header>

        <DashboardLive>
          <section
            aria-label="Chart and whale tracker"
            className="relative overflow-hidden rounded-3xl border border-cyan-500/20 bg-linear-to-br from-slate-950/80 via-aizix-mid/90 to-slate-950/80 p-8 shadow-aizix-chart sm:p-10 lg:p-12"
          >
            <div className="pointer-events-none absolute -right-24 -top-24 size-64 rounded-full bg-violet-600/10 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-20 -left-16 size-56 rounded-full bg-cyan-500/10 blur-3xl" />

            <div className="relative flex min-h-70 flex-col items-center justify-center gap-4 text-center sm:min-h-80">
              <span className="rounded-full border border-cyan-400/25 bg-cyan-400/5 px-3 py-1 text-aizix-micro font-semibold uppercase tracking-aizix-tight text-cyan-300/90">
                Pipeline
              </span>
              <h2 className="text-xl font-semibold tracking-tight text-white sm:text-2xl">
                Chart + Whale Tracker 🐋{" "}
                <span className="text-base font-normal text-slate-500 sm:text-lg">
                  (coming soon)
                </span>
              </h2>
              <p className="max-w-md text-sm/relaxed text-slate-400">
                Live order-flow heatmaps, smart-money clusters, and whale wallet
                trajectories will render here with sub-second refresh.
              </p>
              <div className="mt-4 flex h-28 w-full max-w-xl items-end justify-center gap-1 rounded-xl border border-white/5 bg-slate-900/40 px-4 pb-3 pt-6">
                {[40, 65, 45, 80, 55, 90, 70, 85, 60, 95, 75, 88].map((h, i) => (
                  <div
                    key={i}
                    className="w-full max-w-6 rounded-t-sm bg-linear-to-t from-blue-600/40 via-violet-500/50 to-cyan-400/70 opacity-70"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
            </div>
          </section>
        </DashboardLive>
      </main>
    </div>
  );
}
