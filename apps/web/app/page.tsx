import { BotControlPanel } from "./components/BotControlPanel";

export default function Home() {
  const cards = [
    {
      label: "Total Balance",
      value: "$12,540",
      accent: "from-violet-500/20 to-transparent",
      border: "border-violet-500/30",
      glow: "shadow-[0_0_32px_rgba(139,92,246,0.12)]",
    },
    {
      label: "Daily Profit",
      value: "+$240",
      accent: "from-cyan-400/20 to-transparent",
      border: "border-cyan-400/35",
      glow: "shadow-[0_0_32px_rgba(34,211,238,0.15)]",
    },
    {
      label: "Win Rate",
      value: "78%",
      accent: "from-blue-500/20 to-transparent",
      border: "border-blue-500/30",
      glow: "shadow-[0_0_32px_rgba(59,130,246,0.12)]",
    },
    {
      label: "AI Market Mood",
      value: "Bullish 🐂",
      accent: "from-fuchsia-500/20 to-transparent",
      border: "border-fuchsia-500/25",
      glow: "shadow-[0_0_32px_rgba(217,70,239,0.1)]",
    },
  ] as const;

  return (
    <div className="min-h-screen bg-[#060816] text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(120,119,198,0.25),transparent)]" />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_60%_40%_at_100%_0%,rgba(6,182,212,0.08),transparent)]" />

      <main className="relative mx-auto flex min-h-screen max-w-6xl flex-col gap-12 px-5 py-12 sm:px-8 sm:py-16 lg:gap-16">
        <header className="space-y-3 text-center sm:text-left">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-400/90">
            AIZIX
          </p>
          <h1 className="bg-gradient-to-r from-violet-300 via-cyan-200 to-blue-400 bg-clip-text text-3xl font-bold tracking-tight text-transparent sm:text-4xl lg:text-5xl">
            AIZIX AI Trading Dashboard
          </h1>
          <p className="max-w-2xl text-sm text-slate-400 sm:text-base">
            Neural execution, live risk overlays, and institutional-grade telemetry — unified in one command surface.
          </p>
        </header>

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
                className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${card.accent} opacity-80`}
              />
              <div className="relative flex flex-col gap-3">
                <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  {card.label}
                </span>
                <span className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                  {card.value}
                </span>
                <span className="h-px w-12 bg-gradient-to-r from-cyan-400 to-violet-500 opacity-60" />
              </div>
            </article>
          ))}
        </section>

        <section
          aria-label="Chart and whale tracker"
          className="relative overflow-hidden rounded-3xl border border-cyan-500/20 bg-gradient-to-br from-slate-950/80 via-[#0a1028]/90 to-slate-950/80 p-8 shadow-[0_0_60px_rgba(59,130,246,0.08)] sm:p-10 lg:p-12"
        >
          <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-violet-600/10 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-20 -left-16 h-56 w-56 rounded-full bg-cyan-500/10 blur-3xl" />

          <div className="relative flex min-h-[280px] flex-col items-center justify-center gap-4 text-center sm:min-h-[320px]">
            <span className="rounded-full border border-cyan-400/25 bg-cyan-400/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-cyan-300/90">
              Pipeline
            </span>
            <h2 className="text-xl font-semibold tracking-tight text-white sm:text-2xl">
              Chart + Whale Tracker 🐋{" "}
              <span className="text-base font-normal text-slate-500 sm:text-lg">
                (coming soon)
              </span>
            </h2>
            <p className="max-w-md text-sm leading-relaxed text-slate-400">
              Live order-flow heatmaps, smart-money clusters, and whale wallet
              trajectories will render here with sub-second refresh.
            </p>
            <div className="mt-4 flex h-28 w-full max-w-xl items-end justify-center gap-1 rounded-xl border border-white/5 bg-slate-900/40 px-4 pb-3 pt-6">
              {[40, 65, 45, 80, 55, 90, 70, 85, 60, 95, 75, 88].map((h, i) => (
                <div
                  key={i}
                  className="w-full max-w-[24px] rounded-t-sm bg-gradient-to-t from-blue-600/40 via-violet-500/50 to-cyan-400/70 opacity-70"
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
          </div>
        </section>

        <BotControlPanel />

        <div className="flex justify-center pb-8 sm:justify-start">
          <button
            type="button"
            className="group relative w-full overflow-hidden rounded-2xl border border-cyan-400/30 bg-gradient-to-r from-violet-600 via-blue-600 to-cyan-500 px-10 py-5 text-lg font-semibold tracking-wide text-white shadow-[0_0_40px_rgba(34,211,238,0.25)] transition-all duration-300 hover:shadow-[0_0_56px_rgba(139,92,246,0.35)] sm:w-auto sm:min-w-[280px]"
          >
            <span className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
            <span className="relative">Start Trading</span>
          </button>
        </div>
      </main>
    </div>
  );
}
