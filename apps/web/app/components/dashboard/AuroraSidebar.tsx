"use client";

const NAV = [
  "Dashboard",
  "Trading",
  "AI Brain",
  "ETF Explorer",
  "Portfolio",
  "Risk Control",
  "Compounding",
  "Backtesting",
  "Analytics",
  "Settings",
] as const;

type Props = {
  open: boolean;
  onClose: () => void;
};

export function AuroraSidebar({ open, onClose }: Props) {
  return (
    <>
      <button
        type="button"
        aria-label="Close menu"
        onClick={onClose}
        className={`fixed inset-0 z-30 bg-black/70 backdrop-blur-md transition-opacity lg:hidden ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      />
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-70 flex-col border-r border-violet-500/20 bg-aurora-sidebar shadow-aurora-sidebar backdrop-blur-2xl transition-transform duration-300 ease-out lg:static lg:z-0 lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="border-b border-white/10 px-5 py-6">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-xl border border-cyan-400/40 bg-linear-to-br from-violet-600/50 to-cyan-500/30 shadow-aizix-cta">
                <span className="text-lg font-black tracking-tighter text-white">A</span>
              </div>
              <div>
                <p className="bg-linear-to-r from-violet-200 via-cyan-200 to-blue-300 bg-clip-text text-xl font-bold tracking-tight text-transparent">
                  AIZIX
                </p>
                <p className="text-aizix-micro font-semibold uppercase tracking-aizix-tight text-cyan-400/80">
                  Aurora Core
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white lg:hidden"
              aria-label="Close sidebar"
            >
              ✕
            </button>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3">
          {NAV.map((item, i) => (
            <button
              key={item}
              type="button"
              onClick={onClose}
              className={`rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-all ${
                i === 0
                  ? "border border-cyan-500/25 bg-linear-to-r from-violet-600/25 via-blue-600/15 to-cyan-600/20 text-white shadow-aizix-signals"
                  : "text-slate-400 hover:border hover:border-white/10 hover:bg-white/5 hover:text-slate-100"
              }`}
            >
              {item}
            </button>
          ))}
        </nav>

        <div className="border-t border-white/10 p-4">
          <p className="text-aizix-micro font-bold uppercase tracking-widest text-violet-400/90">
            Neural link
          </p>
          <p className="mt-1 text-xs leading-relaxed text-slate-500">
            Paper venue · Zero live keys
          </p>
        </div>
      </aside>
    </>
  );
}
